import sqlite3

conn = sqlite3.connect('chatbot.db')

# Verificar documentos
print("=== DOCUMENTOS ===")
cursor = conn.execute("SELECT id, filename, business_id, created_at FROM documents")
for row in cursor:
    print(f"ID: {row[0]} | Archivo: {row[1]} | Negocio: {row[2]} | Fecha: {row[3]}")

print("\n=== CHUNKS DE DOCUMENTOS (filtrado por 'menu' o 'plato') ===")
cursor = conn.execute("""
    SELECT d.filename, dc.chunk_index, dc.text
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE LOWER(dc.text) LIKE '%menu%' 
       OR LOWER(dc.text) LIKE '%plato%'
       OR LOWER(dc.text) LIKE '%paella%'
    ORDER BY d.id, dc.chunk_index
    LIMIT 10
""")

for row in cursor:
    print(f"\nArchivo: {row[0]} | Chunk: {row[1]}")
    print(f"Texto ({len(row[2])} chars):")
    print(row[2][:600])
    print("...")

conn.close()
