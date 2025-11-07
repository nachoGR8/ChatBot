"""Diagnóstico: simular la query de FAQs exactamente como la hace el endpoint."""
import sys
sys.path.append(".")

from app.database import SessionLocal
from app.models import FAQ

db = SessionLocal()

business_id = 1

print("=" * 80)
print("🔍 Simulando query de FAQs del endpoint /chat")
print("=" * 80)

# Exactamente la misma query que en chat.py línea 29
faqs = db.query(FAQ).filter(FAQ.business_id == business_id).all()

print(f"\nTotal FAQs obtenidos: {len(faqs)}")

# Filtrar los de menú con prioridad >= 100
menu_faqs = [f for f in faqs if f.priority >= 100 and 
             any(keyword in f.question.lower() for keyword in ['menú', 'menu', 'platos', 'carta'])]

print(f"FAQs de menú con prioridad >= 100: {len(menu_faqs)}")

if menu_faqs:
    print("\n" + "=" * 80)
    print("📋 FAQs de menú encontrados:")
    print("=" * 80)
    for faq in menu_faqs:
        print(f"\nID: {faq.id}")
        print(f"Priority: {faq.priority}")
        print(f"Question: {faq.question}")
        print(f"Answer preview: {faq.answer[:200]}...")

# Mostrar distribución de prioridades
print("\n" + "=" * 80)
print("📊 Distribución de prioridades:")
print("=" * 80)
from collections import Counter
priorities = Counter(f.priority for f in faqs)
for priority in sorted(priorities.keys(), reverse=True):
    count = priorities[priority]
    print(f"  Priority {priority}: {count} FAQs")

db.close()
