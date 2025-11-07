import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

business_id = 2  # Overcome

print("=" * 80)
print("ELIMINANDO FAQs ACTUALES DE OVERCOME")
print("=" * 80)

cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = ?", (business_id,))
count_before = cursor.fetchone()[0]
print(f"FAQs antes: {count_before}")

cursor.execute("DELETE FROM faqs WHERE business_id = ?", (business_id,))
conn.commit()

print(f"✅ {count_before} FAQs eliminadas")
print("\n💡 Ahora vuelve a subir el PDF desde admin.html para regenerar las FAQs mejoradas")

conn.close()
