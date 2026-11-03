"""Chat interactions with the language model."""
from __future__ import annotations

import asyncio
import difflib
import logging
import random
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...models import Business, Conversation, FAQ
from ...schemas import ChatMessage, ChatResponse
from ..dependencies import get_db
from ...services.chatbot_service import chatbot_service
from ...services.document_service import document_service

router = APIRouter(tags=["chat"])
logger = logging.getLogger("chatbot")

CRITICAL_FAQ_MIN_PRIORITY = 100  # FAQs con prioridad >= 100 se devuelven tal cual, sin LLM
FUZZY_MATCH_THRESHOLD = 0.70  # similitud mínima pregunta/FAQ para responder sin LLM
ALL_RULES_MAX_FAQS = 50

ALL_RULES_PHRASES = (
    "las normas", "todas las normas", "qué normas", "cuáles son las normas",
    "las reglas", "todas las reglas", "qué reglas", "cuáles son las reglas",
    "normativa", "reglamento", "dime las normas", "cuales normas",
    "normas del gimnasio", "reglas del gimnasio",
)
RELEVANCE_KEYWORDS = (
    "norma", "regla", "prohibido", "permitido", "horario", "precio",
    "servicio", "clase", "reserva", "instalación", "equipamiento",
    "acceso", "entrada", "tarjeta", "fumar", "alcohol", "comida",
    "bebida", "gimnasio", "spa", "piscina", "ducha", "taquilla",
)

RECOMMENDATION_INSTRUCTION = (
    "\nEl cliente está pidiendo una recomendación concreta. Usa la información del negocio y las FAQs para sugerir como máximo dos opciones específicas (platos, servicios o planes), explica brevemente por qué encajan con lo que pide y ofrece una alternativa opcional si aplica."
)

EXTRA_INSTRUCTIONS = """
INSTRUCCIONES ADICIONALES:
- Responde con calidez, cercanía y profesionalidad; puedes abrir con un saludo breve y algún emoji si encaja con la marca.
- Entrega la información solicitada y, si aporta valor, añade un matiz extra o un ejemplo corto.
- Usa frases naturales; si lo ves útil, incluye una lista corta (máximo 3 puntos) para elementos clave.
- Añade como máximo una pregunta amable orientada a ofrecer más ayuda (por ejemplo, si desea más detalles); nunca pidas al usuario información que correspondería al negocio.
- No repitas la pregunta del usuario ni añadas múltiples preguntas.
- No incluyas roles como 'cliente' o 'asistente' en la respuesta.
- Si no sabes la respuesta, sugiere amablemente contactar con el negocio.
- Si el usuario da las gracias o se despide, responde de forma amable y personalizada.
"""


