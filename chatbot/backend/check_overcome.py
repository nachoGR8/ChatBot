import sqlite3
import os

# Conectar a la base de datos (buscar en el directorio padre)
db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
print(f"Conectando a: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buscar el negocio Overcome
print("=" * 80)
print("BUSCANDO NEGOCIO 'OVERCOME'")
print("=" * 80)

cursor.execute("SELECT id, name FROM businesses WHERE name LIKE ? OR name LIKE ?", ('%overcome%', '%Overcome%'))
businesses = cursor.fetchall()

if businesses:
    for biz in businesses:
        print(f"\n📋 ID: {biz[0]}")
        print(f"📌 Nombre: {biz[1]}")
        
        business_id = biz[0]
        
        # Buscar FAQs asociadas
        print(f"\n{'='*80}")
        print(f"FAQs GENERADAS PARA '{biz[1]}' (ID: {business_id})")
        print("=" * 80)
        
        cursor.execute("""
            SELECT id, question, answer, category, priority
            FROM faqs 
            WHERE business_id = ?
            ORDER BY id DESC
            LIMIT 30
        """, (business_id,))
        
        faqs = cursor.fetchall()
        
        if faqs:
            print(f"\n✅ Total FAQs encontradas: {len(faqs)}")
            print("\n" + "="*80)
            for idx, faq in enumerate(faqs, 1):
                print(f"\n🔹 FAQ #{idx} (ID: {faq[0]})")
                print(f"❓ Pregunta: {faq[1]}")
                print(f"💬 Respuesta: {faq[2][:150]}..." if len(faq[2]) > 150 else f"💬 Respuesta: {faq[2]}")
                print(f"📁 Categoría: {faq[3]}")
                print(f"⭐ Prioridad: {faq[4]}")
                print("-" * 80)
        else:
            print("\n❌ No se encontraron FAQs para este negocio")
        
        # Buscar documentos asociados
        print(f"\n{'='*80}")
        print(f"DOCUMENTOS ASOCIADOS")
        print("=" * 80)
        
        cursor.execute("""
            SELECT id, filename, file_type, num_chunks, upload_date
            FROM documents
            WHERE business_id = ?
            ORDER BY upload_date DESC
        """, (business_id,))
        
        docs = cursor.fetchall()
        
        if docs:
            print(f"\n✅ Total documentos: {len(docs)}")
            for doc in docs:
                print(f"\n📄 ID: {doc[0]}")
                print(f"📎 Nombre: {doc[1]}")
                print(f"📋 Tipo: {doc[2]}")
                print(f"📦 Chunks: {doc[3]}")
                print(f"📅 Fecha: {doc[4]}")
        else:
            print("\n❌ No se encontraron documentos asociados")
else:
    print("\n❌ No se encontró ningún negocio con el nombre 'Overcome'")
    print("\n🔍 Mostrando todos los negocios disponibles:")
    cursor.execute("SELECT id, name FROM businesses")
    all_businesses = cursor.fetchall()
    for biz in all_businesses:
        print(f"  - ID {biz[0]}: {biz[1]}")

conn.close()
