import requests
import os

# Configuración
url = "http://localhost:8000/api/train-ia"  # Ruta correcta
api_key = "nacho123"  # API Key que acabamos de configurar
business_id = 1
file_path = r"c:\Users\nacho\Downloads\Restaurante_La_Paella_Completo.pdf"

print("=" * 80)
print("📤 SUBIENDO DOCUMENTO PARA GENERAR FAQs")
print("=" * 80)
print(f"📄 Archivo: {os.path.basename(file_path)}")
print(f"🏢 Negocio ID: {business_id}")
print(f"🔑 API Key: {api_key}")
print()

if not os.path.exists(file_path):
    print(f"❌ Error: El archivo no existe: {file_path}")
    exit(1)

try:
    with open(file_path, 'rb') as f:
        files = {'files': (os.path.basename(file_path), f, 'application/pdf')}
        data = {'business_id': business_id}
        headers = {'X-API-Key': api_key}
        
        print("🚀 Enviando documento...")
        print("⏳ Generando FAQs automáticamente (esto puede tomar 1-3 minutos)...\n")
        
        response = requests.post(url, files=files, data=data, headers=headers, timeout=180)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ¡DOCUMENTO PROCESADO EXITOSAMENTE!\n")
            print("=" * 80)
            print("📊 RESULTADOS")
            print("=" * 80)
            print(f"📄 Documento ID: {result.get('document_id')}")
            print(f"📝 Chunks creados: {result.get('chunks_created')}")
            print(f"📊 Caracteres procesados: {result.get('characters_processed'):,}")
            print(f"🎯 FAQs generadas: {result.get('faqs_created', 0)}")
            print("=" * 80)
        else:
            print(f"❌ Error {response.status_code}")
            print(response.text)
            
except Exception as e:
    print(f"❌ Error: {e}")
