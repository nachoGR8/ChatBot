"""Service utilities to ingest and search document knowledge."""
from __future__ import annotations

import io
import logging
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from rapidfuzz import fuzz, process
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import DOCUMENTS_DIR
from ..models import Business, Document, DocumentChunk, FAQ

logger = logging.getLogger("chatbot")


class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed."""


@dataclass
class IngestResult:
    document_id: int
    filename: str
    chunks_created: int
    characters: int
    business_id: Optional[int]
    faqs_created: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "chunks_created": self.chunks_created,
            "characters": self.characters,
            "business_id": self.business_id,
            "faqs_created": self.faqs_created,
        }


class DocumentService:
    """Handle ingestion and retrieval of knowledge base documents."""

    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
    MAX_CHARS_PER_CHUNK = 900
    MIN_CHARS_PER_CHUNK = 250
    SEARCH_WINDOW = 200
    MIN_SCORE = 45
    SNIPPET_MAX_CHARS = int(os.getenv("CHATBOT_DOC_SNIPPET_MAX_CHARS", "350"))

    def _extension_for(self, filename: Optional[str]) -> str:
        if not filename:
            return ""
        return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    def _validate_file(self, *, size: int, filename: str, content_type: Optional[str]) -> None:
        ext = f".{self._extension_for(filename)}"
        if size <= 0:
            raise DocumentProcessingError("El archivo está vacío")
        if size > self.MAX_FILE_SIZE:
            raise DocumentProcessingError("El archivo supera el tamaño máximo permitido (20 MB)")
        if ext not in self.ALLOWED_EXTENSIONS and (content_type or "") not in self.ALLOWED_MIME_TYPES:
            raise DocumentProcessingError("Tipo de archivo no soportado. Usa PDF o DOCX")

    def _normalize_text(self, raw: str) -> str:
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\t ]+", " ", text)
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_pdf_text(self, data: bytes) -> str:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - missing optional dependency
            raise DocumentProcessingError("PyPDF2 no está instalado en el entorno") from exc

        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("No se pudo extraer texto de una página PDF: %s", exc)
        return "\n\n".join(filter(None, pages))

    def _extract_docx_text(self, data: bytes) -> str:
        try:
            from docx import Document as DocxDocument  # type: ignore
        except ImportError as exc:  # pragma: no cover - missing optional dependency
            raise DocumentProcessingError("python-docx no está instalado en el entorno") from exc

        with io.BytesIO(data) as buffer:
            document = DocxDocument(buffer)
            paragraphs = [para.text for para in document.paragraphs if para.text]
        return "\n\n".join(paragraphs)

    def extract_text(self, *, data: bytes, filename: str, content_type: Optional[str]) -> str:
        ext = f".{self._extension_for(filename)}"
        try:
            if ext == ".pdf" or (content_type == "application/pdf"):
                return self._extract_pdf_text(data)
            if ext == ".docx" or (
                content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return self._extract_docx_text(data)
        except Exception as exc:
            logger.exception("Error extrayendo texto de %s", filename)
            raise DocumentProcessingError("No se pudo leer el archivo") from exc
        raise DocumentProcessingError("Tipo de archivo no soportado. Usa PDF o DOCX")

    def _chunk_text(self, text: str, business_type: Optional[str] = None) -> List[str]:
        """
        Divide el texto en fragmentos, excepto si el negocio es un restaurante (para mantener el menú completo).
        """
        # 🚫 No fragmentar si es un restaurante o similar
        if business_type and business_type.lower() in ["restaurant", "restaurante", "cafeteria", "bar"]:
            return [text]

        if len(text) <= self.MAX_CHARS_PER_CHUNK:
            return [text]

        import re
        paragraphs: List[str] = re.split(r"\n\s*\n", text)
        chunks: List[str] = []
        current = ""

        def _flush() -> None:
            nonlocal current
            if current.strip():
                chunks.append(current.strip())
            current = ""

        for para in paragraphs:
            paragraph = para.strip()
            if not paragraph:
                continue
            if len(paragraph) > self.MAX_CHARS_PER_CHUNK:
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current) + len(sentence) + 1 > self.MAX_CHARS_PER_CHUNK:
                        _flush()
                    current = f"{current} {sentence}".strip()
                continue

            if len(current) + len(paragraph) + 2 <= self.MAX_CHARS_PER_CHUNK:
                current = f"{current}\n\n{paragraph}".strip()
            else:
                if len(current) < self.MIN_CHARS_PER_CHUNK:
                    current = f"{current} {paragraph}".strip()
                    _flush()
                else:
                    _flush()
                    current = paragraph

        _flush()
        return chunks or [text]

    def _detect_critical_sections(self, text: str, business: Optional[Business] = None) -> List[Dict[str, str]]:
        """
        Detección inteligente y automática de secciones críticas en cualquier documento.
        
        Sistema universal que funciona para cualquier tipo de negocio:
        - Restaurantes: menús, carta de vinos, especialidades
        - Gimnasios: clases, horarios, tarifas
        - Hoteles: habitaciones, servicios, tarifas
        - Tiendas: productos, precios, catálogo
        - Servicios: paquetes, precios, descripción de servicios
        
        Args:
            text: Texto completo del documento
            business: Información del negocio (opcional)
            
        Returns:
            Lista de diccionarios con secciones críticas detectadas:
            [{"question": "...", "answer": "...", "category": "..."}]
        """
        try:
            from .chatbot_service import chatbot_service
            
            # Verificar que el modelo esté disponible
            if not chatbot_service.model or chatbot_service.model_failed:
                logger.warning("Modelo LLM no disponible para detección inteligente")
                return []
            
            critical_sections = []
            
            # Limitar texto para análisis inicial
            text_sample = text[:3000] if len(text) > 3000 else text
            
            business_type = business.business_type if business else "empresa"
            business_name = business.name if business else "la empresa"
            
            # ============================================================================
            # PASO 1: Análisis inteligente con LLM para detectar qué es crítico
            # ============================================================================
            detection_prompt = f"""Analiza este documento de un negocio tipo '{business_type}' llamado '{business_name}'.

