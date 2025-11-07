"""Ver las últimas FAQs generadas y verificar mejoras."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import FAQ, Business

db = SessionLocal()

try:
    # Obtener el negocio
    business = db.query(Business).filter(Business.id == 1).first()
    
    print("=" * 80)
    print(f"FAQs DEL NEGOCIO: {business.name}")
    print("=" * 80)
    print()
    
    # Obtener todas las FAQs ordenadas por fecha de creación
    faqs = db.query(FAQ).filter(
        FAQ.business_id == 1
    ).order_by(FAQ.created_at.desc()).all()
    
    print(f"Total de FAQs en la base de datos: {len(faqs)}")
    print()
    
    # Agrupar por categoría
    by_category = {}
    for faq in faqs:
        cat = faq.category or "sin categoría"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(faq)
    
    print("📊 FAQs por categoría:")
    print("-" * 80)
    for cat, cat_faqs in sorted(by_category.items()):
        print(f"\n🏷️  {cat.upper()} ({len(cat_faqs)} FAQs)")
        print("-" * 80)
        
        for idx, faq in enumerate(cat_faqs, 1):
            print(f"\n{idx}. Pregunta: {faq.question}")
            print(f"   Prioridad: {faq.priority}")
            
            # Mostrar respuesta (limitada)
            answer = faq.answer
            if len(answer) > 200:
                answer = answer[:200] + "..."
            print(f"   Respuesta: {answer}")
    
    # Buscar FAQ especial del menú
    menu_faq = next((f for f in faqs if "menú" in f.question.lower() or "platos" in f.question.lower()), None)
    
    if menu_faq:
        print("\n" + "=" * 80)
        print("🍽️  FAQ ESPECIAL DE MENÚ DETECTADA")
        print("=" * 80)
        print(f"Pregunta: {menu_faq.question}")
        print(f"Categoría: {menu_faq.category}")
        print(f"Prioridad: {menu_faq.priority}")
        print(f"\nRespuesta completa:")
        print(menu_faq.answer)
    else:
        print("\n⚠️  No se detectó FAQ especial de menú")
    
    # Detectar posibles duplicados
    print("\n" + "=" * 80)
    print("🔍 ANÁLISIS DE DUPLICADOS")
    print("=" * 80)
    
    questions = [faq.question.lower().strip('¿?').strip() for faq in faqs]
    duplicates_found = False
    
    for i, q1 in enumerate(questions):
        for j, q2 in enumerate(questions[i+1:], i+1):
            words1 = set(q1.split())
            words2 = set(q2.split())
            if words1 and words2:
                common = words1.intersection(words2)
                similarity = len(common) / max(len(words1), len(words2))
                if similarity > 0.7:
                    duplicates_found = True
                    print(f"\n⚠️  Posible duplicado ({similarity*100:.1f}% similar):")
                    print(f"   1. {faqs[i].question}")
                    print(f"   2. {faqs[j].question}")
    
    if not duplicates_found:
        print("\n✅ No se encontraron duplicados (similitud > 70%)")
    
finally:
    db.close()

print("\n" + "=" * 80)
