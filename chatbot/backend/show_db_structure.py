import sqlite3

conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tablas en chatbot.db:')
for t in tables:
    print(f'  - {t[0]}')
    
    # Ver estructura
    cursor.execute(f'PRAGMA table_info({t[0]})')
    columns = cursor.fetchall()
    for col in columns:
        print(f'      {col[1]} ({col[2]})')
    print()

conn.close()
