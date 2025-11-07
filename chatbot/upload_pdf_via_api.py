"""Script para subir PDF a través de la API del admin panel."""
import requests
from pathlib import Path

# Configuración
API_URL = "http://localhost:8000/api/train-ia"
PDF_PATH = Path("./backend/Restaurante_La_Paella_Completo.pdf")
BUSINESS_ID = 1
ADMIN_API_KEY = "admin123"

print("=" * 80)
print("📤 SUBIENDO PDF A TRAVÉS DE LA API")
print("=" * 80)

# Verificar que el PDF existe
if not PDF_PATH.exists():
    print(f"❌ PDF no encontrado en: {PDF_PATH}")
    exit(1)

print(f"✅ PDF encontrado: {PDF_PATH}")
print(f"📊 Tamaño: {PDF_PATH.stat().st_size} bytes")

# Leer el PDF
with open(PDF_PATH, 'rb') as f:
    pdf_content = f.read()

# Preparar la petición
files = {
    'files': (PDF_PATH.name, pdf_content, 'application/pdf')
}
data = {
    'business_id': BUSINESS_ID
}
headers = {
    'X-Admin-API-Key': ADMIN_API_KEY
}

print("\n🚀 Enviando petición a la API...")
print(f"   URL: {API_URL}")
print(f"   Business ID: {BUSINESS_ID}")

try:
    response = requests.post(API_URL, files=files, data=data, headers=headers, timeout=60)
    
    print(f"\n📡 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ ¡PDF PROCESADO EXITOSAMENTE!")
        print("=" * 80)
        print(f"📊 Documentos procesados: {result.get('documents_processed', 0)}")
        print(f"🏢 Business ID: {result.get('business_id')}")
        
        if 'results' in result:
            for doc_result in result['results']:
                print(f"\n📄 Documento: {doc_result.get('filename')}")
                print(f"   - ID: {doc_result.get('document_id')}")
                print(f"   - Chunks: {doc_result.get('chunks_created')}")
                print(f"   - FAQs generados: {doc_result.get('faqs_generated')}")
        
        if 'errors' in result:
            print(f"\n⚠️  Errores: {len(result['errors'])}")
            for error in result['errors']:
                print(f"   - {error}")
        
        print("=" * 80)
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Respuesta: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: No se pudo conectar al backend")
    print("   ¿Está el backend ejecutándose en http://localhost:8000?")
except requests.exceptions.Timeout:
    print("\n❌ ERROR: Timeout después de 60 segundos")
except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
