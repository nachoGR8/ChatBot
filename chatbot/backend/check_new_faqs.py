import sqlite3

conn = sqlite3.connect('chatbot.db')

print("=== ÚLTIMAS 20 FAQs (más recientes primero) ===\n")
cursor = conn.execute("""
    SELECT id, question, answer, created_at
    FROM faqs 
    WHERE business_id = 1
    ORDER BY id DESC 
    LIMIT 20
""")

for row in cursor:
    print(f"ID: {row[0]} | Fecha: {row[3]}")
    print(f"P: {row[1]}")
    print(f"R: {row[2][:200]}...")
    print("-" * 80 + "\n")

conn.close()
