from app.services.document_service import document_service

# Crear 5 FAQs de menú como lo hace el código
menu_faqs = [
    {"question": "¿Qué platos tienen en el menú?", "answer": "Menu content", "category": "menú"},
    {"question": "¿Cuál es el menú completo?", "answer": "Menu content", "category": "menú"},
    {"question": "¿Qué tienen para comer?", "answer": "Menu content", "category": "menú"},
    {"question": "Dime todos los platos que tienen", "answer": "Menu content", "category": "menú"},
    {"question": "Muéstrame el menú completo del restaurante", "answer": "Menu content", "category": "menú"},
]

print("=" * 80)
print("TEST: Verificando deduplicación de FAQs de menú")
print("=" * 80)
print(f"\n📥 FAQs de entrada: {len(menu_faqs)}")
for i, faq in enumerate(menu_faqs, 1):
    print(f"  {i}. {faq['question']}")

# Llamar al método de deduplicación
unique_faqs = document_service._remove_duplicate_faqs(menu_faqs)

print(f"\n📤 FAQs después de deduplicación: {len(unique_faqs)}")
for i, faq in enumerate(unique_faqs, 1):
    print(f"  {i}. {faq['question']}")

print("\n" + "=" * 80)
if len(unique_faqs) == 5:
    print("✅ PERFECTO: Se mantuvieron las 5 variaciones")
else:
    print(f"❌ PROBLEMA: Se eliminaron {5 - len(unique_faqs)} variaciones")
print("=" * 80)
