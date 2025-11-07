"""Script para limpiar FAQs que tienen [Fuente: ...] duplicadas."""
import re
from app.database import SessionLocal
from app.models import FAQ

db = SessionLocal()

try:
    # Obtener todas las FAQs
    faqs = db.query(FAQ).all()
    print(f"📊 Total FAQs en BD: {len(faqs)}\n")
    
    cleaned_count = 0
    for faq in faqs:
        original_answer = faq.answer
        
        # Eliminar [Fuente: ...] del final
        cleaned_answer = re.sub(r'\n*\s*\[Fuente:.*?\]\s*$', '', original_answer, flags=re.IGNORECASE)
        
        if cleaned_answer != original_answer:
            print(f"🧹 Limpiando FAQ {faq.id}: {faq.question[:60]}...")
            print(f"   Antes: {len(original_answer)} caracteres")
            print(f"   Después: {len(cleaned_answer)} caracteres")
            
            faq.answer = cleaned_answer
            cleaned_count += 1
    
    if cleaned_count > 0:
        db.commit()
        print(f"\n✅ {cleaned_count} FAQs limpiadas exitosamente")
    else:
        print("\n✅ No hay FAQs para limpiar")
        
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
