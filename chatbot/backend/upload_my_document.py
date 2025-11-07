"""Script interactivo para subir tu propio documento y generar FAQs."""
import os
import sys
import requests

def upload_document(file_path, business_id=1):
    """Sube un documento a la API para generar FAQs."""
    
    API_URL = "http://localhost:8000/api/train-ia"
    API_KEY = "nacho123"
    
    print("\n" + "="*70)
    print("GENERACIÓN AUTOMÁTICA DE FAQs DESDE TU DOCUMENTO")
    print("="*70)
    print()
    
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        print(f"❌ Error: El archivo '{file_path}' no existe")
        return
    
    # Verificar extensión
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.pdf', '.docx']:
        print(f"❌ Error: Solo se aceptan archivos PDF o DOCX")
        print(f"   Tu archivo es: {ext}")
        return
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"📄 Archivo: {file_name}")
    print(f"📊 Tamaño: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"🏢 Negocio ID: {business_id}")
    print()
    
    # Confirmar
    response = input("¿Proceder con la carga y generación de FAQs? (s/n): ").lower().strip()
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    print()
    print("🚀 Subiendo documento a la API...")
    print("⏳ Generando FAQs automáticamente...")
    print("   (Esto puede tomar 1-3 minutos dependiendo del tamaño del documento)")
    print()
    
    # Subir el archivo
    try:
        with open(file_path, 'rb') as f:
            files = {
                'files': (file_name, f, 'application/pdf' if ext == '.pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            data = {
                'business_id': business_id
            }
            headers = {
                'X-API-Key': API_KEY
            }
            
            response = requests.post(
                API_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minutos
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
                    
                    # Mostrar las FAQs generadas
                    faqs_created = sum(doc.get('faqs_created', 0) for doc in result.get('results', []))
                    if faqs_created > 0:
                        print("-"*70)
                        print(f"💡 Se generaron {faqs_created} FAQs automáticamente")
                        print()
                        print("Para ver las FAQs generadas:")
                        print("1. Abre el Admin Panel: http://localhost:8000/admin.html")
                        print("2. Ve a la sección de FAQs del negocio")
                        print("3. O consulta la base de datos directamente")
                    else:
                        print("⚠️  No se generaron FAQs automáticamente")
                        print("   Verifica que el backend esté corriendo correctamente")
                else:
                    print(f"⚠️  Respuesta inesperada: {result}")
                    
            elif response.status_code == 401:
                print("❌ Error de autenticación")
                print("   Verifica que la API Key sea correcta")
            elif response.status_code == 400:
                print("❌ Error en la solicitud")
                print(f"   Detalle: {response.json().get('detail', 'Error desconocido')}")
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"   Respuesta: {response.text[:200]}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor")
        print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
        print("   Puedes iniciarlo con: .\\run_backend_fixed.ps1")
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El servidor tardó demasiado en responder")
        print("   El documento puede ser muy grande o el servidor está sobrecargado")
    except FileNotFoundError:
        print(f"❌ Error: No se pudo abrir el archivo '{file_path}'")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*70)

def main():
    print("\n" + "="*70)
    print("GENERADOR DE FAQs AUTOMÁTICO - SUBIR DOCUMENTO")
    print("="*70)
    print()
    print("Este script te permite subir un documento PDF o DOCX")
    print("y generar automáticamente FAQs basadas en su contenido.")
    print()
    
    # Solicitar ruta del archivo
    print("Opciones:")
    print("1. Arrastra y suelta el archivo aquí")
    print("2. Escribe la ruta completa del archivo")
    print("3. Presiona Enter para seleccionar desde el directorio actual")
    print()
    
    file_path = input("Ruta del archivo: ").strip().strip('"').strip("'")
    
    if not file_path:
        # Listar archivos PDF y DOCX en el directorio actual
        print("\nArchivos disponibles en el directorio actual:")
        current_dir = os.getcwd()
        files = []
        for f in os.listdir(current_dir):
            if f.lower().endswith(('.pdf', '.docx')):
                files.append(f)
                print(f"  {len(files)}. {f}")
        
        if not files:
            print("❌ No se encontraron archivos PDF o DOCX en el directorio actual")
            return
        
        print()
        selection = input("Selecciona un número: ").strip()
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(files):
                file_path = os.path.join(current_dir, files[idx])
            else:
                print("❌ Selección inválida")
                return
        except ValueError:
            print("❌ Debes ingresar un número")
            return
    
    # Solicitar business_id
    print()
    business_input = input("ID del negocio (Enter para usar 1): ").strip()
    business_id = int(business_input) if business_input else 1
    
    # Subir el documento
    upload_document(file_path, business_id)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
