from sqlalchemy.orm import Session
from main import SessionLocal, Business, FAQ

CATEGORY_FAQS = {
    "gym": [
        {"question": "¿Qué horario tenéis?", "answer": "Abrimos de lunes a viernes de 7:00 a 22:00, sábados de 9:00 a 14:00."},
        {"question": "¿Cuál es el precio mensual?", "answer": "El precio mensual es de 30€ con acceso completo."},
        {"question": "¿Tenéis entrenadores personales?", "answer": "Sí, disponemos de entrenadores personales bajo cita previa."},
    ],
    "restaurant": [
        {"question": "¿Cuál es el horario de cocina?", "answer": "De 12:00 a 16:00 y de 20:00 a 23:30."},
        {"question": "¿Puedo hacer una reserva?", "answer": "Sí, puedes reservar por teléfono o directamente desde nuestra web."},
        {"question": "¿Hacéis delivery?", "answer": "Sí, trabajamos con Glovo y Uber Eats."},
    ],
    "hairdresser": [
        {"question": "¿Necesito cita previa?", "answer": "Sí, recomendamos pedir cita previa para evitar esperas."},
        {"question": "¿Cuánto cuesta un corte de pelo?", "answer": "El precio medio de un corte es de 15€."},
        {"question": "¿Ofrecéis tintes o mechas?", "answer": "Sí, tenemos varios tratamientos de color disponibles."},
    ],
    "other": [
        {"question": "¿Cuál es vuestro horario?", "answer": "Abrimos de lunes a viernes en horario comercial."},
        {"question": "¿Cómo puedo contactar?", "answer": "Puedes llamarnos al teléfono de la empresa o escribirnos por WhatsApp."},
    ],
}

def seed_faqs_for_business(db: Session, business: Business):
    faqs = CATEGORY_FAQS.get(business.category, CATEGORY_FAQS["other"])
    
    for faq in faqs:
        exists = db.query(FAQ).filter(
            FAQ.business_id == business.id,
            FAQ.question == faq["question"]
        ).first()
        
        if not exists:
            db.add(FAQ(
                business_id=business.id,
                question=faq["question"],
                answer=faq["answer"],
                priority=0
            ))
    
    db.commit()
    print(f"✅ FAQs insertadas para {business.name} ({business.category})")


if __name__ == "__main__":
    db = SessionLocal()
    businesses = db.query(Business).all()
    for b in businesses:
        seed_faqs_for_business(db, b)
    db.close()
