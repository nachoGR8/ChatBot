import sqlite3

conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Ver todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tablas en la base de datos:")
for table in tables:
    print(f"  - {table[0]}")
    
    # Ver cuántos registros tiene cada tabla
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"    Registros: {count}")

conn.close()