def _save_conversation(db: Session, message: ChatMessage, bot_response: str) -> None:
    try:
        db.add(
            Conversation(
                business_id=message.business_id,
                session_id=message.session_id,
                user_message=message.message,
                bot_response=bot_response,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("No se pudo guardar la conversación")


async def _natural_delay() -> None:
    """Pausa breve para simular 'pensamiento'. Es asíncrona: no bloquea el servidor."""
    await asyncio.sleep(random.uniform(1.0, 1.5))


def _critical_faq_answer(faqs: List[FAQ], critical: dict) -> Optional[str]:
    """Respuesta directa desde la FAQ prioritaria que encaje con el tipo de consulta crítica."""
    candidates = [
        f
        for f in faqs
        if (f.priority or 0) >= CRITICAL_FAQ_MIN_PRIORITY
        and any(
            kw in f.question.lower() or kw in (f.category or "").lower()
            for kw in critical["keywords"]
        )
    ]
    if not candidates:
        return None

    best = max(candidates, key=lambda f: f.priority)
    logger.info("✅ Consulta crítica '%s': FAQ %s directa, sin pasar por LLM", critical["type"], best.id)

    # Quitar referencia a fuente antigua (evita duplicados)
    text = re.sub(r"\n*\s*\[Fuente:.*?\]\s*$", "", best.answer, flags=re.IGNORECASE)
    if not text.startswith("¡") and not text.startswith("Hola"):
        text = f"¡Hola! {critical.get('emoji', '📋')} Con mucho gusto te muestro la información:\n\n{text}"
    return text


def _best_faq_match(faqs: List[FAQ], text: str) -> Optional[FAQ]:
    """FAQ cuya pregunta se parece lo bastante al mensaje como para responder sin LLM."""
    text = text.lower()
    best, best_ratio = None, 0.0
    for faq in faqs:
        question = (faq.question or "").strip()
        if not question:
            continue
        ratio = difflib.SequenceMatcher(None, text, question.lower()).ratio()
        if ratio > best_ratio:
            best, best_ratio = faq, ratio
    return best if best_ratio >= FUZZY_MATCH_THRESHOLD else None


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == message.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    faqs = db.query(FAQ).filter(FAQ.business_id == message.business_id).all()

    # 1) Información crítica (menú, clases, precios...): FAQ prioritaria directa, sin LLM
    #    para evitar alucinaciones.
    critical = chatbot_service.is_critical_info_request(message.message)
    if critical:
        answer = _critical_faq_answer(faqs, critical)
        if answer:
            _save_conversation(db, message, answer)
            await _natural_delay()
            return ChatResponse(response=answer, timestamp=datetime.utcnow())

    # 2) Quedarse solo con las FAQs relevantes para no confundir al modelo
    message_lower = message.message.lower()
    wants_all_rules = any(phrase in message_lower for phrase in ALL_RULES_PHRASES)
    keywords = [word for word in RELEVANCE_KEYWORDS if word in message_lower]
    if keywords:
        relevant_faqs = [
            faq
            for faq in faqs
            if any(
                kw in (faq.question + " " + faq.answer + " " + (faq.category or "")).lower()
                for kw in keywords
            )
        ]
        if relevant_faqs:
            faqs = relevant_faqs

    # 3) Pregunta casi idéntica a una FAQ: responder sin LLM ni construir contexto
    matched_faq = _best_faq_match(faqs, message.message)
    if matched_faq:
        answer = (matched_faq.answer or "").strip()
        _save_conversation(db, message, answer)
        return ChatResponse(response=answer, timestamp=datetime.utcnow())

    # 4) Hace falta el modelo
    notice = chatbot_service.ensure_ready()
    if notice:
        return ChatResponse(response=notice, timestamp=datetime.utcnow())

    # 5) Construir contexto
    if wants_all_rules:
        max_faqs = ALL_RULES_MAX_FAQS
        num_faqs_for_context = len(faqs)  # número real de FAQs, para el cálculo de tokens
    else:
        max_faqs = chatbot_service.max_faqs
        num_faqs_for_context = min(len(faqs), max_faqs)

    is_critical_request = critical is not None

    def build(max_faqs_: int) -> str:
        return chatbot_service.build_context(
            business,
            faqs,
            max_faqs=max_faqs_,
            include_default_instructions=not is_critical_request,
            menu_focus=is_critical_request,
        )

    context = build(max_faqs)

    try:
        history_entries = (
            db.query(Conversation)
            .filter(
                Conversation.business_id == message.business_id,
                Conversation.session_id == message.session_id,
            )
            .order_by(Conversation.timestamp.desc())
            .limit(chatbot_service.max_history_turns)
            .all()
        )
        history_entries = list(reversed(history_entries))
    except Exception:
        history_entries = []

    history_text = chatbot_service.format_history(history_entries)
    if history_text:
        context += "\n\nHISTORIAL RECIENTE:\n" + history_text + "\n"

    customer_name = chatbot_service.extract_customer_name(history_entries, message.message)
    name_already_used = False
    if customer_name:
        name_lower = customer_name.lower()
        name_already_used = any(
            entry.bot_response and name_lower in entry.bot_response.lower()
            for entry in history_entries
        )
        context += f"\nNombre del cliente: {customer_name}\n"
        if name_already_used:
            context += "Ya usaste el nombre del cliente anteriormente; evita repetirlo salvo que sea imprescindible.\n"
        else:
            context += "Puedes mencionar el nombre del cliente una única vez en esta respuesta para sonar cercano.\n"

    conversation_started = len(history_entries) > 0
    if conversation_started:
        context += "\n\nCONVERSACIÓN EN CURSO: Ya saludaste al cliente; evita repetir el saludo inicial y responde directamente.\n"
    else:
        context += "\n\nCONVERSACIÓN INICIAL: Saluda cordialmente al cliente al comienzo.\n"
    if customer_name and not name_already_used:
        context += "Recuerda usar el nombre del cliente solo una vez en la respuesta para mantener naturalidad.\n"

    document_snippets = document_service.get_relevant_chunks(
        db=db,
        business_id=business.id,
        query=message.message,
        limit=3,
    )
    if document_snippets:
        context += "\n\nINFORMACIÓN ADICIONAL (Documentos cargados):\n"
        for snippet in document_snippets:
            source_label = snippet.get("source") or "Documento"
            context += f"- {source_label}: {snippet.get('text', '')}\n"

    if chatbot_service.is_recommendation_request(message.message):
        context += RECOMMENDATION_INSTRUCTION

    context += EXTRA_INSTRUCTIONS

    # 6) Ajustar el contexto a la ventana del modelo
    ratio = chatbot_service.context_token_ratio
    allowed = chatbot_service.context_window - chatbot_service.reserve_response_tokens
    approx_tokens = max(1, len(context + message.message) // ratio)
    while approx_tokens > allowed and max_faqs > 1:
        max_faqs = max(1, max_faqs // 2)
        context = build(max_faqs)
        approx_tokens = max(1, len(context + message.message) // ratio)

    if approx_tokens > allowed:
        max_chars = allowed * ratio
        full = context + f"\n\n{message.message}\n"
        tail = full[-(max_chars // 2):]
        head = full[: max(0, max_chars - len(tail))]
        context = head + tail

    # 7) Generar (en un hilo, para no bloquear el event loop)
    phone = business.phone or "el negocio"
    loop = asyncio.get_running_loop()
    try:
        bot_response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: chatbot_service.get_response(
                    message.message,
                    context,
                    temperature=business.generation_temperature,
                    top_p=business.generation_top_p,
                    welcome_message=None if conversation_started else business.welcome_message,
                    suppress_greeting=conversation_started,
                    customer_name=customer_name,
                    name_already_used=name_already_used,
                    db=db,
                    business=business,
                    wants_all_rules=wants_all_rules,
                    wants_menu=is_critical_request and critical["type"] == "menú",
                    num_faqs_in_context=num_faqs_for_context,
                ),
            ),
            timeout=chatbot_service.generate_timeout + 5,
        )
    except asyncio.TimeoutError:
        bot_response = (
            "Lo siento, estoy tardando demasiado al generar la respuesta. Por favor inténtalo de nuevo o contacta con "
            f"{phone}."
        )
    except Exception:
        logger.exception("Error generando la respuesta")
        bot_response = (
            "Lo siento, estamos teniendo problemas técnicos. Por favor contacta con "
            f"{phone}."
        )

    _save_conversation(db, message, bot_response)
    await _natural_delay()
    return ChatResponse(response=bot_response, timestamp=datetime.utcnow())


@router.get("/conversations/{business_id}")
def get_conversations(business_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.business_id == business_id)
        .order_by(Conversation.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "user_message": c.user_message,
            "bot_response": c.bot_response,
            "timestamp": c.timestamp,
        }
        for c in conversations
    ]
