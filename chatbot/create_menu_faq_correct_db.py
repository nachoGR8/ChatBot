"""Crear FAQ 345 en la base de datos correcta del backend."""
import sqlite3
from datetime import datetime

# Usar la misma ruta relativa que usa el backend
conn = sqlite3.connect('./chatbot.db')

# Verificar si ya existe
existing = conn.execute("""
    SELECT id, priority FROM faqs 
    WHERE business_id = 1 
    AND priority >= 100
""").fetchone()

if existing:
    print(f"✅ Ya existe FAQ con prioridad alta: ID {existing[0]}, Priority {existing[1]}")
    conn.close()
    exit()

# Crear FAQ específico solo con los platos
menu_question = "¿Qué platos tienen? ¿Cuáles son los platos disponibles? ¿Qué hay en el menú?"

# SOLO los platos tal como aparecen en el PDF
menu_answer = """**MENÚ RESTAURANTE LA PAELLA - Platos disponibles:**

• **Esgarraet tradicional** - Bacalao, pimiento asado y aceite de oliva - 10.50€

• **Paella Valenciana** - Pollo, conejo, judías verdes, garrofó, arroz bomba - 18.00€

• **Fideuà de Marisco** - Fideos con gambas, mejillones y calamar - 22.00€

• **Secreto ibérico a la brasa** - Con guarnición de verduras asadas - 19.50€

• **Rape al horno con alioli** - Rape fresco con alioli cítrico - 21.50€

• **Tarta de queso al horno** - Con mermelada de tomate valenciano - 7.00€

Estos son TODOS los platos principales del menú. No hay más platos disponibles."""

# Insertar con prioridad máxima
cursor = conn.execute("""
    INSERT INTO faqs (business_id, question, answer, category, priority, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    1,  # business_id
    menu_question,
    menu_answer,
    "menu",
    100,  # prioridad máxima
    datetime.utcnow().isoformat()
))

conn.commit()
new_id = cursor.lastrowid

print("=" * 80)
print("✅ FAQ DE MENÚ CREADO EXITOSAMENTE")
print("=" * 80)
print(f"ID: {new_id}")
print(f"Business ID: 1")
print(f"Priority: 100")
print(f"Question: {menu_question[:60]}...")
print(f"Answer: {menu_answer[:100]}...")
print("=" * 80)

# Verificar total de FAQs ahora
total = conn.execute("SELECT COUNT(*) FROM faqs WHERE business_id = 1").fetchone()[0]
print(f"\n📊 Total FAQs para business_id=1: {total}")

conn.close()
