"""Chat interactions with the language model."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ...database import SessionLocal
from ...models import Business, Conversation, FAQ
from ...schemas import ChatMessage, ChatResponse
from ..dependencies import get_db
from ...services.chatbot_service import chatbot_service
from ...services.document_service import document_service

router = APIRouter(tags=["chat"])
logger = logging.getLogger("chatbot")

CRITICAL_FAQ_MIN_PRIORITY = 100  # FAQs con prioridad >= 100 se devuelven tal cual, sin LLM
FUZZY_MATCH_THRESHOLD = 0.85  # similitud mínima (palabras clave) pregunta/FAQ para responder sin LLM
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
    """FAQ que pregunta lo mismo que el mensaje (mismas palabras clave, tolerando erratas), para responder sin LLM.

    Se comparan solo las palabras con contenido: "¿Qué estudios tiene?" no debe casar con "¿Qué certificaciones tiene?".
    """
    query_words = " ".join(sorted(set(chatbot_service.content_words(text))))
    if not query_words:
        return None
    best, best_ratio = None, 0.0
    for faq in faqs:
        question_words = " ".join(sorted(set(chatbot_service.content_words(faq.question))))
        if not question_words:
            continue
        ratio = fuzz.ratio(query_words, question_words) / 100
        if ratio > best_ratio:
            best, best_ratio = faq, ratio
    return best if best_ratio >= FUZZY_MATCH_THRESHOLD else None


@dataclass
class _Prepared:
    """Resultado de preparar un mensaje: o ya hay respuesta (sin LLM) o hay que generarla con el modelo."""

    answer: Optional[str] = None  # respuesta directa (FAQ, aviso...)
    save: bool = True  # guardar la conversación
    delay: bool = False  # aplicar la pausa natural
    context: str = ""
    kwargs: dict = field(default_factory=dict)  # argumentos para chatbot_service.plan_response
    phone: str = "el negocio"


TIMEOUT_MESSAGE = (
    "Lo siento, estoy tardando demasiado al generar la respuesta. Por favor inténtalo de nuevo o contacta con {phone}."
)
ERROR_MESSAGE = "Lo siento, estamos teniendo problemas técnicos. Por favor contacta con {phone}."


def _prepare_chat(message: ChatMessage, db: Session) -> _Prepared:
    """Pasos comunes de /chat y /chat/stream: negocio, FAQs directas, contexto y ajuste a la ventana del modelo."""
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
            return _Prepared(answer=answer, delay=True)

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
        return _Prepared(answer=(matched_faq.answer or "").strip())

    # 4) Hace falta el modelo
    notice = chatbot_service.ensure_ready()
    if notice:
        return _Prepared(answer=notice, save=False)

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
            query=message.message,
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
        limit=chatbot_service.max_doc_snippets,
    )
    if document_snippets:
        context += "\n\nINFORMACIÓN ADICIONAL (Documentos cargados):\n"
        for snippet in document_snippets:
            source_label = snippet.get("source") or "Documento"
            context += f"- {source_label}: {snippet.get('text', '')}\n"

    if chatbot_service.is_recommendation_request(message.message):
        context += RECOMMENDATION_INSTRUCTION

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

    return _Prepared(
        context=context,
        phone=business.phone or "el negocio",
        kwargs=dict(
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
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    prep = _prepare_chat(message, db)
    if prep.answer is not None:
        if prep.save:
            _save_conversation(db, message, prep.answer)
        if prep.delay:
            await _natural_delay()
        return ChatResponse(response=prep.answer, timestamp=datetime.utcnow())

    # Generar (en un hilo, para no bloquear el event loop)
    loop = asyncio.get_running_loop()
    try:
        bot_response = await asyncio.wait_for(
            loop.run_in_executor(
                None, lambda: chatbot_service.get_response(message.message, prep.context, **prep.kwargs)
            ),
            timeout=chatbot_service.generate_timeout + 5,
        )
    except asyncio.TimeoutError:
        bot_response = TIMEOUT_MESSAGE.format(phone=prep.phone)
    except Exception:
        logger.exception("Error generando la respuesta")
        bot_response = ERROR_MESSAGE.format(phone=prep.phone)

    _save_conversation(db, message, bot_response)
    await _natural_delay()
    return ChatResponse(response=bot_response, timestamp=datetime.utcnow())


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _save_conversation_new_session(message: ChatMessage, bot_response: str) -> None:
    """La sesión de la petición puede estar cerrada cuando termina el streaming: se usa una propia."""
    db = SessionLocal()
    try:
        _save_conversation(db, message, bot_response)
    finally:
        db.close()


@router.post("/chat/stream")
async def chat_stream(message: ChatMessage, db: Session = Depends(get_db)):
    """Igual que /chat pero en Server-Sent Events: `{"delta": "..."}` por trozo y `{"final": "...", "done": true}` al terminar.

    `final` es el texto limpio definitivo (el cliente debe sustituir con él lo que haya ido pintando).
    """
    prep = _prepare_chat(message, db)
    plan = None
    if prep.answer is None:
        plan = chatbot_service.plan_response(message.message, prep.context, **prep.kwargs)
        if isinstance(plan, str):  # saludo o servicio no disponible: no hace falta generar
            prep, plan = _Prepared(answer=plan), None
        else:
            cached = chatbot_service.cached_reply(plan)
            if cached is not None:
                prep, plan = _Prepared(answer=cached), None

    async def events():
        if plan is None:
            if prep.save:
                _save_conversation_new_session(message, prep.answer)
            yield _sse({"final": prep.answer, "done": True})
            return

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()

        def pump() -> None:  # hilo que genera y va pasando los trozos al event loop
            try:
                for piece in chatbot_service.generate_chat_stream(
                    plan.system,
                    plan.user,
                    max_tokens=plan.max_tokens,
                    temperature=plan.temperature,
                    top_p=plan.top_p,
                    should_stop=stop.is_set,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, ("delta", piece))
            except Exception:
                logger.exception("Error generando la respuesta (streaming)")
                loop.call_soon_threadsafe(queue.put_nowait, ("error", ""))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("end", ""))

        loop.run_in_executor(None, pump)
        deadline = loop.time() + chatbot_service.generate_timeout + 5
        parts: List[str] = []
        failure: Optional[str] = None
        try:
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise asyncio.TimeoutError
                kind, value = await asyncio.wait_for(queue.get(), timeout=remaining)
                if kind == "delta":
                    parts.append(value)
                    yield _sse({"delta": value})
                else:
                    failure = ERROR_MESSAGE if kind == "error" else None
                    break
        except asyncio.TimeoutError:
            failure = TIMEOUT_MESSAGE
        finally:
            stop.set()  # corta la generación si el cliente se fue o se agotó el tiempo

        final = chatbot_service._clean_response("".join(parts), plan.wants_menu)
        if final and failure is None:
            chatbot_service.store_reply(plan, final)
        if not final:
            final = (failure or ERROR_MESSAGE).format(phone=prep.phone)
        _save_conversation_new_session(message, final)
        yield _sse({"final": final, "done": True})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
