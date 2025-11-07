"""Consulta directa a la base de datos para verificar FAQs."""
import sys
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import FAQ

# Crear sesión de DB
db = SessionLocal()

try:
    # Consultar FAQs para business_id=1
    faqs = db.query(FAQ).filter(FAQ.business_id == 1).all()
    
    print("=" * 80)
    print(f"📊 CONSULTA DIRECTA A LA BASE DE DATOS")
    print("=" * 80)
    print(f"\nTotal FAQs para business_id=1: {len(faqs)}")
    
    # Filtrar FAQs de menú con prioridad >= 100
    menu_faqs = [f for f in faqs if f.priority >= 100 and 
                 any(keyword in f.question.lower() for keyword in ['menú', 'menu', 'platos', 'carta'])]
    
    print(f"FAQs de menú con prioridad >= 100: {len(menu_faqs)}")
    
    if menu_faqs:
        print("\n" + "=" * 80)
        print("🎯 FAQs DE MENÚ CON ALTA PRIORIDAD:")
        print("=" * 80)
        for faq in menu_faqs:
            print(f"\nID: {faq.id}")
            print(f"Priority: {faq.priority}")
            print(f"Question: {faq.question[:80]}")
            print(f"Answer (primeros 150 chars): {faq.answer[:150]}...")
    else:
        print("\n❌ NO SE ENCONTRARON FAQs de menú con prioridad >= 100")
    
    # Mostrar distribución de prioridades
    print("\n" + "=" * 80)
    print("📊 DISTRIBUCIÓN DE PRIORIDADES:")
    print("=" * 80)
    priority_counts = {}
    for faq in faqs:
        priority_counts[faq.priority] = priority_counts.get(faq.priority, 0) + 1
    
    for priority in sorted(priority_counts.keys(), reverse=True):
        print(f"  Priority {priority}: {priority_counts[priority]} FAQs")

finally:
    db.close()
