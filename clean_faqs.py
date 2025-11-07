import sqlite3
import re

# Conectar a la base de datos correcta (la que usa el backend)
conn = sqlite3.connect('chatbot/chatbot.db')
c = conn.cursor()

# Obtener todas las FAQs
faqs = c.execute('SELECT id, question, answer FROM faqs').fetchall()
print(f"📊 Total FAQs: {len(faqs)}\n")

cleaned_count = 0
for faq_id, question, answer in faqs:
    original_answer = answer
    cleaned_answer = answer
    
    # Limpiar [Fuente: ...] del final
    cleaned_answer = re.sub(r'\n*\s*\[Fuente:.*?\]\s*$', '', cleaned_answer, flags=re.IGNORECASE)
    
    # Limpiar pipes sueltos al final (basura del PDF)
    # Ejemplo: | | | | | | | | | al final
    cleaned_answer = re.sub(r'(\|\s*){5,}$', '', cleaned_answer, flags=re.MULTILINE)
    
    # Limpiar líneas que solo tienen pipes
    cleaned_answer = re.sub(r'\n(\|\s*)+\n', '\n', cleaned_answer)
    
    # Limpiar múltiples saltos de línea al final
    cleaned_answer = cleaned_answer.rstrip() + '\n' if cleaned_answer.strip() else ''
    
    if cleaned_answer != original_answer:
        print(f"🧹 Limpiando FAQ {faq_id}")
        print(f"   Pregunta: {question[:60]}...")
        print(f"   Antes: {len(original_answer)} caracteres")
        print(f"   Después: {len(cleaned_answer)} caracteres")
        
        # Mostrar qué se eliminó
        removed = len(original_answer) - len(cleaned_answer)
        print(f"   Eliminados: {removed} caracteres de basura\n")
        
        c.execute('UPDATE faqs SET answer = ? WHERE id = ?', (cleaned_answer, faq_id))
        cleaned_count += 1

# Guardar cambios
conn.commit()
conn.close()

print(f"\n✅ {cleaned_count} FAQs limpiadas exitosamente")
