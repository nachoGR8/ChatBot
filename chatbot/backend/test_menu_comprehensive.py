import requests
import uuid

url = "http://localhost:8000/chat"
session_id = str(uuid.uuid4())

# Diferentes formas de preguntar por el menú
preguntas = [
    "¿Cuál es el menú completo del restaurante?",
    "¿Qué platos tienen?",
    "Dime todo lo que tienen para comer",
    "¿Qué hay en el menú?",
    "Muéstrame la carta",
    "¿Cuánto cuesta la paella?",
    "¿Tienen postres?",
    "¿Qué opciones de comida hay?",
    "Lista todos los platos",
    "¿Qué recomiendas del menú?"
]

print("=" * 100)
print("🧪 PRUEBAS DE RESPUESTAS DEL CHATBOT SOBRE EL MENÚ")
print("=" * 100)
print(f"Session ID: {session_id}\n")

for i, pregunta in enumerate(preguntas, 1):
    print(f"\n{'=' * 100}")
    print(f"🧪 PRUEBA {i}/10")
    print("=" * 100)
    print(f"❓ Pregunta: {pregunta}\n")
    
    try:
        response = requests.post(
            url,
            json={
                "business_id": 1,
                "session_id": session_id,
                "message": pregunta
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            respuesta = result.get('response', 'Sin respuesta')
            
            # Verificar si la respuesta contiene información del menú
            keywords_menu = ['paella', 'menú', 'plato', 'arroz', 'precio', '€', 'postre', 'entrante']
            tiene_info_menu = any(keyword.lower() in respuesta.lower() for keyword in keywords_menu)
            
            # Mostrar respuesta resumida
            respuesta_preview = respuesta[:300] + "..." if len(respuesta) > 300 else respuesta
            print(f"✅ Respuesta ({len(respuesta)} caracteres):")
            print("-" * 100)
            print(respuesta_preview)
            print("-" * 100)
            
            if tiene_info_menu:
                print("✅ Contiene información del menú")
            else:
                print("⚠️  NO contiene información del menú")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Pequeña pausa entre requests
    import time
    time.sleep(0.5)

print(f"\n{'=' * 100}")
print("✅ PRUEBAS COMPLETADAS")
print("=" * 100)
