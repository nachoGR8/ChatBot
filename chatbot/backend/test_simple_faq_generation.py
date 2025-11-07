"""Test simple de generación de FAQs sin subir documento."""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.document_service import document_service
from app.database import SessionLocal
from app.models import Business, FAQ

# Texto de ejemplo de un gimnasio
SAMPLE_TEXT = """
GIMNASIO FITNESS PLUS - INFORMACIÓN GENERAL

Horarios de Atención:
Lunes a Viernes: 6:00 AM - 10:00 PM
Sábados: 8:00 AM - 8:00 PM
Domingos: 8:00 AM - 6:00 PM

Instalaciones:
- Área de pesas y máquinas de última generación
- Zona de cardio con 30 máquinas
- 2 salas de clases grupales
- Vestuarios con duchas y casilleros
- Área de estiramiento y yoga
- Cafetería saludable

Clases Grupales:
- Spinning: Lunes, Miércoles y Viernes 7:00 AM y 7:00 PM
- Yoga: Martes y Jueves 6:30 AM y 8:00 PM
- CrossFit: Lunes a Viernes 6:00 PM
- Zumba: Martes y Jueves 7:00 PM
- Pilates: Miércoles y Viernes 9:00 AM

Planes y Precios:
- Plan Básico: $30/mes - Acceso al gimnasio
- Plan Premium: $50/mes - Gimnasio + todas las clases
- Plan VIP: $70/mes - Todo incluido + entrenador personal (2 sesiones/mes)
- Pase diario: $8

Servicios Adicionales:
- Entrenador personal: $25 por sesión
- Nutricionista: $40 por consulta
- Masajes deportivos: $35 por sesión
- Evaluación física completa: $15

Políticas:
- Inscripción sin matrícula
- Cancela cuando quieras con 30 días de aviso
- Traer toalla es obligatorio
- Máximo 2 invitados por mes (solo plan VIP)
- No se permiten niños menores de 16 años sin supervisión

Contacto:
Teléfono: (555) 123-4567
Email: info@fitnessplus.com
Dirección: Av. Principal 456, Centro
Web: www.fitnessplus.com

Promoción Actual:
¡Inscríbete este mes y obtén el primer mes con 50% de descuento!
Incluye evaluación física gratuita.
"""

def main():
    print("=" * 70)
    print("PRUEBA SIMPLE DE GENERACIÓN AUTOMÁTICA DE FAQs")
    print("=" * 70)
    print()
    
    db = SessionLocal()
    try:
        # Obtener o crear negocio
        business = db.query(Business).filter(Business.id == 1).first()
        if not business:
            print("Creando negocio de prueba...")
            business = Business(
                name="Gimnasio Fitness Plus",
                business_type="gym",
                phone="(555) 123-4567",
                email="info@fitnessplus.com",
            )
            db.add(business)
            db.commit()
            db.refresh(business)
        
        print(f"✓ Usando negocio: {business.name} (ID: {business.id})")
        print()
        
        # Generar FAQs
        print("🤖 Generando FAQs automáticamente...")
        print("⏳ Esto puede tomar 1-2 minutos dependiendo del hardware...")
        print()
        
        faqs = document_service._generate_faqs_from_text(SAMPLE_TEXT, business)
        
        if not faqs:
            print("❌ No se generaron FAQs.")
            print("   Verifica que el modelo LLM esté disponible y funcionando.")
            return
        
        print(f"✅ ¡Se generaron {len(faqs)} FAQs!")
        print()
        print("-" * 70)
        
        # Mostrar las FAQs generadas
        for idx, faq in enumerate(faqs, 1):
            print(f"\n📌 FAQ #{idx}")
            print(f"   Categoría: [{faq['category']}]")
            print(f"   Pregunta: {faq['question']}")
            print(f"   Respuesta: {faq['answer'][:150]}{'...' if len(faq['answer']) > 150 else ''}")
        
        print()
        print("-" * 70)
        
        # Preguntar si guardar
        response = input("\n¿Guardar estas FAQs en la base de datos? (s/n): ").strip().lower()
        
        if response == 's':
            saved = document_service._save_generated_faqs(db, faqs, business, 999)
            print(f"\n✅ Se guardaron {saved} FAQs en la base de datos")
            
            # Mostrar todas las FAQs del negocio
            print("\n📋 FAQs totales del negocio:")
            all_faqs = db.query(FAQ).filter(FAQ.business_id == business.id).all()
            print(f"   Total: {len(all_faqs)} FAQs")
            
            if saved > 0:
                print("\n   Últimas FAQs agregadas:")
                for faq in all_faqs[-saved:]:
                    print(f"   - {faq.question[:60]}...")
        else:
            print("\n⏭️  FAQs no guardadas")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print()
    print("=" * 70)
    print("PRUEBA COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
