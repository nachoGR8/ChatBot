import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'chatbot.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

business_id = 2  # Overcome

print("=" * 100)
print("📊 ANÁLISIS COMPLETO DE FAQs GENERADAS - GIMNASIO OVERCOME")
print("=" * 100)

# Obtener todas las FAQs
cursor.execute("""
    SELECT id, question, answer, category, priority, created_at
    FROM faqs
    WHERE business_id = ?
    ORDER BY category, id
""", (business_id,))

faqs = cursor.fetchall()

if not faqs:
    print("\n❌ No se encontraron FAQs")
    conn.close()
    exit()

print(f"\n✅ Total de FAQs: {len(faqs)}")

# Análisis por categoría
categories = {}
for faq in faqs:
    cat = faq[3] if faq[3] else "sin categoría"
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(faq)

print(f"\n📁 Distribución por categorías:")
for cat, items in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"   • {cat}: {len(items)} FAQs")

# Análisis de longitud de respuestas
answer_lengths = [len(faq[2]) for faq in faqs]
avg_length = sum(answer_lengths) / len(answer_lengths)
min_length = min(answer_lengths)
max_length = max(answer_lengths)

print(f"\n📏 Análisis de longitud de respuestas:")
print(f"   • Promedio: {avg_length:.0f} caracteres")
print(f"   • Mínima: {min_length} caracteres")
print(f"   • Máxima: {max_length} caracteres")

# Mostrar todas las FAQs por categoría
print("\n" + "=" * 100)
print("📋 DETALLE DE TODAS LAS FAQs")
print("=" * 100)

for cat, items in sorted(categories.items()):
    print(f"\n{'='*100}")
    print(f"📁 CATEGORÍA: {cat.upper()} ({len(items)} FAQs)")
    print("=" * 100)
    
    for idx, faq in enumerate(items, 1):
        faq_id, question, answer, category, priority, created_at = faq
        
        print(f"\n🔹 FAQ #{idx} (ID: {faq_id})")
        print(f"❓ PREGUNTA: {question}")
        print(f"💬 RESPUESTA ({len(answer)} chars):")
        print(f"   {answer}")
        print(f"⭐ Prioridad: {priority}")
        print("-" * 100)

# Análisis de calidad
print("\n" + "=" * 100)
print("🎯 ANÁLISIS DE CALIDAD")
print("=" * 100)

# Contar respuestas muy cortas (< 100 chars)
short_answers = [f for f in faqs if len(f[2]) < 100]
# Contar respuestas completas (> 200 chars)
complete_answers = [f for f in faqs if len(f[2]) > 200]
# Contar respuestas medias (100-200 chars)
medium_answers = [f for f in faqs if 100 <= len(f[2]) <= 200]

print(f"\n📊 Distribución de calidad de respuestas:")
print(f"   ⚠️  Respuestas cortas (< 100 chars): {len(short_answers)} ({len(short_answers)/len(faqs)*100:.1f}%)")
print(f"   ✅ Respuestas medias (100-200 chars): {len(medium_answers)} ({len(medium_answers)/len(faqs)*100:.1f}%)")
print(f"   ⭐ Respuestas completas (> 200 chars): {len(complete_answers)} ({len(complete_answers)/len(faqs)*100:.1f}%)")

# Análisis de preguntas únicas
questions_text = [f[1].lower() for f in faqs]
unique_questions = len(set(questions_text))
print(f"\n🔍 Verificación de duplicados:")
print(f"   • Preguntas únicas: {unique_questions}/{len(faqs)}")
if unique_questions < len(faqs):
    print(f"   ⚠️  Hay {len(faqs) - unique_questions} preguntas duplicadas")
else:
    print(f"   ✅ Todas las preguntas son únicas")

# Análisis del contenido del PDF vs FAQs
print(f"\n📄 Cobertura del contenido del PDF:")
pdf_topics = [
    "acceso", "tarjeta de socio", "registro entrada",
    "fumar", "alcohol", "drogas",
    "ropa deportiva", "calzado deportivo",
    "limpieza material", "pesas", "máquinas", "toallas",
    "fotografiar", "grabar", "privacidad",
    "clases dirigidas", "reservas", "app", "cancelación",
    "ducharse", "spa", "higiene",
    "lesión", "incidente", "seguridad",
    "taquillas", "pérdidas", "robos",
    "respeto", "gritar", "comportamiento", "expulsión"
]

covered_topics = []
all_faq_text = " ".join([f[1].lower() + " " + f[2].lower() for f in faqs])

for topic in pdf_topics:
    if topic.lower() in all_faq_text:
        covered_topics.append(topic)

print(f"   • Temas cubiertos: {len(covered_topics)}/{len(pdf_topics)} ({len(covered_topics)/len(pdf_topics)*100:.1f}%)")
print(f"\n   ✅ Temas presentes en las FAQs:")
for i in range(0, len(covered_topics), 5):
    topics_chunk = covered_topics[i:i+5]
    print(f"      {', '.join(topics_chunk)}")

missing_topics = [t for t in pdf_topics if t not in covered_topics]
if missing_topics:
    print(f"\n   ⚠️  Temas NO cubiertos:")
    for i in range(0, len(missing_topics), 5):
        topics_chunk = missing_topics[i:i+5]
        print(f"      {', '.join(topics_chunk)}")

print("\n" + "=" * 100)
print("✅ ANÁLISIS COMPLETADO")
print("=" * 100)

conn.close()