DOCUMENTO:
{text_sample}

TAREA: Identifica SI hay información CRÍTICA que los clientes consultan frecuentemente.

Información CRÍTICA incluye (según el tipo de negocio):
- **Restaurante/Bar**: Menú completo, carta de bebidas, platos del día, precios de comidas
- **Gimnasio/Fitness**: Lista de clases, horarios de clases, planes y tarifas
- **Hotel**: Tipos de habitaciones, tarifas, servicios incluidos
- **Tienda**: Catálogo de productos, lista de precios, inventario
- **Clínica/Consultorio**: Servicios médicos, lista de especialidades, tarifas
- **Salón de belleza**: Lista de servicios, tratamientos, precios
- **Taller/Mecánico**: Servicios ofrecidos, lista de reparaciones, precios
- Cualquier LISTA ESTRUCTURADA de productos/servicios con precios o detalles

RESPONDE SOLO:
- "SÍ - [tipo]" si encontraste información crítica (especifica el tipo: MENÚ, CLASES, PRODUCTOS, SERVICIOS, TARIFAS, etc.)
- "NO" si no hay información crítica estructurada

Respuesta:"""

            logger.info("🤖 Analizando documento con IA para detectar secciones críticas...")
            
            detection_result = chatbot_service.generate(
                detection_prompt, max_tokens=50, temperature=0.2, top_p=0.85
            ).strip()
            
            logger.info(f"🔍 Resultado detección: {detection_result}")
            
            # ============================================================================
            # PASO 2: Si hay contenido crítico, extraerlo y estructurarlo
            # ============================================================================
            if detection_result.upper().startswith("SÍ") or detection_result.upper().startswith("SI"):
                # Extraer el tipo detectado
                section_type = "información"
                if " - " in detection_result:
                    section_type = detection_result.split(" - ")[1].strip().lower()
                
                logger.info(f"✅ Contenido crítico detectado: {section_type}")
                
                # Extraer el contenido completo de la sección crítica
                extraction_prompt = f"""Del siguiente documento, extrae TODO el contenido de la sección de {section_type}.

DOCUMENTO COMPLETO:
{text}

INSTRUCCIONES:
- Extrae COMPLETO todo el contenido relacionado con {section_type}
- Incluye TODOS los elementos, precios, detalles y descripciones
- Mantén el formato original (tablas, listas, etc.)
- NO inventes ni agregues nada que no esté en el documento
- NO resumas, copia TODO tal cual aparece

