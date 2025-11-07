# comprehensive_faqs.py
# Sistema completo de FAQs para el chatbot

from typing import List, Tuple, Dict
from datetime import datetime

def get_comprehensive_global_faqs() -> List[Tuple[str, str, str, int]]:
    """
    Devuelve FAQs globales exhaustivas para cualquier negocio.
    Formato: (pregunta, respuesta, categoría, prioridad)
    """
    return [
        # ========== IDENTIDAD Y ASISTENTE ==========
        ("qué eres", "Soy un asistente virtual inteligente 🤖 diseñado para ayudarte 24/7 con cualquier duda sobre {business_name}.", "asistente", 10),
        ("quién eres", "Soy el asistente virtual oficial de {business_name}. Estoy aquí para resolver todas tus preguntas al instante.", "asistente", 10),
        ("eres una persona", "No, soy un asistente de inteligencia artificial, pero estoy programado para ayudarte como lo haría el mejor empleado.", "asistente", 9),
        ("eres un robot", "Sí, soy un chatbot con IA avanzada. Puedo responder preguntas, dar información y ayudarte con reservas o consultas.", "asistente", 9),
        ("cómo te llamas", "Soy el asistente virtual de {business_name}. No tengo nombre propio, pero puedes llamarme asistente.", "asistente", 8),
        ("quién te creó", "Fui desarrollado con tecnología de IA para servir específicamente a los clientes de {business_name}.", "asistente", 7),
        ("cómo funcionas", "Uso inteligencia artificial para entender tus preguntas y darte respuestas precisas basadas en la información de {business_name}.", "asistente", 7),
        
        # ========== SALUDOS Y CORTESÍA ==========
        ("hola", "¡Hola! 👋 Bienvenido/a a {business_name}. ¿En qué puedo ayudarte hoy?", "saludo", 10),
        ("buenos días", "¡Buenos días! ☀️ Es un placer atenderte. ¿Qué información necesitas sobre {business_name}?", "saludo", 10),
        ("buenas tardes", "¡Buenas tardes! 😊 Estoy aquí para ayudarte con lo que necesites.", "saludo", 10),
        ("buenas noches", "¡Buenas noches! 🌙 Aunque sea tarde, estoy disponible para ayudarte.", "saludo", 10),
        ("hey", "¡Hey! 👋 ¿Cómo puedo ayudarte con {business_name}?", "saludo", 9),
        ("qué tal", "¡Muy bien, gracias por preguntar! Estoy listo para ayudarte. ¿Qué necesitas saber?", "saludo", 9),
        ("cómo estás", "¡Excelente y listo para ayudarte! ¿Qué puedo hacer por ti hoy?", "saludo", 8),
        
        # ========== DESPEDIDAS ==========
        ("adiós", "¡Hasta pronto! 👋 Gracias por contactar con {business_name}. ¡Que tengas un excelente día!", "despedida", 10),
        ("hasta luego", "¡Hasta luego! Espero haberte ayudado. Recuerda que estoy aquí 24/7 cuando me necesites.", "despedida", 10),
        ("chao", "¡Chao! 👋 Fue un placer ayudarte. ¡Vuelve cuando quieras!", "despedida", 9),
        ("nos vemos", "¡Nos vemos! Gracias por elegir {business_name}. ¡Hasta la próxima!", "despedida", 9),
        
        # ========== AGRADECIMIENTOS ==========
        ("gracias", "¡De nada! 😊 Es un placer ayudarte. ¿Necesitas algo más?", "cortesía", 10),
        ("muchas gracias", "¡Con mucho gusto! 🙌 Para eso estoy aquí. ¿Hay algo más en lo que pueda ayudarte?", "cortesía", 10),
        ("te agradezco", "¡No hay de qué! Me alegra poder ayudarte. ¿Tienes alguna otra pregunta?", "cortesía", 9),
        ("perfecto", "¡Genial! 👍 ¿Hay algo más que quieras saber sobre {business_name}?", "cortesía", 9),
        ("ok", "Perfecto 👌 ¿Te puedo ayudar en algo más?", "cortesía", 8),
        ("vale", "Estupendo ✅ ¿Necesitas información adicional?", "cortesía", 8),
        
        # ========== HORARIOS DETALLADOS ==========
        ("qué horario tenéis", "📅 Nuestro horario es: {schedule}. ¿Quieres saber si estamos abiertos ahora mismo?", "horario", 10),
        ("a qué hora abrís", "🕐 Abrimos a las {opening_time}. Nuestro horario completo es: {schedule}", "horario", 10),
        ("a qué hora cerráis", "🕐 Cerramos a las {closing_time}. Ten en cuenta que el último servicio es 30 minutos antes.", "horario", 10),
        ("estáis abiertos", "Sí, estamos abiertos. Nuestro horario hoy es: {today_schedule}. ¡Te esperamos!", "horario", 10),
        ("estáis abiertos ahora", "{open_now_status}. Nuestro horario de hoy es: {today_schedule}", "horario", 10),
        ("abrís los domingos", "{sunday_schedule}. Los domingos solemos tener horario especial.", "horario", 9),
        ("abrís los festivos", "En festivos nuestro horario puede variar. Te recomiendo llamar al {phone} para confirmar.", "horario", 9),
        ("horario de fin de semana", "🗓️ Fines de semana: {weekend_schedule}. ¡Te esperamos!", "horario", 9),
        ("hasta qué hora estáis", "Hoy estamos hasta las {closing_time}. Último servicio 30 minutos antes del cierre.", "horario", 9),
        
        # ========== UBICACIÓN Y CÓMO LLEGAR ==========
        ("dónde estáis", "📍 Estamos en: {address}. ¿Necesitas indicaciones para llegar?", "ubicación", 10),
        ("cuál es vuestra dirección", "📍 Nuestra dirección es: {address}. Puedes encontrarnos fácilmente en Google Maps.", "ubicación", 10),
        ("cómo llego", "📍 Estamos en {address}. Puedes llegar en transporte público (paradas cercanas) o en coche (tenemos parking).", "ubicación", 10),
        ("dónde está el local", "📍 Nos encontrarás en: {address}. Estamos en una zona muy accesible.", "ubicación", 10),
        ("cómo os encuentro", "Es fácil encontrarnos: {address}. Busca '{business_name}' en Google Maps para indicaciones.", "ubicación", 9),
        ("estáis cerca de", "Estamos en {address}. Dime desde dónde vienes y te oriento mejor.", "ubicación", 8),
        ("hay parking", "🚗 Sí, {parking_info}. También hay transporte público cerca.", "ubicación", 9),
        ("dónde aparcar", "🚗 {parking_info}. La zona tiene bastantes opciones de aparcamiento.", "ubicación", 8),
        
        # ========== CONTACTO COMPLETO ==========
        ("teléfono", "📞 Nuestro teléfono es: {phone}. Atendemos llamadas en horario comercial.", "contacto", 10),
        ("número de teléfono", "📞 Puedes llamarnos al: {phone}. Estaremos encantados de atenderte.", "contacto", 10),
        ("cómo os contacto", "📱 Puedes contactarnos: Teléfono {phone}, Email {email}, o visitarnos en {address}", "contacto", 10),
        ("email", "📧 Nuestro email es: {email}. Respondemos en menos de 24 horas.", "contacto", 10),
        ("correo electrónico", "📧 Escríbenos a: {email}. Te responderemos lo antes posible.", "contacto", 10),
        ("whatsapp", "📱 Sí, puedes escribirnos por WhatsApp al {phone}. Respondemos rápidamente.", "contacto", 9),
        ("tenéis instagram", "📱 Sí, síguenos en Instagram: @{social_media}. Publicamos novedades diariamente.", "contacto", 8),
        ("redes sociales", "📱 Encuéntranos en: Instagram @{social_media}, Facebook /{social_media}", "contacto", 8),
        ("página web", "🌐 Visita nuestra web: {website} para más información y servicios online.", "contacto", 9),
        
        # ========== RESERVAS Y CITAS ==========
        ("cómo reservo", "📅 Puedes reservar: 1) Llamando al {phone} 2) Por WhatsApp 3) Email a {email}", "reservas", 10),
        ("quiero reservar", "¡Perfecto! 📅 Para reservar llama al {phone} o escribe a {email} indicando fecha y hora deseada.", "reservas", 10),
        ("necesito cita", "📅 Sí, recomendamos cita previa. Llama al {phone} para reservar tu cita.", "reservas", 10),
        ("puedo reservar online", "🌐 {online_booking_info}. También puedes reservar por teléfono: {phone}", "reservas", 9),
        ("hay que reservar", "Recomendamos reservar, especialmente fines de semana. Llama al {phone}.", "reservas", 9),
        ("tenéis hueco hoy", "Para disponibilidad de hoy, llama directamente al {phone}. Te atenderemos enseguida.", "reservas", 9),
        ("puedo cancelar reserva", "Sí, puedes cancelar llamando al {phone} con al menos 2 horas de antelación.", "reservas", 8),
        ("política de cancelación", "Puedes cancelar hasta 2 horas antes sin cargo. Llama al {phone}.", "reservas", 8),
        
        # ========== SERVICIOS DETALLADOS ==========
        ("qué servicios ofrecéis", "📋 Ofrecemos: {services_list}. ¿Sobre cuál quieres más información?", "servicios", 10),
        ("qué hacéis", "Somos {business_type} especializado en {specialty}. Ofrecemos {services_summary}.", "servicios", 10),
        ("a qué os dedicáis", "Nos dedicamos a {business_description}. Llevamos años ofreciendo {specialty}.", "servicios", 10),
        ("qué puedo encontrar", "En {business_name} encontrarás: {services_list}. Todo con la máxima calidad.", "servicios", 9),
        ("qué vendéis", "📦 Vendemos/Ofrecemos: {products_services}. ¿Qué te interesa específicamente?", "servicios", 9),
        ("tenéis", "Disponemos de una amplia variedad de {products_services}. ¿Buscas algo en particular?", "servicios", 8),
        
        # ========== PRECIOS Y TARIFAS ==========
        ("precios", "💰 Nuestras tarifas: {price_range}. Los precios exactos dependen del servicio.", "precios", 10),
        ("cuánto cuesta", "💰 Los precios van {price_range}. ¿Sobre qué servicio quieres saber el precio?", "precios", 10),
        ("tarifas", "💰 Tarifas actualizadas: {price_list}. Pregunta por ofertas especiales.", "precios", 10),
        ("es caro", "Nuestros precios son competitivos: {price_range}. Ofrecemos excelente relación calidad-precio.", "precios", 9),
        ("tenéis ofertas", "🎁 {offers_info}. Pregunta por promociones actuales al llamar.", "precios", 9),
        ("descuentos", "🎁 {discount_info}. Consulta condiciones llamando al {phone}.", "precios", 9),
        ("precio medio", "💰 El precio medio es {average_price}. Varía según el servicio elegido.", "precios", 8),
        ("formas de pago", "💳 Aceptamos: {payment_methods}. Todos los métodos seguros.", "precios", 9),
        
        # ========== PAGOS ==========
        ("cómo pago", "💳 Puedes pagar con: {payment_methods}. Todos los pagos son seguros.", "pagos", 10),
        ("aceptáis tarjeta", "💳 Sí, aceptamos todas las tarjetas: Visa, MasterCard, Amex.", "pagos", 10),
        ("puedo pagar en efectivo", "💵 Sí, aceptamos efectivo. También tarjetas y pagos móviles.", "pagos", 10),
        ("tenéis datáfono", "Sí, tenemos datáfono para tarjetas y pagos contactless.", "pagos", 9),
        ("bizum", "📱 {bizum_info}. También aceptamos otros métodos de pago.", "pagos", 9),
        ("apple pay", "📱 Sí, aceptamos Apple Pay y Google Pay para tu comodidad.", "pagos", 8),
        ("pago a plazos", "💳 {installment_info}. Consulta condiciones en el local.", "pagos", 8),
        ("factura", "📄 Sí, emitimos factura. Solicítala al realizar el pago.", "pagos", 8),
        
        # ========== INSTALACIONES ==========
        ("cómo es el local", "🏢 {venue_description}. Ambiente {atmosphere}.", "instalaciones", 9),
        ("tenéis terraza", "☀️ {terrace_info}. Ideal para días soleados.", "instalaciones", 8),
        ("aire acondicionado", "❄️ Sí, tenemos aire acondicionado/calefacción para tu comodidad.", "instalaciones", 8),
        ("wifi", "📶 Sí, WiFi gratis para clientes. Pide la contraseña en recepción.", "instalaciones", 8),
        ("accesible", "♿ {accessibility_info}. Queremos que todos se sientan cómodos.", "instalaciones", 8),
        ("baños", "🚻 Sí, tenemos baños para clientes, incluido adaptado.", "instalaciones", 7),
        ("capacidad", "👥 Nuestra capacidad es {capacity}. Perfecto para grupos.", "instalaciones", 7),
        
        # ========== INFORMACIÓN ESPECÍFICA ==========
        ("cuánto tiempo lleváis", "📅 Llevamos {years_open} años sirviendo a nuestros clientes.", "info", 8),
        ("desde cuándo estáis", "📅 Abrimos en {opening_year}. {years_open} años de experiencia.", "info", 8),
        ("quién es el dueño", "👤 {owner_info}. Un negocio familiar/profesional.", "info", 7),
        ("trabajáis con cita", "{appointment_policy}. Recomendamos reservar.", "info", 8),
        ("admitís mascotas", "🐕 {pet_policy}. Consulta condiciones específicas.", "info", 8),
        ("para niños", "👶 {kids_policy}. Ambiente familiar.", "info", 8),
        
        # ========== URGENCIAS Y PROBLEMAS ==========
        ("es urgente", "🚨 Para urgencias, llama directamente al {phone}. Te atenderemos prioritariamente.", "urgencia", 10),
        ("necesito ayuda", "🆘 Claro, ¿en qué puedo ayudarte? Para atención inmediata llama al {phone}.", "urgencia", 10),
        ("tengo un problema", "😟 Lamento escuchar eso. Explícame el problema o llama al {phone} para resolverlo rápidamente.", "urgencia", 10),
        ("queja", "📝 Lamentamos cualquier inconveniente. Por favor, contacta al {phone} o {email} para gestionar tu queja.", "urgencia", 9),
        ("reclamación", "📝 Para reclamaciones formales, escribe a {email} o llama al {phone}. Lo resolveremos rápidamente.", "urgencia", 9),
        
        # ========== DISPONIBILIDAD ==========
        ("hay disponibilidad", "📅 Para consultar disponibilidad actual, llama al {phone}. Te informaremos al momento.", "disponibilidad", 9),
        ("tenéis sitio", "Para confirmarte disponibilidad necesito que llames al {phone}.", "disponibilidad", 9),
        ("está ocupado", "📅 La ocupación varía. Llama al {phone} para consultar disponibilidad actual.", "disponibilidad", 8),
        ("hay mucha gente", "La afluencia varía según el día. {busy_times}. Mejor reservar.", "disponibilidad", 8),
        ("mejor hora", "🕐 {best_times}. Menos gente y mejor servicio.", "disponibilidad", 8),
        
        # ========== EXTRAS ==========
        ("habláis inglés", "🌍 {languages_spoken}. Atendemos en varios idiomas.", "idiomas", 8),
        ("speak english", "Yes! We speak English. How can we help you?", "idiomas", 8),
        ("gift card", "🎁 {gift_card_info}. Un regalo perfecto.", "extras", 7),
        ("tarjeta regalo", "🎁 {gift_card_info}. Disponibles en el local.", "extras", 7),
        ("eventos", "🎉 {events_info}. Consultamos disponibilidad.", "extras", 8),
        ("celebraciones", "🎉 Sí, organizamos {events_types}. Llama para más info.", "extras", 8),
    ]

