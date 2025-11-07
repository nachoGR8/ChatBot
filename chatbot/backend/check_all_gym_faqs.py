"""
Script para revisar todas las FAQs del gimnasio en la base de datos activa
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import SessionLocal, Business, FAQ

def main():
    db = SessionLocal()
    
    try:
        # Buscar el negocio del gimnasio
        gym = db.query(Business).filter(Business.name.like('%Overcome%')).first()
        if not gym:
            gym = db.query(Business).filter(Business.business_type == 'gym').first()
        
        if not gym:
            print("❌ No se encontró el gimnasio")
            return
        
        print(f"🏋️ Gimnasio encontrado: {gym.name} (ID: {gym.id})")
        print(f"=" * 80)
        
        # Obtener TODAS las FAQs
        faqs = db.query(FAQ).filter(FAQ.gym_id == gym.id).all()
        print(f"\n📊 Total FAQs en la base de datos: {len(faqs)}\n")
        
        # Separar por categorías
        categories = {}
        for faq in faqs:
            cat = faq.category or "Sin categoría"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(faq)
        
        # Mostrar por categorías
        for cat, cat_faqs in sorted(categories.items()):
            print(f"\n📁 {cat.upper()} ({len(cat_faqs)} FAQs)")
            print("-" * 80)
            for i, faq in enumerate(cat_faqs, 1):
                print(f"\n{i}. P: {faq.question}")
                print(f"   R: {faq.answer[:200]}...")
        
        # Buscar FAQs relacionadas con normas
        print("\n" + "=" * 80)
        print("🔍 ANÁLISIS: FAQs relacionadas con NORMAS")
        print("=" * 80)
        
        norma_keywords = ['norma', 'regla', 'prohibido', 'obligatorio', 'permitido', 
                         'acceso', 'requisito', 'política', 'fumar', 'alcohol', 'tarjeta',
                         'toalla', 'ducharse', 'reserva', 'clase', 'taquilla', 'ropa',
                         'calzado', 'deportivo', 'pesas', 'máquina', 'grabar', 'fotografiar']
        
        norma_faqs = []
        for faq in faqs:
            text = (faq.question + " " + faq.answer + " " + (faq.category or "")).lower()
            if any(keyword in text for keyword in norma_keywords):
                norma_faqs.append(faq)
        
        print(f"\n✅ Se encontraron {len(norma_faqs)} FAQs relacionadas con normas:\n")
        for i, faq in enumerate(norma_faqs, 1):
            print(f"{i}. [{faq.category}] {faq.question}")
        
        # Normas que deberían existir según el PDF
        print("\n" + "=" * 80)
        print("📋 VERIFICACIÓN: Normas del PDF original")
        print("=" * 80)
        
        expected_normas = [
            "registrar entrada con tarjeta",
            "ropa y calzado deportivo",
            "limpiar y devolver material",
            "no dejar pesas en el suelo",
            "usar toalla en bancos",
            "no bloquear máquinas",
            "prohibido grabar o fotografiar",
            "reservar plaza clase",
            "ducharse antes de spa",
            "informar incidente",
            "mantener taquillas cerradas",
            "no gritar ni lanzar pesas"
        ]
        
        print("\n¿Están estas normas en las FAQs?")
        all_text = " ".join([f.question.lower() + " " + f.answer.lower() for f in faqs])
        
        for norma in expected_normas:
            existe = any(word in all_text for word in norma.split())
            symbol = "✅" if existe else "❌"
            print(f"{symbol} {norma}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
