"""Script para probar la generación de FAQs con un documento real."""
import os
import sys
import requests
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def create_test_pdf():
    """Crea un PDF de prueba usando reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        print("⚠️  reportlab no está instalado.")
        print("   Instalando reportlab...")
        os.system("pip install reportlab")
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    
    output_file = "test_gym_faqs.pdf"
    
    # Crear el PDF
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    
    # Título
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "GIMNASIO FITNESS PLUS")
    
    # Contenido
    c.setFont("Helvetica", 12)
    y = height - 100
    
    content = [
        "",
        "BIENVENIDOS A FITNESS PLUS",
        "",
        "Horarios de Atención:",
        "Lunes a Viernes: 6:00 AM - 10:00 PM",
        "Sábados: 8:00 AM - 8:00 PM",
        "Domingos: 8:00 AM - 6:00 PM",
        "",
        "Instalaciones:",
        "- Área de pesas y máquinas de última generación",
        "- Zona de cardio con 30 máquinas",
        "- 2 salas de clases grupales",
        "- Vestuarios con duchas y casilleros",
        "- Área de estiramiento y yoga",
        "- Cafetería saludable",
        "",
        "Clases Grupales:",
        "- Spinning: Lunes, Miércoles y Viernes 7:00 AM y 7:00 PM",
        "- Yoga: Martes y Jueves 6:30 AM y 8:00 PM",
        "- CrossFit: Lunes a Viernes 6:00 PM",
        "- Zumba: Martes y Jueves 7:00 PM",
        "- Pilates: Miércoles y Viernes 9:00 AM",
        "",
        "Planes y Precios:",
        "- Plan Básico: $30/mes - Acceso al gimnasio",
        "- Plan Premium: $50/mes - Gimnasio + todas las clases",
        "- Plan VIP: $70/mes - Todo incluido + entrenador personal (2 sesiones/mes)",
        "- Pase diario: $8",
        "",
        "Servicios Adicionales:",
        "- Entrenador personal: $25 por sesión",
        "- Nutricionista: $40 por consulta",
        "- Masajes deportivos: $35 por sesión",
        "- Evaluación física completa: $15",
        "",
        "Políticas:",
        "- Inscripción sin matrícula",
        "- Cancela cuando quieras con 30 días de aviso",
        "- Traer toalla es obligatorio",
        "- Máximo 2 invitados por mes (solo plan VIP)",
        "- No se permiten niños menores de 16 años sin supervisión",
        "",
        "Contacto:",
        "Teléfono: (555) 123-4567",
        "Email: info@fitnessplus.com",
        "Dirección: Av. Principal 456, Centro",
        "Web: www.fitnessplus.com",
        "",
        "Promoción Actual:",
        "¡Inscríbete este mes y obtén el primer mes con 50% de descuento!",
        "Incluye evaluación física gratuita.",
    ]
    
    for line in content:
        if y < 50:  # Nueva página si es necesario
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50
        c.drawString(50, y, line)
        y -= 15
    
    c.save()
    return output_file

def upload_document_to_api(pdf_file, business_id=1):
    """Sube el documento a la API."""
    
    # Configuración
    API_URL = "http://localhost:8000/api/train-ia"
    API_KEY = os.getenv("ADMIN_API_KEY", "nacho123")  # API Key por defecto
    
    print("\n" + "="*70)
    print("PRUEBA DE GENERACIÓN AUTOMÁTICA DE FAQs CON DOCUMENTO REAL")
    print("="*70)
    print()
    
    # Verificar que el archivo existe
    if not os.path.exists(pdf_file):
        print(f"❌ El archivo {pdf_file} no existe")
        return
    
    file_size = os.path.getsize(pdf_file)
    print(f"📄 Archivo: {pdf_file}")
    print(f"📊 Tamaño: {file_size:,} bytes")
    print(f"🏢 Negocio ID: {business_id}")
    if API_KEY:
        print(f"🔑 Usando API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    else:
        print("🔓 Sin API Key (modo desarrollo)")
    print()
    
    # Preparar el archivo
    with open(pdf_file, 'rb') as f:
        files = {
            'files': (pdf_file, f, 'application/pdf')
        }
        data = {
            'business_id': business_id
        }
        headers = {}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        print(f"🚀 Subiendo documento a {API_URL}...")
        print("⏳ Esperando respuesta (esto puede tomar un momento)...")
        print()
        
        try:
            response = requests.post(
                API_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minutos de timeout para la generación de FAQs
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ ¡DOCUMENTO PROCESADO EXITOSAMENTE!")
                print("-"*70)
                print()
                
                if result.get('ok'):
                    print(f"📈 Documentos procesados: {result.get('documents_processed')}")
                    print()
                    
                    for doc in result.get('results', []):
                        print(f"📄 Documento ID: {doc.get('document_id')}")
                        print(f"   Nombre: {doc.get('filename')}")
                        print(f"   Chunks creados: {doc.get('chunks_created')}")
                        print(f"   Caracteres procesados: {doc.get('characters'):,}")
                        print(f"   🎯 FAQs generadas: {doc.get('faqs_created', 0)}")
                        print()
                    
                    # Si hay FAQs creadas, mostrarlas
                    if any(doc.get('faqs_created', 0) > 0 for doc in result.get('results', [])):
                        print("-"*70)
                        print("📋 Consultando las FAQs generadas...")
                        print()
                        show_generated_faqs(business_id)
                else:
                    print(f"⚠️  Respuesta: {result}")
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se puede conectar al servidor")
            print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
        except requests.exceptions.Timeout:
            print("❌ Error: Timeout - El servidor tardó demasiado en responder")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("="*70)

def show_generated_faqs(business_id):
    """Muestra las FAQs generadas desde la base de datos."""
    from app.database import SessionLocal
    from app.models import FAQ
    
    db = SessionLocal()
    try:
        # Obtener las últimas FAQs del negocio
        faqs = db.query(FAQ).filter(
            FAQ.business_id == business_id
        ).order_by(FAQ.created_at.desc()).limit(10).all()
        
        if faqs:
            print("💡 FAQS GENERADAS AUTOMÁTICAMENTE:")
            print("-"*70)
            print()
            
            for idx, faq in enumerate(faqs, 1):
                print(f"FAQ #{idx}")
                print(f"Categoría: [{faq.category}]")
                print(f"Pregunta: {faq.question}")
                print(f"Respuesta: {faq.answer[:200]}{'...' if len(faq.answer) > 200 else ''}")
                print(f"Prioridad: {faq.priority}")
                print()
        else:
            print("ℹ️  No se encontraron FAQs para este negocio")
            
    except Exception as e:
        print(f"⚠️  Error al consultar FAQs: {e}")
    finally:
        db.close()

def main():
    """Función principal."""
    print("Creando documento PDF de prueba...")
    pdf_file = create_test_pdf()
    print(f"✓ PDF creado: {pdf_file}")
    print()
    
    # Subir el documento
    upload_document_to_api(pdf_file, business_id=1)
    
    # Preguntar si eliminar el archivo
    response = input("\n¿Deseas eliminar el archivo PDF de prueba? (s/n): ").lower()
    if response == 's':
        os.remove(pdf_file)
        print(f"✓ Archivo {pdf_file} eliminado")

if __name__ == "__main__":
    main()