def get_business_specific_responses(business_type: str) -> Dict[str, str]:
    """
    Devuelve plantillas de respuesta específicas según el tipo de negocio
    """
    templates = {
        "restaurant": {
            "services_list": "cocina mediterránea, menú del día, carta, menús especiales, comida para llevar",
            "specialty": "platos tradicionales con un toque moderno",
            "business_description": "ofrecer la mejor experiencia gastronómica",
            "price_range": "desde 10€ (menú) hasta 30€ (carta)",
            "average_price": "20€ por persona",
            "atmosphere": "acogedor y familiar",
            "busy_times": "Los fines de semana de 14h-16h y 21h-23h solemos estar llenos",
            "best_times": "Entre semana 13h-14h y 20h-21h es más tranquilo",
        },
        "gimnasio": {
            "services_list": "sala de máquinas, clases dirigidas, entrenador personal, evaluación física",
            "specialty": "fitness y bienestar integral",
            "business_description": "mejorar tu salud y forma física",
            "price_range": "desde 25€ (día) hasta 45€ (mes)",
            "average_price": "35€/mes",
            "atmosphere": "motivador y energético",
            "busy_times": "De 18h a 21h suele haber más gente",
            "best_times": "Por las mañanas de 10h-12h hay menos gente",
        },
        "peluqueria": {
            "services_list": "corte, color, mechas, tratamientos, peinados, alisados",
            "specialty": "últimas tendencias en peluquería",
            "business_description": "cuidar y embellecer tu cabello",
            "price_range": "desde 15€ (corte) hasta 120€ (tratamiento completo)",
            "average_price": "35€ por servicio",
            "atmosphere": "moderno y relajante",
            "busy_times": "Viernes tarde y sábados suelen estar completos",
            "best_times": "Entre semana por la mañana hay más disponibilidad",
        },
        "clinica": {
            "services_list": "consultas, diagnóstico, tratamientos, seguimiento, urgencias",
            "specialty": "atención médica personalizada",
            "business_description": "cuidar tu salud con los mejores profesionales",
            "price_range": "desde 50€ (consulta) - pregunta por tu seguro",
            "average_price": "80€ por consulta",
            "atmosphere": "profesional y tranquilo",
            "busy_times": "Las primeras horas de la mañana suelen tener más demanda",
            "best_times": "Mediodía suele tener más disponibilidad",
        },
    }
    
    return templates.get(business_type.lower(), templates["restaurant"])

