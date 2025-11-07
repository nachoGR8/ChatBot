"""Chat interactions with the language model."""
from __future__ import annotations

import asyncio
import difflib
import logging
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...models import Business, Conversation, FAQ
from ...schemas import ChatMessage, ChatResponse
from ..dependencies import get_db
from ...services.chatbot_service import chatbot_service
from ...services.document_service import document_service

router = APIRouter(tags=["chat"])
logger = logging.getLogger("chatbot")


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == message.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    faqs = db.query(FAQ).filter(FAQ.business_id == message.business_id).all()
    logger.info(f"📊 ENDPOINT: Total FAQs cargados for business_id={message.business_id}: {len(faqs)}")
    
    # ============================================================================
    # SISTEMA INTELIGENTE DE BYPASS DIRECTO (Universal para cualquier negocio)
    # ============================================================================
    # Detectar si el usuario está pidiendo información crítica (menú, clases, productos, servicios, etc.)
    # y responder directamente desde FAQs de alta prioridad para evitar alucinaciones del LLM
    # ============================================================================
    
    critical_request_detected = chatbot_service.is_critical_info_request(message.message)
    
    if critical_request_detected:
        logger.info(f"🔍 Detectada consulta de información crítica: '{message.message}'")
        logger.info(f"🔍 Tipo detectado: {critical_request_detected['type']}")
        logger.info(f"🔍 Total FAQs disponibles: {len(faqs)}")
        
        # Buscar FAQs de alta prioridad que coincidan con el tipo detectado
        critical_faqs = [
            f for f in faqs 
            if f.priority >= 100 and any(
                keyword in f.question.lower() or keyword in (f.category or "").lower()
                for keyword in critical_request_detected['keywords']
            )
        ]
        
        logger.info(f"🔍 FAQs críticos filtrados (prioridad >= 100): {len(critical_faqs)}")
        if critical_faqs:
            for faq in critical_faqs[:3]:  # Mostrar primeros 3
                logger.info(f"   - FAQ {faq.id} (prioridad {faq.priority}): {faq.question[:50]}...")
        
        if critical_faqs:
            # Ordenar por prioridad y tomar el primero
            critical_faqs.sort(key=lambda x: x.priority, reverse=True)
            critical_faq = critical_faqs[0]
            
            logger.info(f"✅ Retornando FAQ {critical_faq.id} directamente SIN pasar por LLM")
            
            # Retornar directamente la respuesta del FAQ sin pasar por el LLM
            # Esto garantiza 100% precisión sin invenciones
            response_text = critical_faq.answer
            
            # Limpiar cualquier referencia a fuente antigua (para evitar duplicados)
            import re
            response_text = re.sub(r'\n*\s*\[Fuente:.*?\]\s*$', '', response_text, flags=re.IGNORECASE)
            
            # Añadir un toque natural al inicio según el tipo
            intro_emoji = critical_request_detected.get('emoji', '📋')
            if not response_text.startswith('¡') and not response_text.startswith('Hola'):
                response_text = f"¡Hola! {intro_emoji} Con mucho gusto te muestro la información:\n\n{response_text}"
            
            # Guardar en historial
            db.add(
                Conversation(
                    business_id=message.business_id,
                    session_id=message.session_id,
                    user_message=message.message,
                    bot_response=response_text,
                    timestamp=datetime.utcnow(),
                )
            )
            db.commit()
            
            # Agregar delay natural (1-1.5 segundos)
            import time
            import random
            time.sleep(random.uniform(1.0, 1.5))
            
            return ChatResponse(
                response=response_text,
                timestamp=datetime.utcnow(),
            )
    
    # Si no es consulta crítica o no hay FAQ específico, continuar con flujo normal
    is_critical_request = critical_request_detected is not None
    if is_critical_request:
        current_max = 50  # Más FAQs si es consulta crítica
    else:
        current_max = chatbot_service.max_faqs
    
    # ============================================================================
    # FILTRADO INTELIGENTE DE FAQs RELEVANTES
    # ============================================================================
    # Filtrar FAQs por relevancia semántica antes de construir el contexto
    # para evitar confusión con múltiples FAQs no relacionadas
    # ============================================================================
    
    message_lower = message.message.lower()
    
    # Detectar si el cliente pide TODAS las normas/reglas (pregunta plural comprehensiva)
    wants_all_rules = any(phrase in message_lower for phrase in [
        'las normas', 'todas las normas', 'qué normas', 'cuáles son las normas',
        'las reglas', 'todas las reglas', 'qué reglas', 'cuáles son las reglas',
        'normativa', 'reglamento', 'dime las normas', 'cuales normas',
        'normas del gimnasio', 'reglas del gimnasio'
    ])
    
    if wants_all_rules:
        logger.info(f"🔥 DETECTADO: Pregunta por TODAS LAS NORMAS - Mensaje: '{message.message}'")
    
    # Palabras clave para filtrar FAQs relevantes
    keywords_in_message = []
    
    # Extraer palabras clave significativas (sustantivos y verbos importantes)
    important_words = ['norma', 'regla', 'prohibido', 'permitido', 'horario', 'precio', 
                       'servicio', 'clase', 'reserva', 'instalación', 'equipamiento',
                       'acceso', 'entrada', 'tarjeta', 'fumar', 'alcohol', 'comida',
                       'bebida', 'gimnasio', 'spa', 'piscina', 'ducha', 'taquilla']
    
    for word in important_words:
        if word in message_lower:
            keywords_in_message.append(word)
    
    # Si detectamos palabras clave, filtrar FAQs relevantes
    if keywords_in_message:
        logger.info(f"🔍 Palabras clave detectadas: {keywords_in_message}")
        
        if wants_all_rules:
            logger.info(f"📋 Cliente pide TODAS las normas/reglas - incluyendo todas las FAQs relacionadas")
        
        # Filtrar FAQs que contengan al menos una palabra clave
        relevant_faqs = []
        for faq in faqs:
            faq_text = (faq.question + " " + faq.answer + " " + (faq.category or "")).lower()
            if any(keyword in faq_text for keyword in keywords_in_message):
                relevant_faqs.append(faq)
        
        if relevant_faqs:
            logger.info(f"✅ FAQs relevantes encontradas: {len(relevant_faqs)} de {len(faqs)}")
            faqs = relevant_faqs  # Usar solo las FAQs relevantes
        else:
            logger.info(f"⚠️ No se encontraron FAQs relevantes, usando todas: {len(faqs)}")
    
    # ============================================================================

    if chatbot_service.model_failed:
        if chatbot_service.model is not None:
            chatbot_service.model_failed = False
            try:
                chatbot_service._failed_at = None
            except Exception:
                pass
        else:
            try:
                phone = business.phone or "el negocio"
            except Exception:
                phone = "el negocio"
            try:
                if not getattr(chatbot_service, "_initializing", False):
                    threading.Thread(target=chatbot_service.initialize_model, daemon=True).start()
            except Exception:
                pass
            return ChatResponse(
                response="El modelo se está preparando. Intenta de nuevo en unos segundos.",
                timestamp=datetime.utcnow(),
            )

    if getattr(chatbot_service, "_initializing", False):
        return ChatResponse(
            response="El modelo se está inicializando. Por favor espera unos segundos y vuelve a intentarlo.",
            timestamp=datetime.utcnow(),
        )

    if chatbot_service.model is None:
        try:
            threading.Thread(target=chatbot_service.initialize_model, daemon=True).start()
        except Exception:
            pass
        return ChatResponse(
            response="El modelo se está preparando. Intenta de nuevo en unos segundos.",
            timestamp=datetime.utcnow(),
        )

    # Ajustar max_faqs según el tipo de consulta
    if wants_all_rules:
        current_max = 50  # Muchas FAQs para listar todas las normas
        logger.info(f"→ Aumentando max_faqs a {current_max} para incluir todas las normas")
        num_faqs_for_context = len(faqs)  # Guardar el número real de FAQs para cálculo de tokens
    else:
        current_max = chatbot_service.max_faqs
        num_faqs_for_context = min(len(faqs), current_max)
    
    context = chatbot_service.build_context(
        business,
        faqs,
        max_faqs=current_max,
        include_default_instructions=not is_critical_request,
        menu_focus=is_critical_request,
    )

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
        for entry in history_entries:
            if entry.bot_response and name_lower in entry.bot_response.lower():
                name_already_used = True
                break
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
            snippet_text = snippet.get("text", "")
            context += f"- {source_label}: {snippet_text}\n"

    if chatbot_service.is_recommendation_request(message.message):
        context += (
            "\nEl cliente está pidiendo una recomendación concreta. Usa la información del negocio y las FAQs para sugerir como máximo dos opciones específicas (platos, servicios o planes), explica brevemente por qué encajan con lo que pide y ofrece una alternativa opcional si aplica."
        )

    context += """
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

    try:
        best = None
        best_ratio = 0.0
        for faq in faqs:
            question = (faq.question or "").strip()
            if not question:
                continue
            ratio = difflib.SequenceMatcher(None, message.message.lower(), question.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best = faq
        if best and best_ratio >= 0.70:
            bot_response = (best.answer or "").strip()
            try:
                conversation = Conversation(
                    business_id=message.business_id,
                    session_id=message.session_id,
                    user_message=message.message,
                    bot_response=bot_response,
                )
                db.add(conversation)
                db.commit()
            except Exception:
                pass
            return ChatResponse(response=bot_response, timestamp=datetime.utcnow())
    except Exception:
        pass

    try:
        approx_tokens = max(1, len(context + message.message) // chatbot_service.context_token_ratio)
        allowed = chatbot_service.context_window - chatbot_service.reserve_response_tokens
        while approx_tokens > allowed and current_max > 1:
            current_max = max(1, current_max // 2)
            context = chatbot_service.build_context(
                business,
                faqs,
                max_faqs=current_max,
                include_default_instructions=not is_critical_request,
                menu_focus=is_critical_request,
            )
            approx_tokens = max(1, len(context + message.message) // chatbot_service.context_token_ratio)

        if approx_tokens > allowed:
            max_chars = allowed * chatbot_service.context_token_ratio
            full = context + f"\n\n{message.message}\n"
            tail = full[-(max_chars // 2):]
            head = full[: max(0, max_chars - len(tail))]
            context = head + tail
    except Exception:
        pass

    loop = asyncio.get_event_loop()
    generation_kwargs = {
        "temperature": getattr(business, "generation_temperature", None),
        "top_p": getattr(business, "generation_top_p", None),
        "welcome_message": getattr(business, "welcome_message", None) if not conversation_started else None,
        "suppress_greeting": conversation_started,
        "customer_name": customer_name,
        "name_already_used": name_already_used,
        "db": db,
        "business": business,
        "wants_all_rules": wants_all_rules,  # Indicar si pide todas las normas
        "num_faqs_in_context": num_faqs_for_context,  # Número de FAQs para cálculo de tokens
    }

    try:
        bot_response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: chatbot_service.get_response(
                    message.message,
                    context,
                    **generation_kwargs,
                ),
            ),
            timeout=chatbot_service.generate_timeout + 5,
        )
    except asyncio.TimeoutError:
        try:
            phone = context.split('Teléfono: ')[1].splitlines()[0]
        except Exception:
            phone = "el negocio"
        bot_response = (
            "Lo siento, estoy tardando demasiado al generar la respuesta. Por favor inténtalo de nuevo o contacta con "
            f"{phone}."
        )
    except Exception:
        try:
            phone = context.split('Teléfono: ')[1].splitlines()[0]
        except Exception:
            phone = "el negocio"
        bot_response = (
            "Lo siento, estamos teniendo problemas técnicos. Por favor contacta con "
            f"{phone}."
        )

    try:
        conversation = Conversation(
            business_id=message.business_id,
            session_id=message.session_id,
            user_message=message.message,
            bot_response=bot_response,
        )
        db.add(conversation)
        db.commit()
    except Exception:
        pass

    # Agregar delay natural para simular "pensamiento" del bot (1-1.5 segundos)
    import time
    import random
    delay = random.uniform(1.0, 1.5)
    time.sleep(delay)

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
