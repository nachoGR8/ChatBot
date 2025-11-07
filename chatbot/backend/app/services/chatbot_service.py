"""Core chatbot service responsible for constructing prompts and generating replies."""
from __future__ import annotations

import concurrent.futures
import difflib
import logging
import os
import re
import threading
import time
import traceback
import unicodedata
from datetime import datetime
from typing import List, Optional

from gpt4all import GPT4All

from ..models import Business, Conversation, FAQ

logger = logging.getLogger("chatbot")


class ChatbotService:
    def __init__(self) -> None:
        self.model = None
        default_model = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "models",
                "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            )
        )
        env_model = os.getenv("CHATBOT_MODEL_NAME")
        if env_model:
            if os.path.isabs(env_model) or os.path.exists(env_model):
                self.model_name = env_model
            else:
                candidate = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "models", env_model)
                )
                self.model_name = candidate if os.path.exists(candidate) else env_model
        else:
            if os.path.exists(default_model):
                self.model_name = default_model
            else:
                self.model_name = "orca-mini-3b-gguf2-q4_0.gguf"
        self.model_failed = False
        self.generate_timeout = 30.0
        try:
            self.temp = float(os.getenv("CHATBOT_TEMP", "0.7"))
        except Exception:
            self.temp = 0.7
        self._init_lock = threading.Lock()
        self._initializing = False
        self._device = None
        self._backend = None
        self._loaded_at = None
        self._failed_at = None
        self.backend_type = None
        self.max_faqs = int(os.getenv("CHATBOT_MAX_FAQS", "4"))
        self.faq_answer_max_chars = int(os.getenv("CHATBOT_FAQ_ANSWER_MAX_CHARS", "250"))
        self.faq_question_max_chars = int(os.getenv("CHATBOT_FAQ_QUESTION_MAX_CHARS", "200"))
        self.context_token_ratio = int(os.getenv("CHATBOT_CONTEXT_TOKEN_RATIO", "4"))
        self.context_window = int(os.getenv("GPT4ALL_CONTEXT_WINDOW", "2048"))
        self.reserve_response_tokens = int(os.getenv("CHATBOT_RESERVE_RESPONSE_TOKENS", "200"))
        self.max_history_turns = int(os.getenv("CHATBOT_MAX_HISTORY_TURNS", "4"))
        self.history_message_max_chars = int(os.getenv("CHATBOT_HISTORY_MESSAGE_MAX_CHARS", "220"))
        self._name_patterns = [
            re.compile(r"\b(?:me\s+llamo|mi\s+nombre\s+es|soy)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)", re.IGNORECASE),
            re.compile(r"\b(?:llámame|puedes\s+llamarme)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)", re.IGNORECASE),
        ]
        self._recommendation_pattern = re.compile(
            r"(recomiend\w*|recomendaci\w*|suger\w*|sugier\w*|aconsej\w*|qué\s+me\s+recomiendas)",
            re.IGNORECASE,
        )
        self._menu_pattern = re.compile(
            r"\b(menu|menú|carta|platos|especialidades|men\s?ú\s?principal)\b",
            re.IGNORECASE,
        )

    def _prepare_context_for_prompt(
        self,
        context: str,
        message: str = "",
        max_tokens: Optional[int] = None,
    ) -> str:
        if max_tokens is None:
            allowed_prompt_tokens = max(1, self.context_window - self.reserve_response_tokens)
            msg_tokens = 0
            if message:
                msg_tokens = max(1, len(message) // self.context_token_ratio)
            max_tokens = max(1, allowed_prompt_tokens - msg_tokens)

        allowed_chars = max_tokens * max(1, self.context_token_ratio)
        if len(context) <= allowed_chars:
            return context

        tail_chars = max(400, allowed_chars // 3)
        tail_chars = min(tail_chars, allowed_chars - 200)
        tail = context[-tail_chars:]
        head = context[: allowed_chars - len(tail)]
        trimmed = f"{head.rstrip()}\n\n[...]\n\n{tail.lstrip()}"
        return trimmed[:allowed_chars]

    def format_history(self, history_items: List[Conversation]) -> str:
        if not history_items:
            return ""

        lines: List[str] = []
        for item in history_items[-self.max_history_turns :]:
            user_msg = (item.user_message or "").strip()
            bot_msg = (item.bot_response or "").strip()
            if not user_msg:
                continue
            if len(user_msg) > self.history_message_max_chars:
                user_msg = user_msg[: self.history_message_max_chars].rstrip() + "…"
            if bot_msg and len(bot_msg) > self.history_message_max_chars:
                bot_msg = bot_msg[: self.history_message_max_chars].rstrip() + "…"
            lines.append(f"Cliente: {user_msg}")
            if bot_msg:
                lines.append(f"Asistente: {bot_msg}")

        return "\n".join(lines)

    @staticmethod
    def _normalize_candidate_name(raw: str) -> Optional[str]:
        if not raw:
            return None
        clean = raw.strip(" ,.!?¿¡\n\t")
        if not clean or len(clean) < 2 or len(clean) > 40:
            return None
        token = clean.split()[0]
        if not token.isalpha():
            return None
        return token[:1].upper() + token[1:].lower()

    def extract_customer_name(
        self,
        history_items: List[Conversation],
        current_user_message: Optional[str] = None,
    ) -> Optional[str]:
        candidate_texts: List[str] = []
        for item in history_items:
            if item and getattr(item, "user_message", None):
                candidate_texts.append(item.user_message)
        if current_user_message:
            candidate_texts.append(current_user_message)

        for text in reversed(candidate_texts):
            if not text:
                continue
            for pattern in self._name_patterns:
                match = pattern.search(text)
                if match:
                    name_candidate = match.group(1)
                    normalized = self._normalize_candidate_name(name_candidate)
                    if normalized:
                        return normalized
        return None

    def is_recommendation_request(self, message: Optional[str]) -> bool:
        if not message:
            return False
        normalized = unicodedata.normalize("NFD", message)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return bool(self._recommendation_pattern.search(normalized))

    def is_critical_info_request(self, message: str) -> Optional[dict]:
        """
        Detecta si el usuario está pidiendo información crítica estructurada 
        (menú, clases, productos, servicios, habitaciones, etc.) de forma UNIVERSAL.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Dict con 'type', 'keywords' y 'emoji' si se detecta solicitud crítica, None si no.
            
        Ejemplos:
            "¿Qué tienen en el menú?" → {'type': 'menú', 'keywords': [...], 'emoji': '🍽️'}
            "¿Qué clases hay?" → {'type': 'clases', 'keywords': [...], 'emoji': '💪'}
            "Productos disponibles" → {'type': 'productos', 'keywords': [...], 'emoji': '🛍️'}
        """
        import re
        
        message_lower = message.lower()
        
        # Diccionario de tipos críticos con palabras clave y emojis
        # ORDEN IMPORTANTE: Los más específicos primero para evitar conflictos
        critical_types = {
            'clases': {
                'patterns': [
                    r'\bclases?\b',
                    r'\bhorarios?\b',
                    r'\bactividades?\b',
                    r'\bentrenamientos?\b',
                    r'\bsesiones?\b',
                    r'qué (clases|actividades) (hay|tienen|ofrecen)',
                ],
                'keywords': ['clases', 'clase', 'horarios', 'actividades', 'entrenamiento'],
                'emoji': '💪'
            },
            'productos': {
                'patterns': [
                    r'\bproductos?\b',
                    r'\bcatálogos?\b',
                    r'\bartículos?\b',
                    r'\barticulos?\b',
                    r'\binventario\b',
                    r'\bmercancías?\b',
                    r'qué (productos|artículos) (hay|tienen|venden)',
                    r'lista de (productos|artículos)',
                    r'catálogo (completo|de productos)',
                    r'tienen.*inventario',
                    r'artículos\s+disponibles',
                ],
                'keywords': ['productos', 'producto', 'catálogo', 'artículos', 'inventario'],
                'emoji': '🛍️'
            },
            'servicios': {
                'patterns': [
                    r'\bservicios?\b',
                    r'\btratamientos?\b',
                    r'\bpaquetes?\b',
                    r'\bofertas?\b',
                    r'qué (servicios|tratamientos) (hay|tienen|ofrecen)',
                ],
                'keywords': ['servicios', 'servicio', 'tratamientos', 'paquetes', 'ofertas'],
                'emoji': '📋'
            },
            'habitaciones': {
                'patterns': [
                    r'\bhabitaciones?\b',
                    r'\bcuartos?\b',
                    r'\bsuites?\b',
                    r'\balojamientos?\b',
                    r'tipos de (habitaciones|cuartos|alojamiento)',
                ],
                'keywords': ['habitaciones', 'habitación', 'cuartos', 'suites', 'alojamiento'],
                'emoji': '🏨'
            },
            'tarifas': {
                'patterns': [
                    r'\btarifas?\b',
                    r'\bprecios?\b',
                    r'\bcostos?\b',
                    r'\bcuánto (cuesta|vale)',
                    r'lista de precios',
                ],
                'keywords': ['tarifas', 'tarifa', 'precios', 'precio', 'costo'],
                'emoji': '💰'
            },
            'planes': {
                'patterns': [
                    r'\bplanes?\b',
                    r'\bmembresías?\b',
                    r'\bsuscripciones?\b',
                    r'qué (planes|membresías) (hay|tienen)',
                ],
                'keywords': ['planes', 'plan', 'membresías', 'suscripciones'],
                'emoji': '📝'
            },
            # MENÚ AL FINAL para evitar conflictos con patrones más específicos
            'menú': {
                'patterns': [
                    r'\bmen[úu]\b',
                    r'\bcarta\b',
                    r'\bplatos?\b',
                    r'\bcomidas?\b',
                    r'\bbebidas?\b',
                    r'\bpostres?\b',
                    r'\bespecialidades?\b',
                    r'menú (del día|completo|diario)',
                    r'qué (hay|tienen|comen|sirven) (para|de) (comer|cenar|almorzar)',
                ],
                'keywords': ['menú', 'menu', 'platos', 'carta', 'especialidades', 'comida'],
                'emoji': '🍽️'
            },
        }
        
        # Detectar qué tipo de información crítica se está pidiendo
        for critical_type, config in critical_types.items():
            for pattern in config['patterns']:
                if re.search(pattern, message_lower):
                    logger.info(f"🎯 Detectado tipo crítico: {critical_type} (patrón: {pattern})")
                    return {
                        'type': critical_type,
                        'keywords': config['keywords'],
                        'emoji': config['emoji']
                    }
        
        # No se detectó ninguna solicitud crítica
        return None
    
    def is_menu_request(self, message: str) -> bool:
        """
        DEPRECATED: Usar is_critical_info_request() en su lugar.
        Detecta si el usuario está pidiendo el menú del restaurante.
        """
        result = self.is_critical_info_request(message)
        return result is not None and result['type'] == 'menú'

    def extract_menu_from_documents(self, db, business_id: int) -> Optional[str]:
        """
        Extrae el menú estructurado directamente de los documentos procesados.
        Busca patrones específicos de platos con precios y descripciones.
        
        Returns:
            String formateado con los platos encontrados o None si no hay documentos.
        """
        try:
            from ..models import DocumentChunk
            from sqlalchemy import and_
            
            logger.info(f"→ Buscando chunks para business_id={business_id}")
            
            # Buscar chunks que contengan información de menú
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.business_id == business_id
            ).order_by(DocumentChunk.chunk_index).all()
            
            logger.info(f"→ Encontrados {len(chunks)} chunks")
            
            if not chunks:
                logger.warning("→ No hay chunks disponibles")
                return None
            
            # Concatenar el texto de los chunks relevantes
            full_text = "\n".join([chunk.text for chunk in chunks])
            logger.info(f"→ Texto total: {len(full_text)} caracteres")
            
            # Buscar la sección del menú principal
            import re
            
            # Encontrar la tabla del menú (después de "Menú principal")
            menu_section_match = re.search(
                r'Menú principal\s+(.*?)(?=\n\n[A-Z]|\Z)',
                full_text,
                re.DOTALL | re.IGNORECASE
            )
            
            if not menu_section_match:
                logger.warning("→ No se encontró sección 'Menú principal'")
                return None
            
            menu_text = menu_section_match.group(1)
            logger.info(f"→ Sección de menú encontrada: {len(menu_text)} caracteres")
            logger.info(f"→ Primeras 200 chars: {menu_text[:200]}")
            
            # Patrón para líneas de menú con formato tabular:
            # Categoría   Plato   Descripción   Precio
            # Usar split por múltiples espacios para detectar columnas
            lines = menu_text.strip().split('\n')
            logger.info(f"→ Líneas en menú: {len(lines)}")
            
            dishes = []
            seen_names = set()
            
            # Saltar la línea de encabezados (Categoría, Plato, Descripción, Precio)
            header_found = False
            
            for i, line in enumerate(lines):
                # Limpiar la línea
                line = line.strip()
                if not line:
                    continue
                
                # Detectar encabezado
                if 'Categoría' in line and 'Plato' in line:
                    header_found = True
                    logger.info(f"→ Encabezado encontrado en línea {i}")
                    continue
                
                if not header_found:
                    continue
                
                # Intentar parsear la línea dividiendo por múltiples espacios
                # Formato: Categoría    Nombre del Plato    Descripción    Precio
                parts = re.split(r'\s{2,}', line)
                logger.info(f"→ Línea {i}: {len(parts)} partes - {parts[:3]}")
                
                if len(parts) >= 4:
                    category = parts[0].strip()
                    name = parts[1].strip()
                    description = parts[2].strip()
                    price = parts[3].strip()
                    
                    # Validar que no sea encabezado repetido y tenga precio numérico
                    if (name and name not in seen_names and
                        name.lower() not in ['plato', 'categoría', 'descripción'] and
                        re.search(r'\d+[.,]\d+', price)):
                        
                        seen_names.add(name)
                        dishes.append({
                            'category': category,
                            'name': name,
                            'description': description,
                            'price': price.replace('■', '-')  # Fix encoding issues
                        })
                        logger.info(f"→ Plato añadido: {name}")
            
            logger.info(f"→ Total platos extraídos: {len(dishes)}")
            
            if dishes:
                # Formatear como lista limpia
                formatted = "**MENÚ DISPONIBLE (platos reales del restaurante):**\n\n"
                for dish in dishes:
                    formatted += f"• **{dish['name']}** - {dish['description']} - {dish['price']}€\n"
                formatted += "\n**IMPORTANTE: Estos son TODOS los platos disponibles. No existen otros platos.**"
                return formatted
            
            logger.warning("→ No se extrajeron platos")
            return None
            
        except Exception as e:
            logger.error(f"→ Error extrayendo menú de documentos: {e}")
            import traceback
            traceback.print_exc()
            return None


    def initialize_model(self) -> None:
        if self.model is not None:
            return

        if self._initializing:
            waited = 0.0
            while self._initializing and waited < 60.0:
                time.sleep(0.1)
                waited += 0.1
            return

        with self._init_lock:
            if self.model is not None:
                return
            self._initializing = True
            try:
                logger.info("Cargando modelo (backend automático)...")
                logger.info("Cargando modelo (intentando backend preferente)...")
                env_backend = os.getenv("CHATBOT_BACKEND")
                if env_backend:
                    self.backend_type = env_backend.lower()
                else:
                    try:
                        if isinstance(self.model_name, str) and "meta-llama" in os.path.basename(self.model_name).lower():
                            self.backend_type = "meta-llama"
                        else:
                            self.backend_type = "gpt4all"
                    except Exception:
                        self.backend_type = "gpt4all"

                preferred_device = os.getenv("GPT4ALL_DEVICE")
                tried_devices = []
                if preferred_device:
                    candidate_devices = [preferred_device]
                else:
                    candidate_devices = ["cuda", "cuda:0", "gpu", "cuda:1", "cpu"]

                last_exc = None
                if self.backend_type == "meta-llama":
                    try:
                        from llama_cpp import Llama  # type: ignore

                        n_threads = int(os.getenv("LLAMA_N_THREADS", "8"))
                        n_gpu_layers = int(os.getenv("LLAMA_N_GPU_LAYERS", "40"))
                        n_batch = int(os.getenv("LLAMA_N_BATCH", "512"))
                        n_ctx = int(os.getenv("CHATBOT_CONTEXT_WINDOW", str(self.context_window)))

                        os.environ.setdefault("GGML_CUDA_FORCE_CUBLAS", "1")
                        os.environ.setdefault("GGML_CUDA_FORCE_MMQ", "1")

                        logger.info("Intentando cargar Meta-Llama (llama_cpp): model=%s", self.model_name)
                        logger.info(
                            "→ n_threads=%s, n_gpu_layers=%s, n_batch=%s, n_ctx=%s",
                            n_threads,
                            n_gpu_layers,
                            n_batch,
                            n_ctx,
                        )

                        self.model = Llama(
                            model_path=self.model_name,
                            n_ctx=n_ctx,
                            n_threads=n_threads,
                            n_gpu_layers=n_gpu_layers,
                            n_batch=n_batch,
                            verbose=True,
                        )

                        self._device = "cuda" if n_gpu_layers > 0 else "cpu"
                        self._backend = "llama_cpp"
                        self._loaded_at = datetime.utcnow()
                        self.model_failed = False
                        self._failed_at = None
                        logger.info(
                            "✅ Meta-Llama cargado exitosamente via llama_cpp (GPU activa)"
                            if n_gpu_layers > 0
                            else "✅ Meta-Llama cargado (CPU)"
                        )
                        last_exc = None
                    except Exception as e_meta:  # pragma: no cover - best effort GPU init
                        last_exc = e_meta
                        logger.warning("⚠️ Fallo cargando Meta-Llama via llama_cpp: %s", e_meta)

                if self.model is None:
                    candidate_devices = ["cpu"]
                    for device in candidate_devices:
                        tried_devices.append(device)
                        logger.info(
                            "Intentando inicializar GPT4All en %s con modelo: %s",
                            device,
                            self.model_name,
                        )
                        try:
                            self.model = GPT4All(self.model_name, device=device)
                            self._device = device
                            self._backend = getattr(self.model, "backend", "gpt4all")
                            self._loaded_at = datetime.utcnow()
                            self.model_failed = False
                            self._failed_at = None
                            logger.info("Modelo GPT4All cargado en %s", device)
                            last_exc = None
                            break
                        except Exception as e_device:
                            last_exc = e_device
                            logger.warning("Fallo cargando GPT4All en %s: %s", device, e_device)

                if last_exc is not None and self.model is None:
                    logger.error(
                        "No se pudo inicializar el modelo en dispositivos intentados: %s",
                        tried_devices,
                    )
                    raise last_exc
            except Exception as e:  # pragma: no cover - defensive fallback
                self.model_failed = True
                try:
                    self._failed_at = datetime.utcnow()
                except Exception:
                    self._failed_at = None
                logger.error("Error cargando modelo: %s", e)
                logger.info(
                    "TIP: Descarga el modelo con: python -c 'from gpt4all import GPT4All; GPT4All(\"orca-mini-3b-gguf2-q4_0.gguf\")'"
                )
                traceback.print_exc()
            finally:
                self._initializing = False

    def status(self) -> dict:
        st = {
            "model_loaded": self.model is not None,
            "model_failed": self.model_failed,
            "model_name": getattr(self, "model_name", None),
            "device": self._device,
            "backend": self._backend,
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at is not None else None,
            "failed_at": getattr(self, "_failed_at", None).isoformat() if getattr(self, "_failed_at", None) else None,
        }
        st.update(
            {
                "max_faqs": getattr(self, "max_faqs", None),
                "faq_answer_max_chars": getattr(self, "faq_answer_max_chars", None),
                "context_window": getattr(self, "context_window", None),
                "context_token_ratio": getattr(self, "context_token_ratio", None),
                "reserve_response_tokens": getattr(self, "reserve_response_tokens", None),
            }
        )
        return st

    def build_context(
        self,
        business: Business,
        faqs: List[FAQ],
        max_faqs: Optional[int] = None,
        *,
        include_default_instructions: bool = True,
        menu_focus: bool = False,
    ) -> str:
        if max_faqs is None:
            max_faqs = self.max_faqs

        context = f"""Eres un asistente virtual del negocio: {business.name}

INFORMACIÓN DEL NEGOCIO:
- Tipo: {business.business_type}
- Teléfono: {business.phone or 'No especificado'}
- Email: {business.email or 'No especificado'}
- Dirección: {business.address or 'No especificada'}
- Web: {business.website or 'No especificada'}

PREGUNTAS FRECUENTES (usa como referencia, no copies literalmente):
"""

        try:
            faqs_sorted = sorted(faqs, key=lambda f: getattr(f, "priority", 0), reverse=True)
        except Exception:
            faqs_sorted = faqs

        included = faqs_sorted[:max_faqs]
        truncated = len(faqs_sorted) > max_faqs
        
        logger.info(f"📝 Construyendo contexto con {len(included)} FAQs de {len(faqs_sorted)} disponibles (max_faqs={max_faqs})")

        for faq in included:
            q = (faq.question or "")[: self.faq_question_max_chars]
            a = (faq.answer or "")[: self.faq_answer_max_chars]
            context += f"\n• Si el cliente pregunta '{q}', puedes responder con algo como: '{a}'.\n"

        if truncated:
            context += "\n[Nota: algunas FAQs se han omitido por límite de contexto.]\n"

        tone_map = {
            "restaurant": "Usa un tono cálido, cercano y gastronómico 🍽️",
            "gym": "Usa un tono motivador y energético 💪",
            "hotel": "Usa un tono profesional, servicial y tranquilo 🏨",
            "store": "Usa un tono amable y práctico 🛍️",
            "clinic": "Usa un tono respetuoso y calmado 👩‍⚕️",
        }
        business_type = (business.business_type or "").lower()
        tone_instruction = tone_map.get(business_type, "Usa un tono profesional y amable.")
        if getattr(business, "tone_override", None):
            tone_instruction = business.tone_override.strip()

        context += f"\nTONO RECOMENDADO: {tone_instruction}\n"

        if getattr(business, "welcome_message", None):
            context += (
                "MENSAJE DE BIENVENIDA A TRANSMITIR: "
                f"{business.welcome_message.strip()}\n"
            )

        default_behavior_instructions = """
=== INSTRUCCIONES GENERALES DE COMPORTAMIENTO ===

Eres un asistente virtual profesional y amable diseñado para ayudar a los clientes de una empresa.

TU MISIÓN:
- Ofrecer respuestas claras, útiles y empáticas.
- Representar los valores de la marca con un tono profesional, cercano y positivo.
- Resolver dudas frecuentes, ofrecer información actualizada y guiar al cliente con naturalidad.

TONO Y ESTILO:
- Siempre saluda cordialmente al inicio (puedes incluir un emoji si encaja con la marca).
- Usa un tono adecuado al tipo de negocio:
  • Restaurantes: cercano y gastronómico. Ej: “🍽️ ¡Hola! Será un placer ayudarte con tu reserva.”
  • Gimnasios: enérgico y motivador. Ej: “💪 ¡Hola! Gracias por contactar con nuestro gimnasio.”
  • Hoteles: profesional y servicial. Ej: “🏨 Bienvenido/a, estaré encantado de ayudarte con tu estancia.”
  • Tiendas: amable y práctico. Ej: “🛍️ ¡Hola! Cuéntame qué necesitas y te ayudo enseguida.”
  • Clínicas o centros médicos: respetuoso y calmado. Ej: “👩‍⚕️ ¡Hola! Estoy aquí para ayudarte con la información que necesites.”
  • Otros negocios: tono neutro pero siempre educado y servicial.

CÓMO DIRIGIRSE AL CLIENTE:
- Usa un trato de “tú” si la empresa se comunica de forma informal, o “usted” si el negocio es más formal (médico, legal, etc.).
- Evita tecnicismos innecesarios y mantén frases naturales.
- Nunca discutas ni respondas con ironía; si el cliente está molesto, responde con calma y cortesía.

ESTRUCTURA DE RESPUESTA:
1. **Saludo breve + empatía:** demuestra atención y disposición (“¡Hola! Claro que sí, te cuento…”).
2. **Respuesta directa y útil:** proporciona la información principal sin rodeos.
3. **Matiz extra:** añade un dato o consejo breve que aporte valor.
4. **Cierre amable:** ofrece ayuda adicional (“¿Quieres que te dé más detalles?” o “¿Deseas que te ayude con algo más?”).

REGLAS DE CONTENIDO:
- Usa la información del negocio y las FAQs disponibles.
- Si el cliente pide la web o sitio, utiliza la URL indicada en la información del negocio. No confundas la web con el email.
- Si no sabes algo, sugiere amablemente contactar directamente (“Puedes llamar al {teléfono} o escribir a {email} para más detalles.”).
- No inventes datos ni hagas suposiciones peligrosas (por ejemplo, precios o diagnósticos).
- Si el usuario da las gracias o se despide, responde de forma personalizada y breve (“¡Gracias a ti! 😊 Que tengas un gran día.”).
- Nunca reveles información interna ni menciones que eres un modelo de IA.

FORMATOS:
- Respuestas concisas (3-5 frases máximo).
- Puedes usar listas cortas (máximo 3 puntos) si ayuda a la claridad.
- Evita repeticiones o copiar texto literal del contexto.

EN CASO DE ERRORES:
- Si el cliente hace una pregunta fuera del alcance (ej. algo muy técnico o no relacionado), responde con cortesía y redirige (“No dispongo de esa información exacta, pero puedes consultar a nuestro equipo en {email}.”).

OBJETIVO FINAL:
Haz que el cliente se sienta atendido, escuchado y guiado, como si hablara con una persona real del negocio.
"""

        if include_default_instructions:
            context += default_behavior_instructions
        elif menu_focus:
            context += """
=== GUÍA PARA RESPUESTA DE MENÚ ===

El cliente quiere conocer el menú del negocio. Responde siguiendo estas pautas:
- Organiza la información en viñetas claras (3 a 6 puntos) con el nombre del plato y una breve descripción o ingredientes clave.
- Agrupa los platos por categoría lógica (entrantes, principales, postres, bebidas) si la información lo permite.
- Indica precios cuando estén disponibles en la información proporcionada.
- Mantén un tono entusiasta pero profesional.
- Cierra invitando al cliente a pedir más detalles o hacer una reserva.
"""
        else:
            context += default_behavior_instructions
        return context

    def get_response(
        self,
        message: str,
        context: str,
        *,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        welcome_message: Optional[str] = None,
        suppress_greeting: bool = False,
        customer_name: Optional[str] = None,
        name_already_used: bool = False,
        db=None,
        business=None,
        wants_all_rules: bool = False,
        num_faqs_in_context: int = 4,
    ) -> str:
        if self.model_failed:
            try:
                phone = context.split("Teléfono: ")[1].splitlines()[0]
            except Exception:
                phone = "el negocio"
            return f"Lo siento, el servicio no está disponible ahora. Puedes contactar con {phone}."

        try:
            self.initialize_model()
        except Exception:
            return "Lo siento, no puedo responder en este momento."

        saludos_simples = [
            "hola",
            "buenas",
            "buenas tardes",
            "buenos días",
            "buenas noches",
            "qué tal",
            "hey",
            "holaa",
            "holaaa",
        ]
        msg_lower = message.strip().lower()

        business_type = "restaurant"
        try:
            business_type = context.split("Tipo: ")[1].splitlines()[0].lower().strip()
        except Exception:
            pass

        emoji_map = {
            "restaurant": "🍽️",
            "gym": "💪",
            "hotel": "🏨",
            "store": "🛍️",
            "clinic": "👩‍⚕️",
        }
        default_emoji = emoji_map.get(business_type, "😊")

        if any(msg_lower == s or msg_lower.strip("!?.") == s for s in saludos_simples):
            if suppress_greeting:
                if customer_name and not name_already_used:
                    short = (
                        f"{default_emoji} {customer_name}, dime cómo puedo ayudarte."
                        if len(msg_lower) <= 8
                        else f"{default_emoji} {customer_name}, aquí estoy para ayudarte con lo que necesites."
                    )
                    return short
                if customer_name and name_already_used:
                    return (
                        f"{default_emoji} Claro, dime cómo puedo ayudarte."
                        if len(msg_lower) <= 8
                        else f"{default_emoji} Aquí estoy para ayudarte con lo que necesites."
                    )
                return (
                    f"{default_emoji} Aquí estoy, dime en qué puedo ayudarte."
                    if len(msg_lower) <= 8
                    else f"{default_emoji} Aquí estoy para ayudarte con lo que necesites."
                )
            if welcome_message:
                cleaned = welcome_message.strip()
                if cleaned:
                    return cleaned

            if "restaurant" in business_type:
                return "¡Hola! 😊 Qué gusto verte por aquí. ¿Quieres ver la carta o prefieres hacer una reserva?"
            if "gym" in business_type:
                return "¡Hola! 💪 Qué alegría verte por aquí. ¿Quieres saber los horarios o ver las clases disponibles?"
            if "hotel" in business_type:
                return "¡Hola! 🏨 Bienvenido, ¿quieres consultar la disponibilidad o conocer nuestras habitaciones?"
            return "¡Hola! 😊 Qué gusto verte por aquí. ¿En qué puedo ayudarte hoy?"

        wants_menu = self.is_menu_request(message)

        # Si es consulta de menú, extraer información estructurada del documento
        menu_extracted = None
        if wants_menu and db:
            menu_extracted = self.extract_menu_from_documents(db, business.id)
            if menu_extracted:
                logger.info("→ Menú extraído estructuradamente de documentos")

        extra_instructions = []
        
        # Para normas, siempre suprimir saludo innecesario
        if wants_all_rules:
            extra_instructions.append("NO repitas saludos ni preguntas. El cliente ya te preguntó algo específico. Responde directo.")
        elif suppress_greeting:
            extra_instructions.append("Si ya saludaste al cliente en turnos previos, no repitas el saludo inicial.")
        
        if customer_name and not name_already_used:
            extra_instructions.append(
                f"El cliente se llama {customer_name}. Usa su nombre de forma natural una única vez en la respuesta."
            )
        elif customer_name and name_already_used:
            extra_instructions.append(
                f"El cliente se llama {customer_name}, pero ya lo mencionaste antes; evita repetirlo salvo que el cliente lo pida explícitamente."
            )
        
        # Instrucción especial para listar TODAS las normas cuando se pregunta en plural
        if wants_all_rules:
            logger.info("📋 Detectado: Cliente pregunta por TODAS las normas (usando cálculo automático de tokens)")
            extra_instructions.append(
                "El cliente pregunta por las normas. Responde: 'Las normas principales del gimnasio son: ' "
                "seguido de TODAS las normas de las FAQs de forma breve, separadas por comas. "
                "Formato: 'llevar tarjeta de socio, prohibido fumar y alcohol, no acceso bajo efectos de drogas, "
                "limpiar material tras uso, no dejar pesas en suelo, usar toalla en máquinas, máximo 30 min en máquinas, "
                "prohibido grabar sin consentimiento, reservar clases, ducharse antes de spa, informar incidentes, "
                "mantener taquillas cerradas, no gritar ni lanzar pesas, respetar a otros, edad mínima 16 años, "
                "prohibidas mascotas, ropa deportiva obligatoria, cancelar reservas si no asistes, y cualquier otra mencionada.' "
                "IMPORTANTE: Termina la última norma con 'y [última norma].' usando punto final. NO uses puntos suspensivos."
            )
        
        if wants_menu:
            if menu_extracted:
                # Si tenemos menú estructurado, dar instrucciones específicas
                extra_instructions.append(
                    "El cliente quiere conocer el menú. DEBES listar EXACTAMENTE los platos que aparecen a continuación."
                )
                extra_instructions.append(
                    "PROHIBIDO ABSOLUTAMENTE inventar, añadir o modificar nombres de platos."
                )
                extra_instructions.append(
                    "Copia los platos tal como aparecen en la sección 'MENÚ DISPONIBLE'."
                )
            else:
                # Fallback a instrucciones generales si no hay menú estructurado
                extra_instructions.append(
                    "El cliente quiere conocer el menú. Lista ÚNICAMENTE los platos exactos que aparecen en la información del negocio."
                )
                extra_instructions.append(
                    "PROHIBIDO inventar o crear platos nuevos. Solo menciona platos que están explícitamente en la información."
                )
                extra_instructions.append(
                    "Si no encuentras información del menú completo, di que no tienes esa información disponible."
                )

        def _build_prompt(context_block: str) -> str:
            # Si hay menú extraído, inyectarlo al principio del contexto
            enhanced_context = context_block
            if menu_extracted:
                enhanced_context = f"{menu_extracted}\n\n{'='*60}\n\n{context_block}"
            
            # Instrucciones base variables según el tipo de consulta
            if wants_all_rules:
                # Prompt especial para listar normas (sin límite de frases)
                base = (
                    f"Información del negocio:\n{enhanced_context}\n\n"
                    f"Cliente: {message}\n\n"
                    "Eres una persona que trabaja en este negocio y hablas con el cliente en tono amable. "
                    "El cliente pregunta por las normas. Debes listar TODAS las normas mencionadas en la información de arriba. "
                    "Escribe una respuesta COMPLETA y LARGA mencionando todas las normas sin omitir ninguna. "
                    "No te limites a 1 o 2 normas. Menciona TODAS. "
                    "No menciones que eres asistente virtual."
                )
            else:
                # Prompt normal para respuestas cortas
                base = (
                    f"Información del negocio:\n{enhanced_context}\n\n"
                    f"Cliente: {message}\n\n"
                    "Eres una persona que trabaja en este negocio y hablas con el cliente en tono amable, natural y cercano. "
                    "Responde SOLO lo que el cliente pregunta. "
                    "IMPORTANTE: Si el cliente pregunta algo específico, responde ÚNICAMENTE sobre ese tema. "
                    "NO mezcles información de diferentes temas o FAQs en una misma respuesta. "
                    "NO combines múltiples FAQs si el cliente solo preguntó por una cosa específica. "
                    "Da una respuesta directa de una o dos frases completas, sin sonar robótico ni demasiado formal. "
                    "NO hagas preguntas adicionales al final de tu respuesta. "
                    "NO preguntes '¿Qué harías si...?' ni generes escenarios hipotéticos. "
                    "NO repitas la misma frase múltiples veces. "
                    "Termina tu respuesta de forma natural y concisa. "
                    "Nunca respondas solo con un saludo. "
                    "No menciones que eres asistente virtual ni uses expresiones como 'respuesta:' o 'cliente:'."
                )
            if extra_instructions:
                base += "\n" + " ".join(extra_instructions)
            return base + "\n\nRespuesta:"

        allowed_prompt_tokens = max(1, self.context_window - self.reserve_response_tokens)
        context_token_budget = allowed_prompt_tokens
        safe_context = self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget)
        prompt = _build_prompt(safe_context)

        approx_tokens = max(1, len(prompt) // max(1, self.context_token_ratio))
        shrink_attempts = 0
        while approx_tokens > allowed_prompt_tokens and shrink_attempts < 5 and context_token_budget > 64:
            shrink_attempts += 1
            context_token_budget = max(32, int(context_token_budget * 0.75))
            safe_context = self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget)
            prompt = _build_prompt(safe_context)
            approx_tokens = max(1, len(prompt) // max(1, self.context_token_ratio))

        if approx_tokens > allowed_prompt_tokens:
            context_token_budget = max(32, allowed_prompt_tokens // 2)
            safe_context = self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget)
            prompt = _build_prompt(safe_context)

        temp_value = temperature if temperature is not None else 0.45
        # Para menú usar temperatura muy baja para evitar invenciones
        if wants_menu:
            temp_value = 0.15
        # Para listar normas usar temperatura más alta para generar respuestas completas
        elif wants_all_rules:
            temp_value = 0.85  # Temperatura alta para enumerar todas las normas sin cortarse
            logger.info(f"→ Usando temperatura={temp_value} para listar normas (mayor verbosidad)")
        
        top_p_value = top_p if top_p is not None else 0.85
        if wants_all_rules:
            top_p_value = 0.95  # Aumentar diversidad en la generación
        
        # ============================================================================
        # CÁLCULO INTELIGENTE DE max_tokens BASADO EN EL CONTENIDO A GENERAR
        # ============================================================================
        if wants_all_rules:
            # Usar el número de FAQs que realmente se incluyeron en el contexto
            num_faqs = num_faqs_in_context
            
            # Estimación: cada norma necesita ~10-15 palabras concisas (~15-20 tokens)
            # Aumentamos a 50 tokens por norma para dar margen muy generoso
            estimated_tokens_per_rule = 50
            estimated_total = num_faqs * estimated_tokens_per_rule
            
            # Añadir tokens para texto introductorio (~70 tokens)
            intro_tokens = 70
            
            # Añadir margen de seguridad del 100% (doble del estimado)
            safety_margin = 2.0
            
            max_tokens_out = int((estimated_total + intro_tokens) * safety_margin)
            
            # Límites razonables: mínimo 1200, máximo 3500
            max_tokens_out = max(1200, min(max_tokens_out, 3500))
            
            logger.info(f"→ Cálculo inteligente de tokens:")
            logger.info(f"   • FAQs a incluir: {num_faqs}")
            logger.info(f"   • Estimación base: {num_faqs} × {estimated_tokens_per_rule} = {estimated_total} tokens")
            logger.info(f"   • Con intro y margen 100%: {max_tokens_out} tokens")
        elif wants_menu:
            max_tokens_out = 400  # Tokens para menú
        else:
            max_tokens_out = 300  # Tokens para respuestas normales

        def _generate():
            if getattr(self, "_backend", None) == "llama_cpp":
                out = self.model(
                    prompt=prompt,
                    max_tokens=max_tokens_out,
                    temperature=temp_value,
                    top_p=top_p_value,
                )
                try:
                    return out["choices"][0]["text"]
                except Exception:
                    return str(out)
            return self.model.generate(
                prompt,
                max_tokens=max_tokens_out,
                temp=temp_value,
                top_p=top_p_value,
                top_k=40,
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_generate)
                response = fut.result(timeout=self.generate_timeout)

            if isinstance(response, dict):
                response = response.get("text", str(response))
            response = str(response)

            # LIMPIEZA AGRESIVA: Eliminar TODAS las instrucciones del sistema que se filtren
            # Patrón 1: Eliminar instrucciones explícitas del prompt
            response = re.sub(r"(?i)(asistente virtual|respuesta:|cliente:|instrucciones?:|información del negocio:).*", "", response)
            
            # Patrón 2: Eliminar frases que contengan "Eres una persona que trabaja"
            response = re.sub(r"(?i)eres una persona que trabaja.*?(\.|$)", "", response, flags=re.DOTALL)
            
            # Patrón 3: Eliminar instrucciones sobre cómo responder
            response = re.sub(r"(?i)(responde? solo|no hagas preguntas|no repitas|termina tu respuesta|nunca respondas|no menciones).*?(\.|$)", "", response, flags=re.DOTALL)
            
            # Patrón 4: Eliminar frases que empiezan con "NO" (instrucciones negativas)
            response = re.sub(r"(?i)\.\s*NO [A-Z].*?(\.|$)", ".", response)
            
            # Eliminar preguntas de entrenamiento que el modelo añade al final
            response = re.sub(r"¿Qué harías si.*?$", "", response, flags=re.IGNORECASE | re.DOTALL)
            response = re.sub(r"¿Qué tipo de.*?\?", "", response, flags=re.IGNORECASE)
            response = re.sub(r"¿Cuál es.*?\?(?=\s*$)", "", response, flags=re.IGNORECASE)
            response = re.sub(r"¿Dónde se.*?\?(?=\s*$)", "", response, flags=re.IGNORECASE)
            
            # Detectar y eliminar patrones repetitivos (como "¡Hasta luego! 👋" repetido)
            # Buscar frases que se repiten 3+ veces consecutivas
            def remove_repetitions(text):
                # Buscar patrones de 3-50 caracteres que se repiten 3+ veces
                pattern = r'(.{3,50}?)(\1{2,})'
                cleaned = re.sub(pattern, r'\1', text)
                return cleaned
            
            response = remove_repetitions(response)
            
            # Eliminar frases de despedida repetitivas al final
            response = re.sub(r'(¡Hasta luego!.*?){2,}$', '¡Hasta luego!', response, flags=re.IGNORECASE)
            response = re.sub(r'(¡Gracias!.*?){2,}$', '¡Gracias!', response, flags=re.IGNORECASE)
            response = re.sub(r'(¡Espero.*?){2,}$', '', response, flags=re.IGNORECASE)
            
            # Eliminar múltiples preguntas al final (patrón común)
            lines = response.split('\n')
            clean_lines = []
            question_count = 0
            for line in lines:
                # Si encontramos 2+ preguntas seguidas al final, las cortamos
                if line.strip().startswith('¿') and line.strip().endswith('?'):
                    question_count += 1
                    if question_count >= 2:
                        break
                else:
                    question_count = 0
                    clean_lines.append(line)
            response = '\n'.join(clean_lines).strip()

            if wants_menu:
                response = response.replace("\r\n", "\n").replace("\r", "\n")
                response = re.sub(r"[ \t]+\n", "\n", response)
                response = re.sub(r"\n{3,}", "\n\n", response)
                response = re.sub(r"\s*•", "\n•", response)
                if not response.startswith("•"):
                    response = "• " + response.lstrip()
                response = response.strip()
            else:
                response = re.sub(r"\s+", " ", response).strip()
            
            # LIMPIEZA FINAL: Eliminar cualquier resto de instrucciones que haya quedado
            # Buscar y eliminar frases sospechosas que contengan palabras clave de instrucciones
            suspicious_keywords = [
                "eres una persona", "trabaja en este negocio", "tono amable", 
                "responde solo", "no hagas preguntas", "no repitas", "no menciones",
                "asistente virtual", "instrucciones", "formato de respuesta"
            ]
            for keyword in suspicious_keywords:
                # Eliminar cualquier oración que contenga estas palabras
                pattern = r"[^.!?]*" + re.escape(keyword) + r"[^.!?]*[.!?]?"
                response = re.sub(pattern, "", response, flags=re.IGNORECASE)
            
            # Limpiar espacios duplicados después de todas las eliminaciones
            response = re.sub(r"\s+", " ", response).strip()

            # Limitar número de frases solo si la respuesta es muy larga
            if not wants_menu:
                sentences = re.split(r"(?<=[.!?])\s", response)
                sentence_limit = 4  # Aumentado de 2 a 4 frases
                if len(sentences) > sentence_limit:
                    response = " ".join(sentences[:sentence_limit]).strip()

            if re.search(r"\b(de|que|para|con|en|a|por|sobre)$", response):
                response = response.rstrip(". ") + "."

            max_length = 2000 if wants_menu else 500  # Aumentado de 300 a 500 caracteres
            if len(response) > max_length:
                if wants_menu:
                    cutoff = response[:max_length]
                    
                    # Intentar cortar después de un plato completo (buscar punto + salto de línea)
                    last_item = cutoff.rfind(".\n•")
                    if last_item > max_length * 0.5:
                        cutoff = cutoff[:last_item + 1]  # Incluir el punto
                    else:
                        # Si no hay items con viñetas, buscar salto de línea
                        last_break = cutoff.rfind("\n")
                        if last_break > max_length * 0.6:
                            cutoff = cutoff[:last_break]
                        else:
                            # Último recurso: buscar último punto
                            last_period = cutoff.rfind(". ")
                            if last_period > max_length * 0.5:
                                cutoff = cutoff[:last_period + 1]
                            else:
                                cutoff = cutoff.rsplit(" ", 1)[0]
                    
                    response = cutoff.rstrip()
                    if not response.endswith('.'):
                        response += "…"
                else:
                    response = response[:max_length].rsplit(" ", 1)[0] + "..."

            if not response:
                response = "Lo siento, no tengo esa información exacta. Puedes contactar con el negocio directamente."

            return response.strip()

        except Exception as e:  # pragma: no cover - best effort logging
            logger.exception("Error en get_response: %s", e, exc_info=True)
            return "Lo siento, ha ocurrido un error generando la respuesta."

    

chatbot_service = ChatbotService()

__all__ = ["ChatbotService", "chatbot_service"]