def format_faq_response(template: str, business_data: Dict[str, str]) -> str:
    """
    Formatea la respuesta de FAQ con los datos del negocio
    """
    # Datos por defecto si no están disponibles
    defaults = {
        "business_name": "nuestro establecimiento",
        "phone": "nuestro teléfono",
        "email": "nuestro email",
        "address": "nuestra dirección",
        "website": "nuestra web",
        "schedule": "horario comercial habitual",
        "opening_time": "hora de apertura",
        "closing_time": "hora de cierre",
        "today_schedule": "horario de hoy",
        "open_now_status": "Consulta si estamos abiertos",
        "sunday_schedule": "Los domingos tenemos horario especial",
        "weekend_schedule": "Sábados y domingos con horario especial",
        "parking_info": "hay parking disponible cerca",
        "online_booking_info": "Puedes reservar online en nuestra web",
        "payment_methods": "efectivo, tarjeta, bizum y pagos móviles",
        "offers_info": "Tenemos ofertas especiales regularmente",
        "discount_info": "Ofrecemos descuentos para grupos y clientes frecuentes",
        "bizum_info": "Sí, aceptamos Bizum",
        "installment_info": "Consulta opciones de financiación",
        "venue_description": "Nuestro local es amplio y cómodo",
        "terrace_info": "Sí, tenemos terraza",
        "accessibility_info": "Local accesible para personas con movilidad reducida",
        "capacity": "para 50 personas",
        "years_open": "varios",
        "opening_year": "hace años",
        "owner_info": "Negocio familiar",
        "appointment_policy": "Recomendamos cita previa",
        "pet_policy": "Se admiten mascotas",
        "kids_policy": "Los niños son bienvenidos",
        "languages_spoken": "Hablamos español e inglés",
        "gift_card_info": "Sí, tenemos tarjetas regalo disponibles",
        "events_info": "Organizamos eventos y celebraciones",
        "events_types": "cumpleaños, eventos corporativos y celebraciones",
        "social_media": "nuestronegocio",
    }
    
    # Combinar datos del negocio con defaults
    data = {**defaults, **business_data}
    
    # Reemplazar placeholders en el template
    for key, value in data.items():
        template = template.replace(f"{{{key}}}", str(value))
    
    return template

