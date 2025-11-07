"""Script de prueba para verificar la generación automática de FAQs desde documentos."""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.document_service import document_service
from app.database import SessionLocal
from app.models import Business, FAQ

def test_faq_generation():
    """Prueba la generación de FAQs desde un texto de ejemplo."""
    
    # Texto de ejemplo (simulando un documento de un restaurante)
    sample_text = """
    Bienvenidos a Restaurante El Sabor
    
    Horarios de Atención:
    Lunes a Viernes: 12:00 PM - 10:00 PM
    Sábados y Domingos: 11:00 AM - 11:00 PM
    
    Especialidades:
    - Paella Valenciana: Nuestra especialidad de la casa, preparada con mariscos frescos y azafrán auténtico.
    - Tapas Variadas: Selección de tapas españolas tradicionales.
    - Sangría de la Casa: Bebida refrescante preparada con frutas frescas.
    
    Servicios:
    - Reservas: Aceptamos reservas con 24 horas de anticipación
    - Delivery: Servicio a domicilio disponible en un radio de 5km
    - Eventos: Organizamos eventos privados para hasta 50 personas
    
    Información de Contacto:
    Teléfono: +34 123 456 789
    Email: info@elsabor.com
    Dirección: Calle Mayor 123, Madrid
    
    Políticas:
    - Los niños son bienvenidos, contamos con menú infantil
    - No permitimos mascotas en el interior
    - Aceptamos pagos en efectivo y tarjeta
    """
    
    print("=" * 60)
    print("PRUEBA DE GENERACIÓN AUTOMÁTICA DE FAQs")
    print("=" * 60)
    print()
    
    # Crear un negocio de prueba
    db = SessionLocal()
    try:
        business = db.query(Business).filter(Business.id == 1).first()
        
        if not business:
            print("Creando negocio de prueba...")
            business = Business(
                name="Restaurante El Sabor",
                business_type="restaurant",
                phone="+34 123 456 789",
                email="info@elsabor.com",
            )
            db.add(business)
            db.commit()
            db.refresh(business)
        
        print(f"Usando negocio: {business.name} (ID: {business.id})")
        print()
        
        # Generar FAQs
        print("Generando FAQs desde el texto...")
        print("-" * 60)
        
        faqs = document_service._generate_faqs_from_text(sample_text, business)
        
        if not faqs:
            print("⚠️  No se generaron FAQs. Verifica que el modelo LLM esté disponible.")
            return
        
        print(f"✓ Se generaron {len(faqs)} FAQs\n")
        
        # Mostrar las FAQs generadas
        for idx, faq in enumerate(faqs, 1):
            print(f"FAQ #{idx}")
            print(f"Categoría: {faq['category']}")
            print(f"Pregunta: {faq['question']}")
            print(f"Respuesta: {faq['answer']}")
            print("-" * 60)
        
        # Preguntar si guardar en la base de datos
        response = input("\n¿Deseas guardar estas FAQs en la base de datos? (s/n): ").lower()
        
        if response == 's':
            saved = document_service._save_generated_faqs(db, faqs, business, 0)
            print(f"\n✓ Se guardaron {saved} FAQs en la base de datos")
            
            # Mostrar FAQs guardadas
            print("\nFAQs en la base de datos para este negocio:")
            all_faqs = db.query(FAQ).filter(FAQ.business_id == business.id).all()
            for faq in all_faqs[-saved:]:  # Mostrar solo las últimas guardadas
                print(f"- {faq.question[:80]}...")
        else:
            print("\nNo se guardaron las FAQs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print()
    print("=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    test_faq_generation()
