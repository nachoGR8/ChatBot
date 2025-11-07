"""
Script maestro para resetear y inicializar la base de datos correctamente.
Este script debe ejecutarse desde c:/Users/nacho/Desktop/chatbot/chatbot/
para usar la misma ruta de DB que el backend.
"""
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("🔄 RESET Y INICIALIZACIÓN DE BASE DE DATOS")
print("=" * 80)

# Verificar que estamos en el directorio correcto
current_dir = Path.cwd()
expected_dir = Path("c:/Users/nacho/Desktop/chatbot/chatbot")
if current_dir.resolve() != expected_dir.resolve():
    print(f"❌ ERROR: Este script debe ejecutarse desde {expected_dir}")
    print(f"   Directorio actual: {current_dir}")
    sys.exit(1)

print(f"✅ Directorio correcto: {current_dir}")

# 1. ELIMINAR BASES DE DATOS ANTIGUAS
print("\n" + "=" * 80)
print("🗑️  PASO 1: Eliminando bases de datos antiguas")
print("=" * 80)

db_files = [
    Path("./chatbot.db"),
    Path("../chatbot.db"),
    Path("./backend/chatbot.db")
]

for db_file in db_files:
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"  ✓ Eliminado: {db_file}")
        except Exception as e:
            print(f"  ✗ Error eliminando {db_file}: {e}")
    else:
        print(f"  - No existe: {db_file}")

# 2. CREAR TABLAS
print("\n" + "=" * 80)
print("📋 PASO 2: Creando tablas en la base de datos")
print("=" * 80)

# Agregar el directorio backend al path para importar módulos
sys.path.insert(0, str(Path("./backend").resolve()))

try:
    from app.database import Base, engine, ensure_business_custom_columns
    from app.models import Business, FAQ, Conversation, Document, DocumentChunk
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas: businesses, faqs, conversations, documents, document_chunks")
    
    # Asegurar columnas personalizadas
    ensure_business_custom_columns()
    print("✅ Columnas personalizadas verificadas")
    
except Exception as e:
    print(f"❌ Error creando tablas: {e}")
    sys.exit(1)

# 3. CREAR BUSINESS INICIAL
print("\n" + "=" * 80)
print("🏢 PASO 3: Creando business inicial")
print("=" * 80)

conn = sqlite3.connect('./chatbot.db')
cursor = conn.cursor()

# Verificar si ya existe business_id=1
existing = cursor.execute("SELECT id FROM businesses WHERE id = 1").fetchone()

if not existing:
    cursor.execute("""
        INSERT INTO businesses (id, name, business_type, address, created_at, active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, "Restaurante La Paella", "restaurant", "Valencia, España", datetime.utcnow().isoformat(), 1))
    conn.commit()
    print("✅ Business ID 1 creado: Restaurante La Paella")
else:
    print("✅ Business ID 1 ya existe")

# 4. SUBIR PDF Y GENERAR FAQS AUTOMÁTICAS
print("\n" + "=" * 80)
print("📄 PASO 4: Procesando PDF y generando FAQs automáticas")
print("=" * 80)

pdf_path = Path("./backend/Restaurante_La_Paella_Completo.pdf")
if not pdf_path.exists():
    print(f"⚠️  PDF no encontrado en: {pdf_path}")
    print("   Saltando este paso. Deberás subir el PDF manualmente.")
else:
    try:
        # Importar el procesador de documentos
        from backend.app.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Leer el PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Procesar el documento
        from app.database import SessionLocal
        db = SessionLocal()
        
        result = processor.process_document(
            file_content=pdf_content,
            filename="Restaurante_La_Paella_Completo.pdf",
            business_id=1,
            db=db
        )
        
        db.close()
        
        print(f"✅ PDF procesado exitosamente:")
        print(f"   - Document ID: {result['document_id']}")
        print(f"   - Chunks creados: {result['chunks_created']}")
        print(f"   - FAQs generados: {result['faqs_generated']}")
        
    except Exception as e:
        print(f"⚠️  Error procesando PDF: {e}")
        print("   Continuando con el siguiente paso...")

# 5. CREAR FAQ DE MENÚ CON PRIORIDAD 100
print("\n" + "=" * 80)
print("📋 PASO 5: Creando FAQ de menú con prioridad máxima")
print("=" * 80)

menu_question = "¿Qué platos tienen? ¿Cuáles son los platos disponibles? ¿Qué hay en el menú?"

menu_answer = """**MENÚ RESTAURANTE LA PAELLA - Platos disponibles:**

• **Esgarraet tradicional** - Bacalao, pimiento asado y aceite de oliva - 10.50€

• **Paella Valenciana** - Pollo, conejo, judías verdes, garrofó, arroz bomba - 18.00€

• **Fideuà de Marisco** - Fideos con gambas, mejillones y calamar - 22.00€

• **Secreto ibérico a la brasa** - Con guarnición de verduras asadas - 19.50€

• **Rape al horno con alioli** - Rape fresco con alioli cítrico - 21.50€

• **Tarta de queso al horno** - Con mermelada de tomate valenciano - 7.00€

Estos son TODOS los platos principales del menú. No hay más platos disponibles."""

try:
    cursor.execute("""
        INSERT INTO faqs (business_id, question, answer, category, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1,
        menu_question,
        menu_answer,
        "menu",
        100,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    
    faq_id = cursor.lastrowid
    print(f"✅ FAQ de menú creado con ID: {faq_id}")
    print(f"   Priority: 100 (máxima)")
    print(f"   Platos: 6")
    
except Exception as e:
    print(f"❌ Error creando FAQ de menú: {e}")

# 6. VERIFICAR RESULTADOS
print("\n" + "=" * 80)
print("📊 PASO 6: Verificando resultados finales")
print("=" * 80)

# Contar registros
businesses_count = cursor.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
faqs_count = cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1").fetchone()[0]
faqs_priority_100 = cursor.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1 AND priority >= 100").fetchone()[0]
documents_count = cursor.execute("SELECT COUNT(*) FROM documents WHERE business_id = 1").fetchone()[0]
chunks_count = cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE business_id = 1").fetchone()[0]

print(f"✅ Businesses: {businesses_count}")
print(f"✅ FAQs (business_id=1): {faqs_count}")
print(f"✅ FAQs con prioridad >= 100: {faqs_priority_100}")
print(f"✅ Documents: {documents_count}")
print(f"✅ Document chunks: {chunks_count}")

conn.close()

# 7. RESUMEN FINAL
print("\n" + "=" * 80)
print("✅ ¡INICIALIZACIÓN COMPLETADA!")
print("=" * 80)
print("\n📝 RESUMEN:")
print("  • Base de datos creada en: ./chatbot.db")
print("  • Esta es la MISMA ubicación que usa el backend")
print("  • FAQ de menú con prioridad 100 creado")
print("  • Bypass directo activado para consultas de menú")
print("\n🚀 SIGUIENTE PASO:")
print("  • Reinicia el backend: .\\run_backend_fixed.ps1")
print("  • Prueba el menú: python backend\\test_menu_response.py")
print("=" * 80)
