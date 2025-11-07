"""Debug: Ver el contenido exacto de los chunks del documento"""
import sqlite3

conn = sqlite3.connect('chatbot.db')

print("=== CHUNKS DE DOCUMENTOS ===\n")
cursor = conn.execute("""
    SELECT id, chunk_index, LENGTH(text) as len, text
    FROM document_chunks
    WHERE business_id = 1
    ORDER BY chunk_index
""")

for row in cursor:
    print(f"\n{'='*80}")
    print(f"Chunk ID: {row[0]} | Index: {row[1]} | Length: {row[2]} chars")
    print(f"{'='*80}")
    print(row[3])
    print(f"{'='*80}\n")

conn.close()
