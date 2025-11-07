"""Crear FAQ específico solo con platos del menú."""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('chatbot.db')

# Primero, verificar si ya existe un FAQ similar
existing = conn.execute("""
    SELECT id FROM faqs 
    WHERE business_id = 1 
    AND question LIKE '%platos disponibles%'
""").fetchone()

if existing:
    print(f"Ya existe FAQ similar con ID: {existing[0]}")
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
conn.execute("""
    INSERT INTO faqs (business_id, question, answer, category, priority, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    1,  # business_id
    menu_question,
    menu_answer,
    "menu",
    100,  # prioridad máxima
    datetime.utcnow().isoformat(),
    datetime.utcnow().isoformat()
))

conn.commit()

# Verificar
new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
print(f"✅ FAQ de menú específico creado con ID: {new_id}")
print(f"   Prioridad: 100")
print(f"   Pregunta: {menu_question}")
print(f"   Longitud respuesta: {len(menu_answer)} caracteres")

conn.close()
