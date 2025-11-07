import sqlite3

conn = sqlite3.connect('chatbot.db')
cursor = conn.execute("""
    SELECT id, question, answer 
    FROM faqs 
    WHERE question LIKE '%menu%' OR answer LIKE '%Paella%'
""")

rows = cursor.fetchall()
for r in rows:
    print(f"\n=== FAQ ID: {r[0]} ===")
    print(f"Pregunta: {r[1]}")
    print(f"Respuesta ({len(r[2])} caracteres):")
    print(r[2])
    print("\n" + "="*80)

conn.close()
