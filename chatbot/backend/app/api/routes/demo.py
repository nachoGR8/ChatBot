"""Demo utilities such as seeding sample data."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ...models import Business, Conversation, FAQ
from ..dependencies import get_db, verify_admin_api_key

router = APIRouter(tags=["demo"])

DEMO_NAME = "Asistente de demostración"
# (pregunta, respuesta, categoría, prioridad): el asistente explica el propio proyecto.
DEMO_FAQS = [
    ("¿Qué es este chatbot?",
     "Un asistente que cualquier negocio puede añadir a su web con dos líneas. Responde con las FAQ del negocio y, "
     "si no hay una respuesta exacta, con un modelo de lenguaje que corre en el propio servidor.",
     "general", 10),
    ("¿Qué modelo de IA usa?",
     "Un modelo Llama cuantizado (GGUF) que se ejecuta con llama.cpp en el mismo servidor, sin APIs de pago.",
     "tecnologia", 9),
    ("¿Mis datos salen del servidor?",
     "No. Las preguntas, las FAQ y el modelo están en el mismo servidor: no se envía nada a servicios externos.",
     "privacidad", 9),
    ("¿Cómo lo añado a mi web?",
     "Con dos líneas: una indica el ID del negocio y otra carga widget.js desde el servidor del chatbot.",
     "integracion", 8),
    ("¿Puede atender a varios negocios?",
     "Sí. Cada negocio tiene sus propias FAQ, su tono y su mensaje de bienvenida, y se gestionan desde el panel de administración.",
     "general", 7),
]


@router.post("/seed-demo", dependencies=[Depends(verify_admin_api_key)])
def seed_demo_data(
    db: Session = Depends(get_db),
    reset: bool = Query(False, description="Si es true, borra los datos existentes y los recrea"),
):
    existing = db.query(Business).filter(func.lower(Business.name) == DEMO_NAME.lower()).first()

    if reset and existing:
        db.query(FAQ).filter(FAQ.business_id == existing.id).delete()
        db.query(Conversation).filter(Conversation.business_id == existing.id).delete()
        db.delete(existing)
        db.commit()
        existing = None

    if existing:
        return {
            "msg": "El negocio de demo ya existe, no se ha duplicado.",
            "business_id": existing.id,
            "business_name": existing.name,
            "note": "Usa ?reset=true para regenerar desde cero.",
        }

    demo_business = Business(
        name=DEMO_NAME,
        business_type="otro",
        welcome_message="¡Hola! 👋 Soy la demo de este chatbot. Pregúntame cómo funciona.",
    )
    db.add(demo_business)
    db.commit()
    db.refresh(demo_business)

    demo_faqs = [
        FAQ(business_id=demo_business.id, question=q, answer=a, category=c, priority=p)
        for q, a, c, p in DEMO_FAQS
    ]

    for faq in demo_faqs:
        db.add(faq)

    db.commit()

    return {
        "msg": "Datos de demo creados correctamente" + (" (reset)" if reset else ""),
        "business_id": demo_business.id,
        "business_name": demo_business.name,
        "faqs_created": len(demo_faqs),
    }
