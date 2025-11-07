"""Test de la lógica de detección del FAQ de menú"""
import sqlite3

conn = sqlite3.connect('chatbot.db')

print("=== FAQs CON PRIORIDAD >= 100 ===\n")
cursor = conn.execute("""
    SELECT id, priority, question, LENGTH(answer) as len
    FROM faqs 
    WHERE business_id = 1 AND priority >= 100
    ORDER BY priority DESC
""")

for row in cursor:
    print(f"ID: {row[0]} | Prioridad: {row[1]}")
    print(f"Pregunta: {row[2]}")
    print(f"Longitud respuesta: {row[3]} caracteres")
    
    # Verificar keywords
    keywords = ['menú', 'menu', 'platos', 'carta']
    found_keywords = [k for k in keywords if k in row[2].lower()]
    print(f"Keywords encontrados: {found_keywords}")
    print("-" * 80 + "\n")

conn.close()
