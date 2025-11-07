from main import SessionLocal, Business, FAQ

def make_faqs():
    # A list of FAQs tailored for a gym business
    return [
        {"q": "¿Cuál es vuestro horario?", "a": "Abrimos de lunes a viernes de 06:00 a 23:00 y sábados/domingos de 08:00 a 20:00.", "category": "horario", "priority": 10},
        {"q": "¿Tenéis clases dirigidas?", "a": "Sí, ofrecemos clases dirigidas como yoga, spinning, crossfit, pilates y zumba. Consulta el horario en recepción o en nuestra web.", "category": "clases", "priority": 9},
        {"q": "¿Ofrecéis entrenadores personales?", "a": "Sí, contamos con entrenadores certificados disponibles por hora. Consulta disponibilidad y tarifas en recepción.", "category": "entrenador", "priority": 9},
        {"q": "¿Cómo puedo hacerme socio?", "a": "Puedes hacerte socio en recepción rellenando la ficha o desde nuestra web en la sección 'Afíliate'. Necesitarás una fotocopia del DNI y una cuenta bancaria para domiciliación.", "category": "membresía", "priority": 10},
        {"q": "¿Tenéis oferta de prueba gratuita?", "a": "Ofrecemos una clase de prueba gratuita para nuevos clientes. Reserva llamando o en recepción.", "category": "promociones", "priority": 8},
        {"q": "¿Cuánto cuesta la membresía mensual?", "a": "Tenemos varios planes: básico 29€/mes, estándar 45€/mes y premium 65€/mes (incluye clases y acceso 24/7 según plan).", "category": "precios", "priority": 9},
        {"q": "¿Hay descuentos para estudiantes o familias?", "a": "Sí, ofrecemos descuentos para estudiantes y tarifas familiares. Consulta condiciones en recepción.", "category": "precios", "priority": 7},
        {"q": "¿Aceptáis pagos con tarjeta?", "a": "Sí, aceptamos tarjeta de crédito/débito y domiciliación bancaria para las mensualidades.", "category": "pagos", "priority": 7},
        {"q": "¿Cómo funciona la cancelación de la suscripción?", "a": "La baja se solicita por escrito con 30 días de antelación y puede gestionarse en recepción o por email.", "category": "membresía", "priority": 8},
        {"q": "¿Ofrecéis entrenamientos online?", "a": "Disponemos de entrenamientos y rutinas en vídeo accesibles con la membresía premium.", "category": "online", "priority": 6},
        {"q": "¿Tenéis taquillas y duchas?", "a": "Sí, disponemos de taquillas y duchas con gel y secador. Trae un candado o compra uno en recepción.", "category": "instalaciones", "priority": 8},
        {"q": "¿Hay parking disponible?", "a": "Disponemos de parking gratuito limitado para clientes; también hay aparcamiento público en la calle cercana.", "category": "instalaciones", "priority": 6},
        {"q": "¿El gimnasio es accesible para personas con movilidad reducida?", "a": "Sí, nuestras instalaciones cuentan con accesos adaptados y baño accesible.", "category": "accesibilidad", "priority": 7},
        {"q": "¿Puedo traer a mi hijo?", "a": "Por razones de seguridad, los menores deben ir acompañados y solo se permite la entrada a zonas familiares durante horarios concretos. Consulta la política infantil en recepción.", "category": "políticas", "priority": 5},
        {"q": "¿Qué medidas de higiene tenéis?", "a": "Limpiamos y desinfectamos equipos varias veces al día. Disponemos de gel hidroalcohólico y protocolos de higiene para miembros y personal.", "category": "salud", "priority": 9},
        {"q": "¿Puedo congelar mi suscripción temporalmente?", "a": "Sí, ofrecemos congelación de contrato por motivos médicos o temporales previa presentación de documentación. Consulta condiciones en recepción.", "category": "membresía", "priority": 6},
        {"q": "¿Cómo reservo una clase o entrenador?", "a": "Reservas vía app, web o en recepción. Para entrenadores personales se recomienda reservar con antelación.", "category": "reservas", "priority": 8},
        {"q": "¿Ofrecéis nutricionista o planes de dieta?", "a": "Sí, tenemos un servicio de nutrición con cita previa (servicio adicional).", "category": "servicios", "priority": 6},
        {"q": "¿Tenéis Wi-Fi para clientes?", "a": "Sí, Wi‑Fi gratuito para socios. Pregunta la contraseña en recepción.", "category": "instalaciones", "priority": 5},
        {"q": "¿Cómo puedo contactar con el gimnasio?", "a": "Teléfono: +34 600 000 001, Email: info@borjagym.com o acércate a recepción en horario de apertura.", "category": "contacto", "priority": 10},
        {"q": "¿Qué normas debo seguir en las instalaciones?", "a": "Por favor usa toalla en máquinas, limpia tu equipo tras el uso y respeta los turnos en las clases. No se permite fumar ni consumir alcohol.", "category": "políticas", "priority": 7},
        {"q": "¿Hay horario especial en festivos?", "a": "En festivos solemos tener horario reducido. Consulta el calendario de festivos en nuestra web o en recepción.", "category": "horario", "priority": 5},
        {"q": "¿Tenéis programas para mayores o rehabilitación?", "a": "Sí, contamos con clases específicas para mayores y programas supervisados por profesionales para rehabilitación.", "category": "servicios", "priority": 5}
    ]

def main():
    db = SessionLocal()
    try:
        biz = db.query(Business).filter(Business.name == 'Borja SL').first()
        if not biz:
            print("Negocio 'Borja SL' no encontrado. Creando negocio...")
            biz = Business(name='Borja SL', business_type='gym', phone='+34 600 000 001', email='info@borjagym.com', address='Calle Fitness 10', website='www.borjagym.com')
            db.add(biz)
            db.commit()
            db.refresh(biz)
            print(f"Negocio creado con id={biz.id}")
        else:
            print(f"Encontrado negocio 'Borja SL' con id={biz.id}")

        faqs = make_faqs()
        added = 0
        for f in faqs:
            # Evitar duplicados simples comparando pregunta exacta
            exists = db.query(FAQ).filter(FAQ.business_id == biz.id, FAQ.question == f['q']).first()
            if exists:
                continue
            new = FAQ(business_id=biz.id, question=f['q'], answer=f['a'], category=f.get('category'), priority=f.get('priority', 0))
            db.add(new)
            added += 1

        db.commit()
        print(f"FAQs procesadas: {len(faqs)}. FAQs nuevas añadidas: {added}.")
    finally:
        db.close()

if __name__ == '__main__':
    main()
