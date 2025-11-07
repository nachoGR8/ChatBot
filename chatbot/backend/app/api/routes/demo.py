"""Demo utilities such as seeding sample data."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ...models import Business, Conversation, FAQ
from ..dependencies import get_db

router = APIRouter(tags=["demo"])


@router.post("/seed-demo")
def seed_demo_data(
    db: Session = Depends(get_db),
    reset: bool = Query(False, description="Si es true, borra los datos existentes y los recrea"),
):
    existing = db.query(Business).filter(func.lower(Business.name) == "restaurante la paella").first()

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
        name="Restaurante La Paella",
        business_type="restaurant",
        phone="+34 977 123 456",
        email="info@lapaella.com",
        address="Calle Principal 123, Salou",
        website="www.lapaella.com",
    )
    db.add(demo_business)
    db.commit()
    db.refresh(demo_business)

    demo_faqs = [
        FAQ(
            business_id=demo_business.id,
            question="¿Qué horario tenéis?",
            answer="Abrimos de lunes a domingo de 13:00 a 16:00 y de 20:00 a 23:30. Los domingos solo mediodía.",
            category="horario",
            priority=10,
        ),
        FAQ(
            business_id=demo_business.id,
            question="¿Tenéis menú sin gluten?",
            answer="Sí, tenemos opciones sin gluten en todos nuestros menús. Nuestro arroz y marisco son naturalmente sin gluten.",
            category="menu",
            priority=9,
        ),
        FAQ(
            business_id=demo_business.id,
            question="¿Cómo puedo hacer una reserva?",
            answer="Puedes reservar llamando al +34 977 123 456 o escribiéndonos a info@lapaella.com. También por WhatsApp.",
            category="reservas",
            priority=10,
        ),
        FAQ(
            business_id=demo_business.id,
            question="¿Tenéis parking?",
            answer="Sí, tenemos parking privado gratuito para clientes justo detrás del restaurante.",
            category="instalaciones",
            priority=5,
        ),
        FAQ(
            business_id=demo_business.id,
            question="¿Aceptáis grupos grandes?",
            answer="Sí, tenemos capacidad para grupos de hasta 50 personas. Para grupos superiores a 10, recomendamos reservar con antelación.",
            category="reservas",
            priority=7,
        ),
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