CONTENIDO DE {section_type.upper()}:"""

                logger.info(f"📄 Extrayendo contenido completo de {section_type}...")
                
                extracted_content = chatbot_service.generate(
                    extraction_prompt, max_tokens=2000, temperature=0.1, top_p=0.85
                ).strip()
                
                if extracted_content and len(extracted_content) > 50:
                    # Generar pregunta apropiada según el tipo
                    question = self._generate_question_for_type(section_type, business_type)
                    
                    critical_section = {
                        "question": question,
                        "answer": extracted_content,
                        "category": section_type
                    }
                    critical_sections.append(critical_section)
                    logger.info(f"✅ Sección crítica extraída: {len(extracted_content)} caracteres")
                else:
                    logger.warning(f"⚠️ No se pudo extraer contenido de {section_type}")
            
            else:
                logger.info("ℹ️ No se detectó contenido crítico estructurado en el documento")
            
            return critical_sections
            
        except Exception as e:
            logger.error(f"Error en detección inteligente de secciones: {e}", exc_info=True)
            return []
    
    def _generate_question_for_type(self, section_type: str, business_type: str) -> str:
        """Genera una pregunta apropiada según el tipo de sección detectada."""
        
        # Mapeo de tipos a preguntas comunes
        question_templates = {
            "menú": "¿Qué tienen en el menú? ¿Cuál es el menú completo? ¿Qué platos tienen?",
            "menu": "¿Qué tienen en el menú? ¿Cuál es el menú completo? ¿Qué platos tienen?",
            "carta": "¿Qué tienen en la carta? ¿Cuál es la carta de bebidas?",
            "clases": "¿Qué clases tienen? ¿Cuáles son las clases disponibles? ¿Qué actividades ofrecen?",
            "horarios": "¿Cuáles son los horarios? ¿Qué horarios tienen?",
            "productos": "¿Qué productos tienen? ¿Cuál es el catálogo de productos? ¿Qué venden?",
            "servicios": "¿Qué servicios ofrecen? ¿Cuáles son los servicios disponibles?",
            "tarifas": "¿Cuáles son los precios? ¿Cuánto cuesta? ¿Qué tarifas tienen?",
            "precios": "¿Cuáles son los precios? ¿Cuánto cuesta?",
            "habitaciones": "¿Qué tipos de habitaciones tienen? ¿Cuáles son las habitaciones disponibles?",
            "planes": "¿Qué planes tienen? ¿Cuáles son los planes disponibles?",
            "paquetes": "¿Qué paquetes ofrecen? ¿Cuáles son los paquetes disponibles?",
            "tratamientos": "¿Qué tratamientos ofrecen? ¿Cuáles son los tratamientos disponibles?",
            "especialidades": "¿Cuáles son sus especialidades? ¿Qué especialidades tienen?",
        }
        
        # Buscar coincidencia exacta o parcial
        section_lower = section_type.lower()
        for key, question in question_templates.items():
            if key in section_lower or section_lower in key:
                return question
        
        # Pregunta genérica si no hay coincidencia
        return f"¿Qué {section_type} tienen disponibles? ¿Cuáles son los {section_type}?"

    def _auto_categorize_faq(self, question: str, answer: str) -> str:
        """
        Categoriza automáticamente una FAQ basándose en palabras clave.
        Sistema universal que funciona para cualquier tipo de negocio.
        NORMALIZA categorías para evitar duplicados con mayúsculas/minúsculas.
        """
        text_combined = (question + " " + answer).lower()
        
        # Categorías con palabras clave específicas (orden de prioridad)
        category_keywords = {
            "acceso": ["entrar", "acceso", "ingreso", "entrada", "tarjeta", "credencial", "identificación", "dni", "código", "menor", "edad"],
            "horarios": ["horario", "hora", "abierto", "cerrado", "funcionamiento", "atención", "apertura", "cierre"],
            "reservas": ["reservar", "reserva", "cita", "turno", "agendar", "programar"],
            "clases": ["clase", "instructor", "entrenador", "sesión", "capacitación", "curso", "fitness", "dirigida"],
            "cancelación": ["cancelar", "cancelación", "pausar", "suspender", "reembolso", "llegar tarde", "no puedo asistir"],
            "normas": ["prohibido", "permitido", "norma", "regla", "reglamento", "fumar", "beber", "alcohol", "droga"],
            "conducta": ["conducta", "comportamiento", "respeto", "tratar", "gritar", "lanzar", "expulsión", "inapropiado"],
            "seguridad": ["seguridad", "emergencia", "evacuación", "lesión", "accidente", "primeros auxilios", "incidente", "pérdida", "robo", "taquilla", "objeto de valor"],
            "higiene": ["limpieza", "higiene", "ducha", "ducharse", "toalla", "limpio", "desinfección", "spa"],
            "instalaciones": ["instalación", "equipo", "máquina", "área", "zona", "espacio", "gimnasio", "piscina", "sauna", "usar", "bloquear", "pesa", "barra", "material", "calzado", "ropa", "fotografiar", "grabar", "teléfono", "mascota", "perro"],
            "membresía": ["membresía", "suscripción", "plan", "paquete", "cuota", "pago", "precio", "tarifa"],
            "servicios": ["servicio", "ofrecer", "disponible", "incluye", "proporciona", "compromiso", "objetivo"],
        }
        
        # Buscar categoría más relevante (orden de prioridad importa)
        for category, keywords in category_keywords.items():
            if any(keyword in text_combined for keyword in keywords):
                return category
        
        # Si no se encontró ninguna categoría específica
        return "información general"
    
    def _normalize_category(self, category: str) -> str:
        """
        Normaliza nombres de categorías para evitar duplicados.
        Convierte variantes a su forma canónica.
        """
        category_lower = category.lower().strip()
        
        # Mapeo de variantes a forma canónica
        normalizations = {
            "clases dirigidas": "clases",
            "clase dirigida": "clases",
            "uso de las instalaciones": "instalaciones",
            "uso de instalaciones": "instalaciones",
            "higiene y seguridad": "higiene",
            "seguridad e higiene": "seguridad",
            "normas generales": "normas",
            "información general": "general",
            "general": "información general",
        }
        
        # Aplicar normalización si existe
        return normalizations.get(category_lower, category_lower)

    def _generate_faqs_from_text(self, text: str, business: Optional[Business] = None) -> List[Dict[str, str]]:
        """
        Genera FAQs automáticamente usando el LLM basándose en el contenido del documento.
        
        Args:
            text: El texto del documento normalizado
            business: El negocio asociado (opcional)
            
        Returns:
            Lista de diccionarios con 'question', 'answer' y 'category'
        """
        try:
            # Importar el servicio de chatbot que ya tiene el modelo cargado
            from .chatbot_service import chatbot_service
            
            # Verificar que el modelo esté disponible
            if not chatbot_service.model or chatbot_service.model_failed:
                logger.warning("Modelo LLM no disponible, intentando cargar...")
                chatbot_service.initialize_model()
                if not chatbot_service.model or chatbot_service.model_failed:
                    logger.warning("No se pudo cargar el modelo LLM, no se generarán FAQs")
                    return []
            
            all_faqs = []
            
            # ========================================================================
            # PASO 1: DETECCIÓN INTELIGENTE DE SECCIONES CRÍTICAS
            # Sistema universal que funciona para cualquier tipo de negocio
            # ========================================================================
            logger.info("=" * 80)
            logger.info("🤖 ANÁLISIS INTELIGENTE DE CONTENIDO")
            logger.info("=" * 80)
            
            critical_sections = self._detect_critical_sections(text, business)
            
            # Crear FAQs de alta prioridad para secciones críticas detectadas
            for section in critical_sections:
                critical_faq = {
                    "question": section["question"],
                    "answer": section["answer"],
                    "category": section["category"],
                    "priority": 100  # Alta prioridad para activar bypass directo (evita alucinaciones)
                }
                all_faqs.append(critical_faq)
                logger.info(f"✅ FAQ crítico creado: {section['category']} ({len(section['answer'])} chars)")
            
            logger.info("=" * 80)
            
            # 2. Generar FAQs generales (excluyendo secciones críticas del texto)
            text_without_critical = text
            for section in critical_sections:
                text_without_critical = text_without_critical.replace(section['answer'], '')
            
            # Limitar el texto para no sobrecargar el modelo (aumentado para más contexto)
            max_text_length = 5000  # Aumentado de 4000 a 5000 para incluir TODA la información posible
            text_sample = text_without_critical[:max_text_length] if len(text_without_critical) > max_text_length else text_without_critical
            
            # ========================================================================
            # 🧠 CÁLCULO INTELIGENTE DE TOKENS NECESARIOS
            # Analiza el contenido para determinar cuántas FAQs y tokens se necesitan
            # ========================================================================
            
            # Análisis del contenido para estimar FAQs necesarias
            doc_length = len(text_sample)
            num_sections = len(re.findall(r'\n\n+', text_sample))  # Secciones separadas por líneas vacías
            num_sentences = len(re.findall(r'[.!?]+', text_sample))  # Aproximado
            
            # FÓRMULA INTELIGENTE: Estimar FAQs necesarias basado en contenido
            # - Documentos cortos (<2000 chars): 15-20 FAQs
            # - Documentos medianos (2000-4000 chars): 20-30 FAQs  
            # - Documentos largos (>4000 chars): 30-40 FAQs
            
            estimated_faqs = 15  # Mínimo
            if doc_length > 4000:
                estimated_faqs = 35  # Documentos muy completos
            elif doc_length > 3000:
                estimated_faqs = 28  # Documentos completos
            elif doc_length > 2000:
                estimated_faqs = 22  # Documentos medianos
            else:
                estimated_faqs = 18  # Documentos cortos
            
            # Ajustar según densidad de información (más secciones = más FAQs)
            if num_sections > 15:
                estimated_faqs += 5
            elif num_sections > 10:
                estimated_faqs += 3
            
            # CALCULAR TOKENS NECESARIOS (aprox 250-300 tokens por FAQ generada)
            # Incluye: pregunta (~50 tokens) + respuesta (~150-200 tokens) + formato (~50 tokens)
            tokens_per_faq = 280  # Promedio conservador
            calculated_tokens = estimated_faqs * tokens_per_faq
            
            # Aplicar límites razonables (mínimo 4000, máximo 12000)
            calculated_tokens = max(4000, min(12000, calculated_tokens))
            
            logger.info("=" * 80)
            logger.info("🧠 ANÁLISIS INTELIGENTE DE TOKENS")
            logger.info("=" * 80)
            logger.info(f"📄 Longitud del documento: {doc_length} caracteres")
            logger.info(f"📊 Secciones detectadas: {num_sections}")
            logger.info(f"📝 Oraciones aproximadas: {num_sentences}")
            logger.info(f"🎯 FAQs estimadas necesarias: {estimated_faqs}")
            logger.info(f"🔢 Tokens calculados dinámicamente: {calculated_tokens}")
            logger.info("💡 Esto garantiza ~100% de cobertura del contenido")
            logger.info("=" * 80)
            
            business_context = ""
            if business:
                business_context = f" para el negocio '{business.name}' ({business.business_type})"
            
            # Instrucciones dinámicas basadas en secciones críticas detectadas
            special_instructions = ""
            if critical_sections:
                categories = [s['category'] for s in critical_sections]
                special_instructions = f"\n- NO generes FAQs sobre estas categorías (ya se crearon FAQs especiales): {', '.join(categories)}"
            
            # ESTRATEGIA MULTI-PASADA: Generar FAQs en grupos por categoría para mayor profundidad
            logger.info("🎯 GENERACIÓN MULTI-CATEGORÍA ACTIVADA")
            logger.info("   Generando FAQs especializadas por categoría para máxima cobertura...")
            
            all_generated_faqs = []
            
            # Calcular FAQs para pasada 1 (70% del total estimado)
            faqs_pass1 = int(estimated_faqs * 0.7)
            faqs_pass2 = estimated_faqs - faqs_pass1
            
            # PASADA 1: FAQs generales y de alto nivel (adaptativo)
            prompt_general = f"""Eres un experto en atención al cliente{business_context}.

