import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver las últimas 20 FAQs
cursor.execute("""
    SELECT id, category, question, LENGTH(answer) as answer_length
    FROM faqs 
    WHERE business_id = 1 
    ORDER BY id DESC 
    LIMIT 20
""")

faqs = cursor.fetchall()

print("=" * 100)
print("ÚLTIMAS 20 FAQs DEL NEGOCIO")
print("=" * 100)

for faq_id, category, question, answer_len in faqs:
    print(f"\n[{faq_id}] {category}")
    print(f"    Q: {question[:80]}{'...' if len(question) > 80 else ''}")
    print(f"    A: {answer_len} caracteres")

# Ver total
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1")
total = cursor.fetchone()[0]
print(f"\n{'=' * 100}")
print(f"Total FAQs: {total}")
print("=" * 100)

conn.close()
