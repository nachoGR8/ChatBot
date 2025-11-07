import sqlite3

db_path = r"c:\Users\nacho\Desktop\chatbot\chatbot\chatbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Contar FAQs antes
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1")
before = cursor.fetchone()[0]
print(f"📊 FAQs antes: {before}")

# Eliminar TODAS las FAQs del negocio 1
cursor.execute("DELETE FROM faqs WHERE business_id = 1")
conn.commit()

deleted = cursor.rowcount
print(f"🗑️  FAQs eliminadas: {deleted}")

# Verificar
cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1")
after = cursor.fetchone()[0]
print(f"📊 FAQs después: {after}")
print(f"\n✅ Listo para generar FAQs frescas")

conn.close()
