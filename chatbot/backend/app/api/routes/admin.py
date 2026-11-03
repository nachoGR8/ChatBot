"""Administrative routes for the chatbot backend."""
from __future__ import annotations

import threading
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...models import Business, FAQ
from ...schemas import ConfigUpdate
from ..dependencies import get_db, verify_admin_api_key
from ...services.chatbot_service import chatbot_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin_api_key)])


@router.get("/config")
def get_config() -> Dict[str, object]:
    try:
        return {
            "ok": True,
            "config": {
                "max_faqs": chatbot_service.max_faqs,
                "faq_answer_max_chars": chatbot_service.faq_answer_max_chars,
                "faq_question_max_chars": chatbot_service.faq_question_max_chars,
                "context_window": chatbot_service.context_window,
                "context_token_ratio": chatbot_service.context_token_ratio,
                "reserve_response_tokens": chatbot_service.reserve_response_tokens,
            },
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/config")
def update_config(payload: ConfigUpdate) -> Dict[str, object]:
    try:
        data = payload.dict(exclude_unset=True)
        if "max_faqs" in data:
            chatbot_service.max_faqs = max(1, int(data["max_faqs"]))
        if "faq_answer_max_chars" in data:
            chatbot_service.faq_answer_max_chars = max(32, int(data["faq_answer_max_chars"]))
        if "faq_question_max_chars" in data:
            chatbot_service.faq_question_max_chars = max(16, int(data["faq_question_max_chars"]))

        return {
            "ok": True,
            "config": {
                "max_faqs": chatbot_service.max_faqs,
                "faq_answer_max_chars": chatbot_service.faq_answer_max_chars,
                "faq_question_max_chars": chatbot_service.faq_question_max_chars,
            },
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/ensure_gym_faqs")
def admin_ensure_gym_faqs(db: Session = Depends(get_db)):
    faqs = [
        ("¿Cuál es vuestro horario?", "Abrimos de lunes a viernes de 06:00 a 23:00; sábados y domingos de 08:00 a 20:00."),
        ("¿Cómo puedo hacerme socio?", "Puedes hacerte socio en recepción o desde nuestra web. Necesitarás DNI y método de pago para domiciliación."),
        ("¿Qué tipos de membresía ofrecéis?", "Ofrecemos Plan Básico, Estándar y Premium; consulta los precios y beneficios en recepción o en la web."),
        ("¿Hay periodos de prueba gratuitos?", "Sí, ofrecemos una clase de prueba gratuita para nuevos clientes. Reserva previa obligatoria."),
        ("¿Tenéis clases dirigidas?", "Sí: yoga, pilates, spinning, zumba, crossfit y bodypump. Consulta el horario actualizado en la app o en recepción."),
        ("¿Cómo reservo una clase?", "Reserva desde la app, la web o en recepción. Las plazas son limitadas y suelen requerir reserva previa."),
        ("¿Ofrecéis entrenadores personales?", "Sí, contamos con entrenadores personales certificados. Consulta tarifas y disponibilidad en recepción."),
        ("¿Puedo cancelar mi membresía?", "La baja se solicita por escrito con 30 días de antelación. Consulta condiciones en tu contrato."),
        ("¿Tenéis taquillas y duchas?", "Sí, taquillas y duchas disponibles. Trae o compra un candado en recepción."),
        ("¿Hay parking?", "Tenemos parking limitado para clientes y aparcamiento público cercano."),
        ("¿Se permite la entrada a menores?", "Los menores deben ir acompañados de un adulto y solo pueden acceder a áreas habilitadas. Consulta la política infantil en recepción."),
        ("¿Qué medidas de higiene seguís?", "Desinfectamos máquinas varias veces al día. Disponemos de gel hidroalcohólico y solicitamos el uso de toalla."),
        ("¿Tenéis Wifi gratuito?", "Sí, Wifi gratuito para socios. Pide la contraseña en recepción."),
        ("¿Puedo congelar mi suscripción?", "Se permite congelar la suscripción por motivos médicos o personales según condiciones; consulta en recepción."),
        ("¿Aceptáis pagos con tarjeta?", "Sí, aceptamos tarjeta y domiciliación bancaria para mensualidades."),
        ("¿Ofrecéis planes para empresas?", "Sí, tenemos tarifas corporativas y packs para empresas; contacta con ventas para más información."),
        ("¿Qué ocurre si me lesiono en el gimnasio?", "Notifica al personal inmediatamente; recomendamos consulta médica. Tenemos protocolos y personal formado para primeros auxilios."),
        ("¿Tenéis programas de rehabilitación o para mayores?", "Sí, programas supervisados por profesionales para rehabilitación y clases adaptadas para mayores."),
        ("¿Puedo traer mi propio entrenador?", "Se permite con autorización y siempre que el entrenador cumpla nuestros requisitos; consulta en recepción."),
        ("¿Ofrecéis servicios de nutrición?", "Sí, asesoramiento nutricional con cita previa (servicio de pago adicional)."),
        ("¿Cuál es la política de reservas para grupos grandes?", "Para grupos >10 recomendamos reservar con antelación y consultar condiciones especiales."),
        ("¿Qué debo llevar al gimnasio?", "Ropa deportiva, calzado adecuado, toalla y botella de agua. Evita ropa de calle en las áreas de entrenamiento."),
        ("¿Hay normas de uso de equipos?", "Usa toalla, desinfecta tras uso y respeta tiempos en máquinas durante horas punta."),
        ("¿Tenéis política de reembolso?", "Las devoluciones se gestionan según el contrato y la causa; consulta en recepción para casos específicos."),
        ("¿Cómo puedo contactar con atención al cliente?", "Teléfono: +34 600 000 001, Email: info@borjagym.com o acude a recepción en horario de apertura."),
    ]

    created = False
    biz = db.query(Business).filter(Business.id == 1).first()
    if not biz:
        biz = Business(
            name="Borja SL",
            business_type="gym",
            phone="+34 600 000 001",
            email="info@borjagym.com",
            address="Calle Fitness 10",
            website="www.borjagym.com",
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)
        created = True
    else:
        if (biz.business_type or "").lower() not in ("gym", "gimnasio"):
            biz.business_type = "gym"
            db.add(biz)
            db.commit()

    added = 0
    for question, answer in faqs:
        exists = (
            db.query(FAQ)
            .filter(FAQ.business_id == biz.id, FAQ.question == question)
            .first()
        )
        if exists:
            continue
        db.add(
            FAQ(
                business_id=biz.id,
                question=question,
                answer=answer,
                category="general",
                priority=5,
            )
        )
        added += 1

    db.commit()

    return {
        "business_id": biz.id,
        "created": created,
        "faqs_processed": len(faqs),
        "faqs_added": added,
    }


@router.get("/model_status")
def admin_model_status():
    status = {
        "model_present": chatbot_service.model is not None,
        "initializing": chatbot_service._initializing,
        "failed": chatbot_service.model_failed,
        "backend": chatbot_service._backend,
        "device": chatbot_service._device,
    }
    model = chatbot_service.model
    if model is not None:
        try:
            status["backend"] = model.backend
            status["device"] = model.device
        except Exception as exc:
            status["backend_error"] = str(exc)
    return status


@router.post("/clear_model_failure")
def admin_clear_model_failure():
    chatbot_service.reset_failure()
    if chatbot_service.model is None and not chatbot_service._initializing:
        threading.Thread(target=chatbot_service.initialize_model, daemon=True).start()
    return {"ok": True, "model_failed": chatbot_service.model_failed}


@router.post("/reinit_model")
def admin_reinit_model():
    chatbot_service.model = None
    chatbot_service.reset_failure()
    threading.Thread(target=chatbot_service.initialize_model, daemon=True).start()
    return {"ok": True, "message": "Reinicialización disparada"}
