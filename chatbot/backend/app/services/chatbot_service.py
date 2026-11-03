"""Core chatbot service responsible for constructing prompts and generating replies."""
from __future__ import annotations

import concurrent.futures
import logging
import os
import re
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rapidfuzz import fuzz

from ..models import Business, Conversation, DocumentChunk, FAQ

logger = logging.getLogger("chatbot")

# Palabras vacías para puntuar la relevancia de una FAQ respecto a la pregunta
_STOPWORDS = frozenset(
    "el la los las un una unos unas de del al y o en a que es son se me te mi tu su sus por para con sin como "
    "cual cuales quien quienes donde cuando hay tiene tienen puedo puede pueden quiero quieres hola buenas "
    "dime saber sobre algo muy mas".split()
)

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_MODEL_FILE = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
FALLBACK_MODEL = "orca-mini-3b-gguf2-q4_0.gguf"

# Tipos de información que se responden directo desde una FAQ prioritaria.
# ORDEN IMPORTANTE: los más específicos primero para evitar conflictos.
# (menú va al final para no pisar patrones más específicos)
_CRITICAL_TYPES = {
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



class ChatbotService:
    def __init__(self) -> None:
        self.model = None
        self.model_name = self._resolve_model_name()
        self.model_failed = False
        self.generate_timeout = float(os.getenv("CHATBOT_GENERATE_TIMEOUT", "30"))
        self._init_lock = threading.Lock()
        self._generate_lock = threading.Lock()  # llama.cpp/GPT4All no son thread-safe: una generación a la vez
        self._initializing = False
        self._device = None
        self._backend = None
        self._loaded_at = None
        self._failed_at = None
        self.backend_type = None
        self.max_faqs = int(os.getenv("CHATBOT_MAX_FAQS", "4"))
        self.faq_answer_max_chars = int(os.getenv("CHATBOT_FAQ_ANSWER_MAX_CHARS", "250"))
        self.faq_question_max_chars = int(os.getenv("CHATBOT_FAQ_QUESTION_MAX_CHARS", "200"))
        self.context_token_ratio = int(os.getenv("CHATBOT_CONTEXT_TOKEN_RATIO", "3"))  # español: ~3 caracteres/token
        self.context_window = int(os.getenv("CHATBOT_CONTEXT_WINDOW", os.getenv("GPT4ALL_CONTEXT_WINDOW", "4096")))
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
        """Detecta si el usuario pide información estructurada (menú, clases, precios, ...).

        Devuelve {'type', 'keywords', 'emoji'} del primer tipo de _CRITICAL_TYPES cuyo
        patrón coincide con el mensaje, o None.
        """
        message_lower = message.lower()
        for critical_type, config in _CRITICAL_TYPES.items():
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower):
                    logger.info("🎯 Detectado tipo crítico: %s (patrón: %s)", critical_type, pattern)
                    return {
                        "type": critical_type,
                        "keywords": config["keywords"],
                        "emoji": config["emoji"],
                    }
        return None
    
    def extract_menu_from_documents(self, db, business_id: int) -> Optional[str]:
        """Extrae el menú (tabla Categoría/Plato/Descripción/Precio) de los documentos del negocio."""
        try:
            chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.business_id == business_id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )
            if not chunks:
                return None

            full_text = "\n".join(chunk.text for chunk in chunks)
            match = re.search(r"Menú principal\s+(.*?)(?=\n\n[A-Z]|\Z)", full_text, re.DOTALL | re.IGNORECASE)
            if not match:
                logger.warning("→ No se encontró sección 'Menú principal'")
                return None

            dishes = []
            seen_names = set()
            header_found = False
            for line in match.group(1).strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "Categoría" in line and "Plato" in line:
                    header_found = True
                    continue
                if not header_found:
                    continue

                parts = re.split(r"\s{2,}", line)  # Categoría   Plato   Descripción   Precio
                if len(parts) < 4:
                    continue
                _, name, description, price = (p.strip() for p in parts[:4])
                if (
                    name
                    and name not in seen_names
                    and name.lower() not in ("plato", "categoría", "descripción")
                    and re.search(r"\d+[.,]\d+", price)
                ):
                    seen_names.add(name)
                    dishes.append((name, description, price.replace("■", "-")))  # fix encoding

            if not dishes:
                logger.warning("→ No se extrajeron platos")
                return None

            listing = "".join(f"• **{name}** - {desc} - {price}€\n" for name, desc, price in dishes)
            return (
                "**MENÚ DISPONIBLE (platos reales del restaurante):**\n\n"
                f"{listing}"
                "\n**IMPORTANTE: Estos son TODOS los platos disponibles. No existen otros platos.**"
            )
        except Exception:
            logger.exception("Error extrayendo menú de documentos")
            return None


    @staticmethod
    def _resolve_model_name() -> str:
        """CHATBOT_MODEL_NAME (ruta o fichero en models/) > Llama por defecto > orca-mini."""
        env_model = os.getenv("CHATBOT_MODEL_NAME")
        if env_model:
            if os.path.isabs(env_model) or os.path.exists(env_model):
                return env_model
            candidate = MODELS_DIR / env_model
            return str(candidate) if candidate.exists() else env_model
        default_model = MODELS_DIR / DEFAULT_MODEL_FILE
        return str(default_model) if default_model.exists() else FALLBACK_MODEL

    def reset_failure(self) -> None:
        self.model_failed = False
        self._failed_at = None

    def ensure_ready(self) -> Optional[str]:
        """None si el modelo está listo; si no, lanza la carga en segundo plano y devuelve un aviso para el cliente."""
        if self.model_failed and self.model is not None:
            self.reset_failure()
        if self.model is not None:
            return None
        if self._initializing:
            return "El modelo se está inicializando. Por favor espera unos segundos y vuelve a intentarlo."
        threading.Thread(target=self.initialize_model, daemon=True).start()
        return "El modelo se está preparando. Intenta de nuevo en unos segundos."

    def _mark_loaded(self, device: str, backend: str) -> None:
        self._device = device
        self._backend = backend
        self._loaded_at = datetime.utcnow()
        self.reset_failure()

    def _load_llama_cpp(self) -> None:
        """Intenta cargar el modelo con llama.cpp; si falla, deja self.model en None."""
        try:
            from llama_cpp import Llama  # type: ignore

            n_threads = int(os.getenv("LLAMA_N_THREADS", "8"))
            n_gpu_layers = int(os.getenv("LLAMA_N_GPU_LAYERS", "40"))
            n_batch = int(os.getenv("LLAMA_N_BATCH", "512"))
            n_ctx = self.context_window

            os.environ.setdefault("GGML_CUDA_FORCE_CUBLAS", "1")
            os.environ.setdefault("GGML_CUDA_FORCE_MMQ", "1")

            logger.info(
                "Cargando Meta-Llama (llama_cpp): model=%s n_threads=%s n_gpu_layers=%s n_batch=%s n_ctx=%s",
                self.model_name, n_threads, n_gpu_layers, n_batch, n_ctx,
            )
            self.model = Llama(
                model_path=self.model_name,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,
                verbose=True,
            )
            self._mark_loaded("cuda" if n_gpu_layers > 0 else "cpu", "llama_cpp")
            logger.info("✅ Meta-Llama cargado via llama_cpp (%s)", self._device)
        except Exception as exc:  # pragma: no cover - best effort GPU init
            logger.warning("⚠️ Fallo cargando Meta-Llama via llama_cpp: %s", exc)

    def _load_gpt4all(self) -> None:
        """Carga GPT4All en CPU. Propaga la excepción si falla."""
        from gpt4all import GPT4All  # import diferido: solo se necesita si llama.cpp no cargó

        logger.info("Cargando GPT4All (cpu): %s", self.model_name)
        self.model = GPT4All(self.model_name, device="cpu")
        self._mark_loaded("cpu", getattr(self.model, "backend", "gpt4all"))

    def initialize_model(self) -> None:
        """Carga el modelo una sola vez (thread-safe): llama.cpp si procede, GPT4All como respaldo."""
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
                env_backend = os.getenv("CHATBOT_BACKEND")
                if env_backend:
                    self.backend_type = env_backend.lower()
                elif "meta-llama" in os.path.basename(self.model_name).lower():
                    self.backend_type = "meta-llama"
                else:
                    self.backend_type = "gpt4all"

                if self.backend_type == "meta-llama":
                    self._load_llama_cpp()
                if self.model is None:
                    self._load_gpt4all()
            except Exception as exc:  # pragma: no cover - defensive fallback
                self.model_failed = True
                self._failed_at = datetime.utcnow()
                logger.exception("Error cargando modelo: %s", exc)
                logger.info(
                    "TIP: Descarga el modelo con: python -c 'from gpt4all import GPT4All; GPT4All(\"orca-mini-3b-gguf2-q4_0.gguf\")'"
                )
            finally:
                self._initializing = False

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        top_p: float = 0.85,
        top_k: int = 40,
    ) -> str:
        """Genera texto con el backend cargado (llama.cpp o GPT4All). Requiere el modelo inicializado."""
        with self._generate_lock:
            if self._backend == "llama_cpp":
                out = self.model(prompt=prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p)
                try:
                    return out["choices"][0]["text"]
                except (KeyError, IndexError, TypeError):
                    return str(out)
            return str(
                self.model.generate(prompt, max_tokens=max_tokens, temp=temperature, top_p=top_p, top_k=top_k)
            )

    def generate_chat(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int,
        temperature: float,
        top_p: float = 0.85,
        top_k: int = 40,
    ) -> str:
        """Como `generate`, pero con la plantilla de chat del modelo (llama.cpp). GPT4All recibe texto plano."""
        if self._backend == "llama_cpp":
            with self._generate_lock:
                out = self.model.create_chat_completion(
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                )
            try:
                return out["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError):
                return str(out)
        return self.generate(
            f"{system}\n\nCliente: {user}\n\nRespuesta:",
            max_tokens=max_tokens, temperature=temperature, top_p=top_p, top_k=top_k,
        )

    @staticmethod
    def _clean_response(response: str, wants_menu: bool) -> str:
        """Quita restos del prompt y repeticiones, y ajusta formato y longitud de la respuesta."""
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

    def status(self) -> dict:
        return {
            "model_loaded": self.model is not None,
            "model_failed": self.model_failed,
            "model_name": self.model_name,
            "device": self._device,
            "backend": self._backend,
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
            "failed_at": self._failed_at.isoformat() if self._failed_at else None,
            "max_faqs": self.max_faqs,
            "faq_answer_max_chars": self.faq_answer_max_chars,
            "context_window": self.context_window,
            "context_token_ratio": self.context_token_ratio,
            "reserve_response_tokens": self.reserve_response_tokens,
        }

    @staticmethod
    def _normalize(text: str) -> str:
        """Minúsculas y sin tildes, para comparar textos."""
        decomposed = unicodedata.normalize("NFD", (text or "").lower())
        return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")

    def _rank_faqs(self, faqs: List[FAQ], query: Optional[str]) -> List[FAQ]:
        """Ordena las FAQs por relevancia respecto a la pregunta; sin pregunta, solo por prioridad."""
        def priority(f: FAQ) -> int:
            return getattr(f, "priority", 0) or 0

        keywords = [
            w for w in re.findall(r"\w+", self._normalize(query or ""))
            if len(w) > 2 and w not in _STOPWORDS
        ]
        if not keywords:
            return sorted(faqs, key=priority, reverse=True)

        norm_query = " ".join(keywords)

        def score(f: FAQ) -> float:
            q = self._normalize(f.question)
            a = self._normalize(f.answer)
            points = sum(2 for kw in keywords if kw[:5] in q) + sum(1 for kw in keywords if kw[:5] in a)
            return points + fuzz.token_set_ratio(norm_query, q) / 100

        return sorted(faqs, key=lambda f: (score(f), priority(f)), reverse=True)

    def build_context(
        self,
        business: Business,
        faqs: List[FAQ],
        max_faqs: Optional[int] = None,
        *,
        include_default_instructions: bool = True,
        menu_focus: bool = False,
        query: Optional[str] = None,
    ) -> str:
        if max_faqs is None:
            max_faqs = self.max_faqs

        context = f"""NEGOCIO: {business.name}

INFORMACIÓN DEL NEGOCIO:
- Tipo: {business.business_type}
- Teléfono: {business.phone or 'No especificado'}
- Email: {business.email or 'No especificado'}
- Dirección: {business.address or 'No especificada'}
- Web: {business.website or 'No especificada'}

PREGUNTAS FRECUENTES:
"""

        faqs_sorted = self._rank_faqs(faqs, query)

        included = faqs_sorted[:max_faqs]
        truncated = len(faqs_sorted) > max_faqs
        
        logger.info(f"📝 Construyendo contexto con {len(included)} FAQs de {len(faqs_sorted)} disponibles (max_faqs={max_faqs})")

        for faq in included:
            q = (faq.question or "")[: self.faq_question_max_chars]
            a = (faq.answer or "")[: self.faq_answer_max_chars]
            context += f"\nP: {q}\nR: {a}\n"

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

        default_behavior_instructions = (
            "\nSi el cliente da las gracias o se despide, responde de forma breve y cordial. "
            "Si pregunta por la web, usa la URL indicada en la información del negocio (no el email).\n"
        )

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
        wants_menu: Optional[bool] = None,
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

        if wants_menu is None:
            critical = self.is_critical_info_request(message)
            wants_menu = critical is not None and critical["type"] == "menú"

        # Si es consulta de menú, extraer información estructurada del documento
        menu_extracted = None
        if wants_menu and db:
            menu_extracted = self.extract_menu_from_documents(db, business.id)

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

        business_name = getattr(business, "name", None) or "este negocio"
        long_answer = wants_all_rules or wants_menu
        rules = (
            f"Eres el asistente virtual de {business_name}. Atiendes a clientes en español, con tono amable y cercano, "
            "tratando de tú.\n"
            "REGLAS:\n"
            "- Usa únicamente la información de abajo; si no está, dilo y sugiere contactar con el negocio "
            "(teléfono o email).\n"
            + ("" if long_answer else "- Responde solo a lo que se pregunta, en 1 a 3 frases completas.\n")
            + "- Habla de las personas y del negocio en tercera persona; no te hagas pasar por una persona concreta "
            "ni menciones que eres una IA.\n"
            "- No inventes datos, precios ni horarios. No mezcles temas distintos. No hagas preguntas al final. "
            "No repitas frases.\n"
            "- No uses etiquetas como 'Cliente:' o 'Respuesta:'."
        )
        if wants_all_rules:
            rules += "\n- Menciona TODAS las normas de la información, sin omitir ninguna."
        if extra_instructions:
            rules += "\n" + " ".join(extra_instructions)

        def _build_system(context_block: str) -> str:
            # Si hay menú extraído, inyectarlo al principio del contexto
            if menu_extracted:
                context_block = f"{menu_extracted}\n\n{'=' * 60}\n\n{context_block}"
            return f"{rules}\n\n{context_block}"

        allowed_prompt_tokens = max(1, self.context_window - self.reserve_response_tokens)
        context_token_budget = allowed_prompt_tokens
        system_prompt = _build_system(self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget))

        approx_tokens = max(1, (len(system_prompt) + len(message)) // max(1, self.context_token_ratio))
        shrink_attempts = 0
        while approx_tokens > allowed_prompt_tokens and shrink_attempts < 5 and context_token_budget > 64:
            shrink_attempts += 1
            context_token_budget = max(32, int(context_token_budget * 0.75))
            system_prompt = _build_system(self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget))
            approx_tokens = max(1, (len(system_prompt) + len(message)) // max(1, self.context_token_ratio))

        if approx_tokens > allowed_prompt_tokens:
            context_token_budget = max(32, allowed_prompt_tokens // 2)
            system_prompt = _build_system(self._prepare_context_for_prompt(context, message, max_tokens=context_token_budget))

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
            
            logger.info("→ max_tokens=%s para %s FAQs", max_tokens_out, num_faqs)
        elif wants_menu:
            max_tokens_out = 400  # Tokens para menú
        else:
            max_tokens_out = 300  # Tokens para respuestas normales

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(
                    self.generate_chat,
                    system_prompt,
                    message,
                    max_tokens=max_tokens_out,
                    temperature=temp_value,
                    top_p=top_p_value,
                )
                response = fut.result(timeout=self.generate_timeout)

            return self._clean_response(response, wants_menu)

        except Exception as e:  # pragma: no cover - best effort logging
            logger.exception("Error en get_response: %s", e, exc_info=True)
            return "Lo siento, ha ocurrido un error generando la respuesta."

    

chatbot_service = ChatbotService()

__all__ = ["ChatbotService", "chatbot_service"]
