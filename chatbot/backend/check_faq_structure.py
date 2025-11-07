import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver estructura de la tabla faqs
cursor.execute("PRAGMA table_info(faqs)")
columns = cursor.fetchall()

print("Columnas de la tabla 'faqs':")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
