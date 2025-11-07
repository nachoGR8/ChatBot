import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Eliminar FAQs de menú anteriores
cursor.execute("DELETE FROM faqs WHERE business_id = 1 AND category = 'menú'")
deleted_count = cursor.rowcount
conn.commit()

print(f"✅ Eliminadas {deleted_count} FAQs de menú antiguas")

# Contar FAQs restantes
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1")
total = cursor.fetchone()[0]
print(f"📊 FAQs restantes del negocio 1: {total}")

conn.close()
