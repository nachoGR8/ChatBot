import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Contar todas las FAQs del negocio 1
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1")
total = cursor.fetchone()[0]
print(f"📊 Total FAQs del negocio 1: {total}\n")

# Obtener las últimas 15 FAQs
cursor.execute("""
    SELECT id, question, category, priority, created_at
    FROM faqs 
    WHERE business_id = 1 
    ORDER BY id DESC 
    LIMIT 15
""")

print("=" * 80)
print("ÚLTIMAS 15 FAQs CREADAS")
print("=" * 80)

for i, (faq_id, question, category, priority, created_at) in enumerate(cursor.fetchall(), 1):
    q_preview = question[:70] + "..." if len(question) > 70 else question
    print(f"\n{i}. [ID: {faq_id}] (Pri: {priority}, Cat: {category})")
    print(f"   📅 {created_at}")
    print(f"   ❓ {q_preview}")

conn.close()
