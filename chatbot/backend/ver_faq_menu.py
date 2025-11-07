import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buscar FAQ del menú
cursor.execute("""
    SELECT id, question, answer, priority, category
    FROM faqs 
    WHERE business_id = 1 AND category = 'menú'
    ORDER BY id DESC 
    LIMIT 1
""")

faq = cursor.fetchone()

if faq:
    faq_id, question, answer, priority, category = faq
    print("=" * 80)
    print("FAQ DEL MENÚ ENCONTRADA")
    print("=" * 80)
    print(f"\n📌 ID: {faq_id}")
    print(f"❓ Pregunta: {question}")
    print(f"⭐ Prioridad: {priority}")
    print(f"🏷️  Categoría: {category}")
    print(f"\n💬 Respuesta ({len(answer)} caracteres):")
    print("-" * 80)
    print(answer)
    print("-" * 80)
else:
    print("❌ No se encontró FAQ del menú")

conn.close()
