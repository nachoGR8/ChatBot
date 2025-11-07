import sqlite3

conn = sqlite3.connect('chatbot.db')

# Ver todas las tablas
print("=== TABLAS EN LA BASE DE DATOS ===")
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(tables)

# Ver estructura de cada tabla
for table in tables:
    print(f"\n=== Estructura de {table} ===")
    cursor = conn.execute(f"PRAGMA table_info({table})")
    for row in cursor:
        print(f"  {row[1]} ({row[2]})")
    
    # Contar registros
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  Total registros: {count}")

conn.close()