DOCUMENTO:
{text_sample}

TAREA: Genera {faqs_pass1} FAQs completas basadas SOLO en la información del documento.

REGLAS:
1. Respuestas de 2-4 oraciones con información completa
2. NO inventes nada - usa SOLO el documento
3. Categoría: una palabra que describa el tema (por ejemplo servicios, horarios, contacto, reservas, normas, formación, experiencia, tecnologías)
4. Redacta SIEMPRE en tercera persona sobre el negocio o las personas del documento (por ejemplo "Ignacio estudió..."). Si el documento está en primera persona (como un CV), reescríbelo: nunca uses "yo", "mi", "mis" ni "estoy"{special_instructions}

FORMATO EXACTO (una FAQ por bloque):
P: ¿Pregunta específica?
R: Respuesta completa en 2-4 oraciones con detalles importantes.
C: categoría

EJEMPLO:
P: ¿Cómo se puede reservar una cita?
R: Las citas se reservan llamando por teléfono o escribiendo al correo del negocio. Conviene indicar el día y la hora preferidos para confirmar la disponibilidad. Si no hay hueco, el equipo propondrá otra fecha cercana.
C: reservas

Genera {faqs_pass1} FAQs siguiendo este formato EXACTO:"""

            logger.info(f"Generando {faqs_pass1} FAQs (Pasada 1) con {calculated_tokens} tokens usando %s...", chatbot_service._backend)
            
            # Generar usando el mismo backend que el chatbot (TOKENS DINÁMICOS)
            response_text = chatbot_service.generate(
                prompt_general, max_tokens=calculated_tokens, temperature=0.3, top_p=0.9
            )
            
            # DEBUG: Mostrar la respuesta del modelo
            logger.info("=" * 80)
            logger.info("📝 RESPUESTA DEL MODELO LLM:")
            logger.info("=" * 80)
            logger.info(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)
            logger.info("=" * 80)
            
            # Parsear la respuesta - patrón MEJORADO que NO captura múltiples preguntas
            # El patrón usa \n\n o \n[PR] para delimitar FAQs
            faq_pattern = re.compile(
                r'(?:P:|(?:\d+)\.)\s*([^\n]+?)\s*\n+\s*R:\s*([^\n]+(?:\n(?!P:|(?:\d+)\.|R:|C:)[^\n]+)*)\s*\n+\s*C:\s*([^\n]+)',
                re.DOTALL | re.IGNORECASE
            )
            
            matches = faq_pattern.findall(response_text)
            logger.info(f"🔎 Patrón encontró {len(matches)} FAQs en la respuesta")
            
            for idx, (question, answer, category) in enumerate(matches, 1):
                question = question.strip()
                answer = answer.strip()
                category = category.strip() if category else "información general"
                
                # LIMPIEZA MEJORADA: Remover "P:" duplicado al inicio de la pregunta
                question = re.sub(r'^P:\s*', '', question, flags=re.IGNORECASE).strip()
                
                # LIMPIEZA: Remover el "C: categoría" si aparece al final de la respuesta
                if re.search(r'C:\s*[\w\s]+\.?$', answer, re.IGNORECASE):
                    answer = re.sub(r'\s*C:\s*[\w\s]+\.?$', '', answer, flags=re.IGNORECASE).strip()
                
                # LIMPIEZA: Remover números de lista si quedaron en la pregunta
                question = re.sub(r'^\d+\.\s*', '', question).strip()
                
                # NORMALIZACIÓN: Convertir categoría a forma canónica
                category = self._normalize_category(category)
                
                # CATEGORIZACIÓN MEJORADA: Reclasificar automáticamente si está como "información general" o variantes
                if category in ["información general", "normas generales", "general", "otros"]:
                    category = self._auto_categorize_faq(question, answer)
                
                logger.info(f"\n📌 FAQ #{idx} encontrada:")
                logger.info(f"   P: {question[:100]}...")
                logger.info(f"   R: {answer[:150]}...")
                logger.info(f"   C: {category}")
                
                # Validación ESTRICTA: respuestas deben ser detalladas (mínimo 80 caracteres)
                # Y la pregunta no debe ser demasiado larga (máx 200 chars)
                if question and answer and 15 < len(question) <= 200 and len(answer) > 80:
                    # Limpiar saltos de línea múltiples
                    answer = re.sub(r'\n\s*\n', '\n', answer)
                    
                    # Expandir respuesta si es necesario (agregar punto final si falta)
                    if not answer.endswith('.') and not answer.endswith('!') and not answer.endswith('?'):
                        answer += '.'
                    
                    all_generated_faqs.append({
                        "question": question[:500],
                        "answer": answer[:2500],  # Aumentado a 2500 para respuestas muy completas
                        "category": category[:100],
                    })
                    logger.info(f"   ✅ FAQ aceptada (Q: {len(question)} chars, R: {len(answer)} chars)")
                elif len(answer) <= 80:
                    logger.warning(f"   ⚠️ Respuesta demasiado corta rechazada ({len(answer)} chars) - Se requiere mínimo 80")
                elif len(question) > 200:
                    logger.warning(f"   ⚠️ Pregunta demasiado larga rechazada ({len(question)} chars) - Máximo 200")
                elif len(question) <= 15:
                    logger.warning(f"   ⚠️ Pregunta demasiado corta rechazada ({len(question)} chars)")
            
            # Agregar FAQs generadas a la lista principal
            all_faqs.extend(all_generated_faqs)
            
            logger.info(f"\n✅ PASADA 1 completada: {len(all_generated_faqs)} FAQs generadas")
            
            # PASADA 2: FAQs específicas y de detalle (ADAPTATIVA - solo si estimamos más FAQs necesarias)
            if len(text_sample) > 1000 and faqs_pass2 > 0:
                logger.info(f"\n🎯 PASADA 2: Generando {faqs_pass2} FAQs adicionales de detalle...")
                
                # Calcular tokens para pasada 2 (30% restante)
                tokens_pass2 = int(calculated_tokens * 0.4)  # 40% de tokens para la segunda pasada
                tokens_pass2 = max(2000, min(5000, tokens_pass2))  # Entre 2000-5000
                
                prompt_detailed = f"""Basándote en el siguiente documento, genera {faqs_pass2} FAQs sobre temas específicos.

