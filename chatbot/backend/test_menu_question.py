import requests
import json
import uuid

url = "http://localhost:8000/chat"

# Generar session_id único
session_id = str(uuid.uuid4())

print("=" * 80)
print("🧪 PRUEBA 1: Preguntando por el menú completo")
print("=" * 80)
print(f"Session ID: {session_id}\n")

question1 = "¿Cuál es el menú completo del restaurante?"
print(f"Pregunta: {question1}\n")

try:
    response = requests.post(
        url,
        json={
            "business_id": 1,
            "session_id": session_id,
            "message": question1
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Respuesta del chatbot:")
        print("-" * 80)
        print(result.get('response', 'Sin respuesta'))
        print("-" * 80)
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("🧪 PRUEBA 2: Pregunta alternativa")
print("=" * 80)

question2 = "¿Qué platos tienen en el menú?"
print(f"Pregunta: {question2}\n")

try:
    response = requests.post(
        url,
        json={
            "business_id": 1,
            "session_id": session_id,
            "message": question2
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Respuesta del chatbot:")
        print("-" * 80)
        print(result.get('response', 'Sin respuesta'))
        print("-" * 80)
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("🧪 PRUEBA 3: Pregunta genérica")
print("=" * 80)

question3 = "Dime todos los platos que tienes"
print(f"Pregunta: {question3}\n")

try:
    response = requests.post(
        url,
        json={
            "business_id": 1,
            "session_id": session_id,
            "message": question3
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Respuesta del chatbot:")
        print("-" * 80)
        print(result.get('response', 'Sin respuesta'))
        print("-" * 80)
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
