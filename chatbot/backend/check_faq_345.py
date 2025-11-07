"""Verificar FAQ 345 y otros FAQs con prioridad alta."""
import sqlite3

conn = sqlite3.connect('chatbot.db')

# Buscar FAQ 345
print("=" * 80)
print("🔍 Buscando FAQ 345:")
print("=" * 80)
result = conn.execute("SELECT id, business_id, priority, question FROM faqs WHERE id = 345").fetchone()
if result:
    print(f"ID: {result[0]}")
    print(f"Business ID: {result[1]}")
    print(f"Priority: {result[2]}")
    print(f"Question: {result[3][:100]}...")
else:
    print("❌ FAQ 345 NO EXISTE")

print("\n" + "=" * 80)
print("🔍 Buscando todos los FAQs con prioridad >= 100:")
print("=" * 80)
results = conn.execute("SELECT id, business_id, priority, question FROM faqs WHERE priority >= 100").fetchall()
if results:
    for row in results:
        print(f"\nID: {row[0]}")
        print(f"Business ID: {row[1]}")
        print(f"Priority: {row[2]}")
        print(f"Question: {row[3][:80]}...")
else:
    print("❌ NO HAY FAQs con prioridad >= 100")

print("\n" + "=" * 80)
print("🔍 Todos los FAQs para business_id=1:")
print("=" * 80)
results = conn.execute("""
    SELECT id, priority, category, substr(question, 1, 60) as question 
    FROM faqs 
    WHERE business_id = 1 
    ORDER BY priority DESC, id DESC
""").fetchall()
print(f"Total: {len(results)} FAQs")
for row in results[:20]:  # Mostrar primeros 20
    print(f"  ID {row[0]:<5} | Priority {row[1]:<3} | Category: {row[2]:<15} | {row[3]}")

conn.close()