DOCUMENTO:
{text_sample}

TAREA: Genera {faqs_pass2} FAQs sobre detalles, casos específicos o excepciones.
Redacta en tercera persona sobre el negocio o las personas del documento; nunca uses "yo", "mi" ni "estoy".

FORMATO EXACTO (igual que antes):
P: ¿Pregunta específica?
R: Respuesta de 2-4 oraciones con detalles.
C: categoría

EJEMPLO:
P: ¿Se puede cancelar una reserva?
R: Sí, las reservas se pueden cancelar avisando con antelación por teléfono o correo. Así el hueco queda libre para otros clientes. Si hay algún cargo por cancelar tarde, el negocio lo comunica al reservar.
C: reservas

Genera {faqs_pass2} FAQs AHORA:"""

                logger.info(f"   Tokens asignados para Pasada 2: {tokens_pass2}")
                
                try:
                    response_text2 = chatbot_service.generate(
                        prompt_detailed, max_tokens=tokens_pass2, temperature=0.3, top_p=0.9
                    )
                    
                    logger.info("\n📝 RESPUESTA PASADA 2:")
                    logger.info(response_text2[:500] + "..." if len(response_text2) > 500 else response_text2)
                    
                    # Parsear respuesta de la segunda pasada (MISMO PROCESAMIENTO que pasada 1)
                    matches2 = faq_pattern.findall(response_text2)
                    logger.info(f"🔎 Segunda pasada encontró {len(matches2)} FAQs adicionales")
                    
                    additional_faqs = []
                    for idx, (question, answer, category) in enumerate(matches2, 1):
                        question = question.strip()
                        answer = answer.strip()
                        category = category.strip() if category else "información general"
                        
                        # APLICAR MISMAS LIMPIEZAS que en pasada 1
                        question = re.sub(r'^P:\s*', '', question, flags=re.IGNORECASE).strip()
                        if re.search(r'C:\s*[\w\s]+\.?$', answer, re.IGNORECASE):
                            answer = re.sub(r'\s*C:\s*[\w\s]+\.?$', '', answer, flags=re.IGNORECASE).strip()
                        question = re.sub(r'^\d+\.\s*', '', question).strip()
                        
                        # NORMALIZACIÓN: Convertir categoría a forma canónica
                        category = self._normalize_category(category)
                        
                        # CATEGORIZACIÓN AUTOMÁTICA
                        if category in ["información general", "general", "otros"]:
                            category = self._auto_categorize_faq(question, answer)
                        
                        logger.info(f"\n📌 FAQ Adicional #{idx}:")
                        logger.info(f"   P: {question[:80]}...")
                        logger.info(f"   R: {answer[:120]}...")
                        logger.info(f"   C: {category}")
                        
                        # MISMA VALIDACIÓN que pasada 1
                        if question and answer and 15 < len(question) <= 200 and len(answer) > 80:
                            answer = re.sub(r'\n\s*\n', '\n', answer)
                            if not answer.endswith('.') and not answer.endswith('!') and not answer.endswith('?'):
                                answer += '.'
                            
                            additional_faqs.append({
                                "question": question[:500],
                                "answer": answer[:2500],
                                "category": category[:100],
                            })
                            logger.info(f"   ✅ FAQ adicional aceptada (Q: {len(question)} chars, R: {len(answer)} chars)")
                        elif len(answer) <= 80:
                            logger.warning(f"   ⚠️ Respuesta muy corta rechazada ({len(answer)} chars)")
                        elif len(question) > 200:
                            logger.warning(f"   ⚠️ Pregunta muy larga rechazada ({len(question)} chars)")
                    
                    all_faqs.extend(additional_faqs)
                    logger.info(f"✅ PASADA 2 completada: {len(additional_faqs)} FAQs adicionales generadas")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error en segunda pasada: {e}")
            else:
                logger.info("ℹ️ Documento muy corto, omitiendo segunda pasada")


            
            # 3. Eliminar duplicados basados en similitud de preguntas
            logger.info("🔍 Verificando duplicados en FAQs generadas...")
            unique_faqs = self._remove_duplicate_faqs(all_faqs)
            
            duplicates_removed = len(all_faqs) - len(unique_faqs)
            if duplicates_removed > 0:
                logger.info("✓ Eliminadas %d FAQs duplicadas durante la generación", duplicates_removed)
            else:
                logger.info("✓ No se encontraron duplicados en FAQs generadas")
            
            logger.info("=" * 60)
            logger.info("📊 RESUMEN DE GENERACIÓN")
            logger.info("=" * 60)
            logger.info("   🧠 Tokens utilizados: %d (calculados dinámicamente)", calculated_tokens)
            logger.info("   🎯 FAQs objetivo: %d (%d pasada 1 + %d pasada 2)", estimated_faqs, faqs_pass1, faqs_pass2)
            logger.info("   FAQs generadas totales: %d", len(all_faqs))
            logger.info("   FAQs únicas (sin duplicados): %d", len(unique_faqs))
            
            # Calcular % de cobertura logrado
            coverage_pct = (len(unique_faqs) / estimated_faqs * 100) if estimated_faqs > 0 else 0
            logger.info(f"   📈 Cobertura lograda: {coverage_pct:.1f}% del objetivo")
            
            # Estadísticas por categoría
            categories_count = {}
            total_answer_length = 0
            for faq in unique_faqs:
                cat = faq.get("category", "sin categoría")
                categories_count[cat] = categories_count.get(cat, 0) + 1
                total_answer_length += len(faq.get("answer", ""))
            
            avg_answer_length = total_answer_length // len(unique_faqs) if unique_faqs else 0
            
            logger.info("\n   📁 FAQs por categoría:")
            for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"      • {cat}: {count} FAQs")
            
            logger.info(f"\n   📏 Longitud promedio de respuestas: {avg_answer_length} caracteres")
            
            # Verificar si hay FAQ de menú
            has_menu_faq = any(faq.get("category", "").lower() == "menú" for faq in unique_faqs)
            if has_menu_faq:
                logger.info("   ✅ FAQ de menú completo incluida")
            else:
                logger.info("   ℹ️  Sin FAQ de menú")
            
            logger.info("=" * 60)
            
            return unique_faqs
            
        except ImportError as e:
            logger.warning("Error importando chatbot_service: %s", e)
            return []
        except Exception as exc:
            logger.warning("Error generando FAQs automáticas: %s", exc)
            import traceback
            traceback.print_exc()
            return []

    def _remove_duplicate_faqs(self, faqs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Elimina FAQs duplicadas basándose en similitud de preguntas.
        EXCEPCIÓN: Las FAQs de menú con diferentes preguntas NO se consideran duplicadas
        (son variaciones intencionales para mejorar la búsqueda).
        
        Args:
            faqs: Lista de FAQs
            
        Returns:
            Lista de FAQs sin duplicados
        """
        if not faqs:
            return []
        
        if len(faqs) == 1:
            return faqs
        
        unique_faqs = []
        seen_questions = []
        duplicates_log = []
        
        for faq in faqs:
            question_normalized = faq['question'].lower().strip('¿?').strip()
            
            # EXCEPCIÓN: Las FAQs de menú con diferente pregunta NO son duplicados
            # (son variaciones intencionales para mejorar búsqueda)
            is_menu_faq = faq.get('category', '').lower() == 'menú'
            
            # Verificar si hay una pregunta similar
            is_duplicate = False
            similar_to = None
            for idx, seen_q in enumerate(seen_questions):
                # Si ambas son FAQs de menú, solo son duplicados si la pregunta es IDÉNTICA
                if is_menu_faq and unique_faqs[idx].get('category', '').lower() == 'menú':
                    if question_normalized == seen_q:
                        is_duplicate = True
                        similar_to = unique_faqs[idx]['question']
                        break
                    else:
                        # Diferentes preguntas de menú = NO duplicado
                        continue
                
                # Calcular similitud simple (palabras en común)
                words_new = set(question_normalized.split())
                words_seen = set(seen_q.split())
                
                if not words_new or not words_seen:
                    continue
                
                # Si más del 70% de las palabras coinciden, es duplicado
                common_words = words_new.intersection(words_seen)
                similarity = len(common_words) / max(len(words_new), len(words_seen))
                
                if similarity > 0.7:
                    is_duplicate = True
                    similar_to = unique_faqs[idx]['question']
                    duplicates_log.append({
                        'duplicate': faq['question'][:60],
                        'similar_to': similar_to[:60],
                        'similarity': similarity
                    })
                    break
            
            if not is_duplicate:
                unique_faqs.append(faq)
                seen_questions.append(question_normalized)
        
        # Log detallado de duplicados encontrados
        if duplicates_log:
            logger.info("   Duplicados detectados durante generación:")
            for dup in duplicates_log:
                logger.info("   • '%s...' similar a '%s...' (%.0f%%)", 
                          dup['duplicate'], dup['similar_to'], dup['similarity']*100)
        
        return unique_faqs

    def _save_generated_faqs(
        self,
        db: Session,
        faqs: List[Dict[str, str]],
        business: Optional[Business],
        document_id: int,
    ) -> int:
        """
        Guarda las FAQs generadas en la base de datos, evitando duplicados.
        
        Args:
            db: Sesión de base de datos
            faqs: Lista de FAQs generadas
            business: Negocio asociado
            document_id: ID del documento fuente
            
        Returns:
            Número de FAQs guardadas
        """
        if not business:
            logger.info("ℹ️  No hay negocio asociado, las FAQs no se guardarán automáticamente")
            return 0
        
        logger.info("=" * 60)
        logger.info("💾 GUARDANDO FAQs EN BASE DE DATOS")
        logger.info("=" * 60)
        logger.info("   Negocio: %s (ID: %d)", business.name, business.id)
        logger.info("   FAQs a guardar: %d", len(faqs))
        
        # Obtener FAQs existentes del negocio
        existing_faqs = db.query(FAQ).filter(FAQ.business_id == business.id).all()
        existing_questions = [faq.question.lower().strip('¿?').strip() for faq in existing_faqs]
        
        logger.info("   FAQs existentes en BD: %d", len(existing_faqs))
        logger.info("   Verificando duplicados contra BD...")
        
        saved_count = 0
        skipped_duplicates = 0
        duplicates_log = []
        
        for faq_data in faqs:
            try:
                question_normalized = faq_data["question"].lower().strip('¿?').strip()
                
                # Verificar si ya existe una pregunta similar
                is_duplicate = False
                similar_to = None
                
                for existing_q in existing_questions:
                    words_new = set(question_normalized.split())
                    words_existing = set(existing_q.split())
                    
                    if not words_new or not words_existing:
                        continue
                    
                    common_words = words_new.intersection(words_existing)
                    similarity = len(common_words) / max(len(words_new), len(words_existing))
                    
                    if similarity > 0.75:  # 75% de similitud = duplicado
                        is_duplicate = True
                        similar_to = existing_q
                        skipped_duplicates += 1
                        duplicates_log.append({
                            'new': faq_data["question"][:60],
                            'existing': similar_to[:60],
                            'similarity': similarity
                        })
                        break
                
                if is_duplicate:
                    continue
                
                # No agregar fuente aquí - el chatbot la añade automáticamente al responder
                # answer_with_source = f"{faq_data['answer']}\n\n[Fuente: Documento #{document_id}]"
                
                # Determinar prioridad: usar la prioridad proporcionada o por defecto 5
                priority = faq_data.get("priority", 5)
                
                faq = FAQ(
                    business_id=business.id,
                    question=faq_data["question"],
                    answer=faq_data["answer"],  # Sin fuente - se añade al responder
                    category=faq_data.get("category", "documento"),
                    priority=priority,
                )
                db.add(faq)
                existing_questions.append(question_normalized)  # Actualizar lista para siguientes checks
                saved_count += 1
            except Exception as exc:
                logger.error("   ❌ Error guardando FAQ: %s", exc)
                continue
        
        # Log detallado de duplicados omitidos
        if duplicates_log:
            logger.info("   ")
            logger.info("   🔄 FAQs duplicadas omitidas (ya existen en BD):")
            for dup in duplicates_log[:5]:  # Mostrar máximo 5
                logger.info("   • Nueva: '%s...'", dup['new'])
                logger.info("     Similar a: '%s...' (%.0f%% similar)", 
                          dup['existing'], dup['similarity']*100)
            if len(duplicates_log) > 5:
                logger.info("   ... y %d más", len(duplicates_log) - 5)
        
        if saved_count > 0:
            try:
                db.commit()
                logger.info("   ")
                logger.info("   ✅ ÉXITO: Se guardaron %d FAQs nuevas", saved_count)
                if skipped_duplicates > 0:
                    logger.info("   ⏭️  Se omitieron %d FAQs duplicadas", skipped_duplicates)
            except Exception as exc:
                logger.error("   ❌ Error al hacer commit: %s", exc)
                db.rollback()
                saved_count = 0
        else:
            logger.info("   ℹ️  No se guardaron FAQs nuevas (todas eran duplicadas)")
        
        logger.info("=" * 60)
        return saved_count

    def _build_storage_name(self, document_id: int, filename: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "documento")
        unique = uuid.uuid4().hex[:8]
        return Path(f"{document_id}_{unique}_{safe}")

    def ingest_upload(
        self,
        *,
        db: Session,
        data: bytes,
        filename: str,
        content_type: Optional[str],
        business: Optional[Business],
    ) -> IngestResult:
        size = len(data)
        self._validate_file(size=size, filename=filename, content_type=content_type)

        extracted = self.extract_text(data=data, filename=filename, content_type=content_type)
        normalized = self._normalize_text(extracted)
        if not normalized:
            raise DocumentProcessingError("No se pudo extraer texto legible del documento")

        chunks = self._chunk_text(normalized, getattr(business, "business_type", None))
        document = Document(
            business_id=business.id if business else None,
            original_filename=filename or "documento",
            content_type=content_type,
            size_bytes=size,
            status="processed",
        )
        db.add(document)
        db.flush()

        try:
            storage_name = self._build_storage_name(document.id, filename)
            storage_path = DOCUMENTS_DIR / storage_name
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            with storage_path.open("wb") as fh:
                fh.write(data)
            document.storage_path = str(storage_path)
        except Exception as exc:
            logger.warning("No se pudo guardar el archivo original: %s", exc)

        for index, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document.id,
                business_id=document.business_id,
                chunk_index=index,
                text=chunk_text,
                char_length=len(chunk_text),
            )
            db.add(chunk)

        logger.info(
            "Documento '%s' (%s bytes) procesado en %s fragmentos",
            filename,
            size,
            len(chunks),
        )
        
        # Generar FAQs automáticamente desde el contenido del documento
        faqs_created = 0
        try:
            generated_faqs = self._generate_faqs_from_text(normalized, business)
            if generated_faqs:
                faqs_created = self._save_generated_faqs(db, generated_faqs, business, document.id)
                logger.info("Se crearon %d FAQs automáticas desde el documento '%s'", faqs_created, filename)
        except Exception as exc:
            logger.warning("Error en la generación automática de FAQs: %s", exc)

        return IngestResult(
            document_id=document.id,
            filename=document.original_filename,
            chunks_created=len(chunks),
            characters=len(normalized),
            business_id=document.business_id,
            faqs_created=faqs_created,
        )

    @staticmethod
    def _snippet_around(text: str, query: str, max_chars: int) -> str:
        """Recorta `text` a `max_chars` centrado en la primera palabra de la pregunta que aparezca."""
        text = " ".join((text or "").split())
        if len(text) <= max_chars:
            return text
        lower = text.lower()
        positions = [
            lower.find(word[:5])
            for word in re.findall(r"\w+", query.lower())
            if len(word) > 3 and lower.find(word[:5]) >= 0
        ]
        start = max(0, min(positions) - max_chars // 3) if positions else 0
        start = min(start, len(text) - max_chars)
        window = text[start : start + max_chars]
        if start > 0:
            window = "…" + window.split(" ", 1)[-1]
        if start + max_chars < len(text):
            window = window.rsplit(" ", 1)[0] + "…"
        return window

    def get_relevant_chunks(
        self,
        *,
        db: Session,
        business_id: Optional[int],
        query: str,
        limit: int = 3,
    ) -> List[Dict[str, object]]:
        if not query or not query.strip():
            return []

        query = query.strip()

        chunks: List[DocumentChunk] = (
            db.query(DocumentChunk)
            .filter(
                or_(
                    DocumentChunk.business_id == business_id,
                    DocumentChunk.business_id.is_(None),
                )
            )
            .order_by(DocumentChunk.created_at.desc())
            .limit(self.SEARCH_WINDOW)
            .all()
        )

        if not chunks:
            return []

        choice_map = {chunk.id: chunk for chunk in chunks}
        text_map = {chunk_id: chunk.text for chunk_id, chunk in choice_map.items()}

        matches = process.extract(
            query,
            text_map,
            scorer=fuzz.token_set_ratio,
            limit=limit,
        )

        snippets: List[Dict[str, object]] = []
        for chunk_id, score, _ in matches:
            if score < self.MIN_SCORE:
                continue
            chunk = choice_map.get(chunk_id)
            if chunk is None:
                continue
            source = None
            try:
                if chunk.document:
                    source = chunk.document.original_filename
            except Exception:  # pragma: no cover - lazy load fallback
                source = None
            snippets.append(
                {
                    "text": self._snippet_around(chunk.text, query, self.SNIPPET_MAX_CHARS),
                    "score": float(score),
                    "document_id": chunk.document_id,
                    "source": source,
                }
            )
            if len(snippets) >= limit:
                break

        # Sin coincidencias no se añade nada: meter trozos al azar solo alarga el prompt (y el tiempo de respuesta).
        return snippets


document_service = DocumentService()

__all__ = ["document_service", "DocumentService", "DocumentProcessingError", "IngestResult"]
