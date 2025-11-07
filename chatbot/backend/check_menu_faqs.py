import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Contar FAQs de menú
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1 AND category = 'menú'")
count = cursor.fetchone()[0]
print(f"📊 Total FAQs de menú: {count}\n")

# Obtener preguntas de menú
cursor.execute("""
    SELECT id, question, created_at
    FROM faqs 
    WHERE business_id = 1 AND category = 'menú'
    ORDER BY id DESC 
    LIMIT 10
""")

faqs = cursor.fetchall()

print("🍽️  FAQs DE MENÚ CREADAS:")
print("=" * 80)
for i, (faq_id, question, created_at) in enumerate(faqs, 1):
    print(f"\n{i}. [ID: {faq_id}] {created_at[:19]}")
    print(f"   ❓ {question}")

conn.close()
