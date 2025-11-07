"""
Script de prueba para verificar la detección de 'wants_all_rules'
"""

message_tests = [
    "dime las normas del gimnasio",
    "las normas del gimnasio",
    "cuales son las normas",
    "me gustaría saber las normas",
    "normas del gimnasio"
]

# Patrones de detección
patterns = [
    'las normas', 'todas las normas', 'qué normas', 'cuáles son las normas',
    'las reglas', 'todas las reglas', 'qué reglas', 'cuáles son las reglas',
    'normativa', 'reglamento', 'dime las normas', 'cuales normas',
    'normas del gimnasio', 'reglas del gimnasio'
]

print("🧪 Prueba de detección de 'wants_all_rules'\n")
print("=" * 80)

for msg in message_tests:
    msg_lower = msg.lower()
    detected = any(phrase in msg_lower for phrase in patterns)
    symbol = "✅" if detected else "❌"
    print(f"{symbol} '{msg}'")
    if detected:
        matched = [p for p in patterns if p in msg_lower]
        print(f"   Coincide con: {matched}")
    print()

print("=" * 80)
print("\n🔍 Probando tu mensaje exacto: 'dime las normas del gimnasio'")
msg = "dime las normas del gimnasio"
msg_lower = msg.lower()
detected = any(phrase in msg_lower for phrase in patterns)
print(f"Resultado: {'✅ DETECTADO' if detected else '❌ NO DETECTADO'}")
if detected:
    matched = [p for p in patterns if p in msg_lower]
    print(f"Patrones que coinciden: {matched}")
