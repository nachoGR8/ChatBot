"""
Consulta directa a SQLite para revisar FAQs
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "chatbot.db")
if not os.path.exists(db_path):
    print(f"❌ Base de datos no encontrada en: {db_path}")
    exit()

print(f"📂 Usando base de datos: {db_path}\n")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buscar el gimnasio
print("🏋️ Buscando gimnasio...")
cursor.execute("SELECT id, name, business_type FROM businesses WHERE business_type = 'gym' OR name LIKE '%Overcome%'")
gym = cursor.fetchone()

if not gym:
    print("❌ No se encontró el gimnasio")
    conn.close()
    exit()

gym_id, gym_name, business_type = gym
print(f"✅ Gimnasio: {gym_name} (ID: {gym_id})")
print("=" * 80)

# Obtener TODAS las FAQs
cursor.execute(f"SELECT id, question, answer, category FROM faqs WHERE business_id = {gym_id}")
faqs = cursor.fetchall()

print(f"\n📊 Total FAQs en la base de datos: {len(faqs)}\n")

# Agrupar por categorías
categories = {}
for faq_id, question, answer, category in faqs:
    cat = category or "Sin categoría"
    if cat not in categories:
        categories[cat] = []
    categories[cat].append((faq_id, question, answer))

# Mostrar por categorías
for cat, cat_faqs in sorted(categories.items()):
    print(f"\n📁 {cat.upper()} ({len(cat_faqs)} FAQs)")
    print("-" * 80)
    for faq_id, question, answer in cat_faqs:
        print(f"\n  ID {faq_id}: {question}")
        print(f"  → {answer[:150]}...")

# Análisis de normas
print("\n" + "=" * 80)
print("🔍 ANÁLISIS: FAQs relacionadas con NORMAS")
print("=" * 80)

norma_keywords = ['norma', 'regla', 'prohibido', 'obligatorio', 'permitido', 
                 'acceso', 'requisito', 'política', 'fumar', 'alcohol', 'tarjeta',
                 'toalla', 'ducharse', 'reserva', 'clase', 'taquilla', 'ropa',
                 'calzado', 'deportivo', 'pesas', 'máquina', 'grabar', 'fotografiar',
                 'respeto', 'privacidad', 'protección', 'equipo', 'limpiar', 'devolver']

norma_faqs = []
for faq_id, question, answer, category in faqs:
    text = (question + " " + answer + " " + (category or "")).lower()
    matched_keywords = [kw for kw in norma_keywords if kw in text]
    if matched_keywords:
        norma_faqs.append((faq_id, question, answer, matched_keywords))

print(f"\n✅ Se encontraron {len(norma_faqs)} FAQs relacionadas con normas:\n")
for faq_id, question, answer, keywords in norma_faqs:
    print(f"  {faq_id}. {question}")
    print(f"     Keywords: {', '.join(keywords)}")
    print(f"     Respuesta: {answer[:100]}...")
    print()

# Verificar normas específicas del PDF
print("\n" + "=" * 80)
print("📋 VERIFICACIÓN: ¿Están las normas del PDF?")
print("=" * 80)

expected_normas = {
    "Registrar entrada con tarjeta": ["registrar", "tarjeta", "entrada"],
    "Ropa y calzado deportivo": ["ropa", "calzado", "deportivo"],
    "Limpiar y devolver material": ["limpiar", "devolver", "material"],
    "No dejar pesas en el suelo": ["pesas", "suelo"],
    "Usar toalla en bancos/máquinas": ["toalla", "banco", "máquina"],
    "No bloquear máquinas >30 min": ["bloquear", "máquina", "minuto", "30"],
    "Prohibido grabar/fotografiar": ["grabar", "fotografiar", "foto"],
    "Reservar plaza en clase": ["reservar", "plaza", "clase"],
    "Ducharse antes de spa": ["ducha", "spa"],
    "Informar incidente/lesión": ["informar", "incidente", "lesión"],
    "Mantener taquillas cerradas": ["taquilla", "cerrada"],
    "No gritar ni lanzar pesas": ["gritar", "lanzar", "pesas"],
    "Prohibido fumar/alcohol": ["fumar", "alcohol", "prohibido"],
    "No acceso bajo efectos": ["acceso", "alcohol", "droga", "efecto"],
    "Respetar privacidad": ["respetar", "privacidad"],
    "Equipo de protección": ["equipo", "protección", "gafas", "guantes"]
}

all_text = " ".join([q + " " + a for _, q, a, _ in faqs]).lower()

print()
for norma, keywords in expected_normas.items():
    found = any(kw in all_text for kw in keywords)
    # Contar cuántas keywords aparecen
    matches = sum(1 for kw in keywords if kw in all_text)
    symbol = "✅" if matches >= 2 else "⚠️" if matches == 1 else "❌"
    print(f"{symbol} {norma} ({matches}/{len(keywords)} keywords)")

conn.close()