# Función para integrar en el main.py
def enhance_chatbot_with_complete_faqs(business_data: Dict[str, str]) -> List[Tuple[str, str, str, int]]:
    """
    Genera FAQs completas personalizadas para un negocio específico
    """
    global_faqs = get_comprehensive_global_faqs()
    business_responses = get_business_specific_responses(business_data.get("business_type", "restaurant"))
    
    # Combinar datos del negocio con respuestas específicas
    complete_data = {**business_data, **business_responses}
    
    # Formatear todas las respuestas con los datos del negocio
    formatted_faqs = []
    for question, answer_template, category, priority in global_faqs:
        formatted_answer = format_faq_response(answer_template, complete_data)
        formatted_faqs.append((question, formatted_answer, category, priority))
    
    return formatted_faqs

# Ejemplo de uso
if __name__ == "__main__":
    # Datos de ejemplo de un negocio
    example_business = {
        "business_name": "Restaurante La Paella",
        "business_type": "restaurant",
        "phone": "+34 977 123 456",
        "email": "info@lapaella.com",
        "address": "Calle Principal 123, Salou",
        "website": "www.lapaella.com",
        "schedule": "L-V 13:00-23:30, S-D 13:00-00:00",
        "opening_time": "13:00",
        "closing_time": "23:30",
        "capacity": "80 personas",
        "years_open": "15",
        "opening_year": "2009",
    }
    
    # Generar FAQs personalizadas
    personalized_faqs = enhance_chatbot_with_complete_faqs(example_business)
    
    # Mostrar algunas FAQs de ejemplo
    print("=== FAQs PERSONALIZADAS ===")
    for faq in personalized_faqs[:5]:
        print(f"\nP: {faq[0]}")
        print(f"R: {faq[1]}")
        print(f"Categoría: {faq[2]} | Prioridad: {faq[3]}")