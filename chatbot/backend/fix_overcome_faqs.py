import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ID del negocio Overcome
business_id = 2

# Primero, eliminar las FAQs existentes mal generadas
print("🗑️ Eliminando FAQs mal generadas...")
cursor.execute("DELETE FROM faqs WHERE business_id = ?", (business_id,))
print(f"✅ {cursor.rowcount} FAQs eliminadas")

# Ahora, crear FAQs completas y de calidad basadas en el PDF
faqs_correctas = [
    # NORMAS GENERALES
    {
        "question": "¿Quién puede acceder al gimnasio Overcome?",
        "answer": "El acceso está reservado exclusivamente a socios activos de Overcome. Es obligatorio registrar la entrada con tu tarjeta de socio.",
        "category": "acceso",
        "priority": 10
    },
    {
        "question": "¿Qué necesito para entrar al gimnasio?",
        "answer": "Necesitas tu tarjeta de socio activa para registrar la entrada. Es obligatorio presentarla en recepción.",
        "category": "acceso",
        "priority": 10
    },
    {
        "question": "¿Puedo fumar o consumir alcohol en Overcome?",
        "answer": "No, está completamente prohibido fumar o consumir alcohol en todas las instalaciones del gimnasio.",
        "category": "normas",
        "priority": 8
    },
    {
        "question": "¿Qué ropa debo usar en el gimnasio?",
        "answer": "Es obligatorio usar ropa y calzado deportivo en todas las instalaciones. No se permite el acceso con ropa de calle o calzado inadecuado.",
        "category": "normas",
        "priority": 9
    },
    {
        "question": "¿Puedo entrar si he bebido alcohol?",
        "answer": "No, no se permite el acceso al gimnasio bajo los efectos del alcohol o drogas. Esto es por tu seguridad y la de los demás socios.",
        "category": "normas",
        "priority": 8
    },
    
    # USO DE INSTALACIONES
    {
        "question": "¿Qué debo hacer después de usar las máquinas o pesas?",
        "answer": "Es obligatorio limpiar y devolver todo el material tras su uso. No dejes pesas ni barras tiradas en el suelo, siempre devuélvelas a su sitio.",
        "category": "instalaciones",
        "priority": 9
    },
    {
        "question": "¿Tengo que llevar toalla al gimnasio?",
        "answer": "Sí, es obligatorio usar siempre una toalla en bancos y máquinas por higiene. Esto ayuda a mantener las instalaciones limpias para todos.",
        "category": "higiene",
        "priority": 9
    },
    {
        "question": "¿Cuánto tiempo puedo usar una máquina?",
        "answer": "Evita bloquear las máquinas más de 30 minutos en horas punta para que todos los socios puedan entrenar. Si el gimnasio está tranquilo, no hay problema en usarlas más tiempo.",
        "category": "instalaciones",
        "priority": 7
    },
    {
        "question": "¿Puedo tomar fotos o vídeos en el gimnasio?",
        "answer": "Está prohibido grabar o fotografiar a otros socios sin su consentimiento expreso. Respeta la privacidad de los demás.",
        "category": "normas",
        "priority": 8
    },
    
    # CLASES DIRIGIDAS
    {
        "question": "¿Cómo reservo una clase dirigida?",
        "answer": "Puedes reservar tu plaza con antelación mediante la app de Overcome o directamente en recepción. Es importante hacerlo antes para asegurar tu sitio.",
        "category": "clases",
        "priority": 10
    },
    {
        "question": "¿Puedo entrar a una clase si llego tarde?",
        "answer": "No, no se permite el acceso a las clases una vez iniciadas. Esto evita interrumpir al instructor y a los demás participantes.",
        "category": "clases",
        "priority": 8
    },
    {
        "question": "¿Qué hago si reservé una clase pero no puedo ir?",
        "answer": "Debes cancelar tu asistencia a través de la app o en recepción para liberar tu plaza. Así otro socio puede aprovecharla.",
        "category": "clases",
        "priority": 9
    },
    
    # HIGIENE Y SEGURIDAD
    {
        "question": "¿Tengo que ducharme antes de usar el spa?",
        "answer": "Sí, es obligatorio ducharse antes de usar la zona de spa por razones de higiene. Esto mantiene el agua limpia y saludable para todos.",
        "category": "higiene",
        "priority": 8
    },
    {
        "question": "¿Qué hago si me lesiono o tengo un accidente en el gimnasio?",
        "answer": "Informa inmediatamente de cualquier incidente o lesión al personal del gimnasio. Estamos aquí para ayudarte y registrar el incidente.",
        "category": "seguridad",
        "priority": 10
    },
    {
        "question": "¿Puedo dejar objetos de valor en la taquilla?",
        "answer": "Mantén las taquillas cerradas con candado, pero ten en cuenta que Overcome no se hace responsable de pérdidas o robos. Evita dejar objetos de mucho valor.",
        "category": "seguridad",
        "priority": 7
    },
    {
        "question": "¿Qué pasa si pierdo algo en el gimnasio?",
        "answer": "Puedes preguntar en recepción por objetos perdidos, pero Overcome no se hace responsable de pérdidas o robos en las instalaciones.",
        "category": "seguridad",
        "priority": 6
    },
    
    # CONDUCTA
    {
        "question": "¿Cómo debo comportarme con el personal y otros socios?",
        "answer": "Trata al personal y a los demás socios con respeto en todo momento. Somos una comunidad y el respeto mutuo es fundamental.",
        "category": "conducta",
        "priority": 10
    },
    {
        "question": "¿Puedo hacer ruido mientras entreno?",
        "answer": "Evita gritar o lanzar pesas al suelo. Un poco de ruido es normal al entrenar, pero el ruido excesivo molesta a otros socios.",
        "category": "conducta",
        "priority": 7
    },
    {
        "question": "¿Qué pasa si no respeto las normas del gimnasio?",
        "answer": "Cualquier comportamiento inapropiado puede suponer la expulsión temporal o definitiva del centro. Queremos mantener un ambiente seguro y respetuoso para todos.",
        "category": "conducta",
        "priority": 9
    },
    
    # INFORMACIÓN GENERAL
    {
        "question": "¿Cuál es la filosofía de Overcome?",
        "answer": "Nuestro compromiso es ayudarte a conseguir tus objetivos en un entorno seguro, saludable y motivador. Estamos aquí para apoyarte en tu viaje fitness.",
        "category": "general",
        "priority": 5
    },
    {
        "question": "¿Qué debo hacer si tengo dudas sobre las normas?",
        "answer": "Puedes consultar con el personal en recepción en cualquier momento. Estamos aquí para resolver tus dudas y ayudarte.",
        "category": "general",
        "priority": 6
    }
]

# Insertar las nuevas FAQs
print(f"\n✨ Generando {len(faqs_correctas)} FAQs mejoradas...")
for faq in faqs_correctas:
    cursor.execute("""
        INSERT INTO faqs (business_id, question, answer, category, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        business_id,
        faq["question"],
        faq["answer"],
        faq["category"],
        faq["priority"],
        datetime.now().isoformat()
    ))

conn.commit()
print(f"✅ {len(faqs_correctas)} FAQs insertadas correctamente")

# Verificar
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = ?", (business_id,))
total = cursor.fetchone()[0]
print(f"\n📊 Total FAQs ahora en la base de datos: {total}")

# Mostrar por categorías
cursor.execute("""
    SELECT category, COUNT(*) as total
    FROM faqs
    WHERE business_id = ?
    GROUP BY category
    ORDER BY total DESC
""", (business_id,))

categories = cursor.fetchall()
print("\n📁 FAQs por categoría:")
for cat in categories:
    print(f"   - {cat[0]}: {cat[1]} FAQs")

conn.close()
print("\n✅ ¡Proceso completado!")
