from main import SessionLocal, Business, FAQ

def make_extra_faqs():
    return [
        ("¿Cuál es vuestro horario?", "Abrimos de lunes a viernes de 06:00 a 23:00; sábados y domingos de 08:00 a 20:00."),
        ("¿Cómo puedo hacerme socio?", "Puedes hacerte socio en recepción o desde nuestra web. Necesitarás DNI y método de pago para domiciliación."),
        ("¿Qué tipos de membresía ofrecéis?", "Ofrecemos Plan Básico, Estándar y Premium; consulta los precios y beneficios en recepción o en la web."),
        ("¿Hay periodos de prueba gratuitos?", "Sí, ofrecemos una clase de prueba gratuita para nuevos clientes. Reserva previa obligatoria."),
        ("¿Tenéis clases dirigidas?", "Sí: yoga, pilates, spinning, zumba, crossfit y bodypump. Consulta el horario actualizado en la app o en recepción."),
        ("¿Cómo reservo una clase?", "Reserva desde la app, la web o en recepción. Las plazas son limitadas y suelen requerir reserva previa."),
        ("¿Ofrecéis entrenadores personales?", "Sí, contamos con entrenadores personales certificados. Consulta tarifas y disponibilidad en recepción."),
        ("¿Puedo cancelar mi membresía?", "La baja se solicita por escrito con 30 días de antelación. Consulta condiciones en tu contrato.") ,
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

def main():
    db = SessionLocal()
    try:
        biz = db.query(Business).filter(Business.id == 1).first()
        if not biz:
            print("Negocio id=1 no encontrado. Creando negocio 'Borja SL' como gimnasio...")
            biz = Business(name='Borja SL', business_type='gym', phone='+34 600 000 001', email='info@borjagym.com', address='Calle Fitness 10', website='www.borjagym.com')
            db.add(biz)
            db.commit()
            db.refresh(biz)
        else:
            # asegurar que es gym
            if (biz.business_type or '').lower() != 'gym' and (biz.business_type or '').lower() != 'gimnasio':
                print(f"Actualizando business_type de id=1: {biz.business_type} -> gym")
                biz.business_type = 'gym'
                db.add(biz)
                db.commit()

        faqs = make_extra_faqs()
        added = 0
        for q,a in faqs:
            exists = db.query(FAQ).filter(FAQ.business_id == biz.id, FAQ.question == q).first()
            if exists:
                continue
            new = FAQ(business_id=biz.id, question=q, answer=a, category='general', priority=5)
            db.add(new)
            added += 1
        db.commit()
        print(f"FAQs procesadas: {len(faqs)}. FAQs nuevas añadidas: {added}.")
    finally:
        db.close()

if __name__ == '__main__':
    main()
