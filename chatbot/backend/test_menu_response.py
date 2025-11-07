"""Script para probar la consulta del menú con el documento cargado."""
import requests
import json

url = "http://localhost:8000/chat"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "nacho123"
}

# Simular conversación
payload = {
    "business_id": 1,
    "session_id": "test_menu_session",
    "message": "Dime el menú"
}

print("=" * 80)
print("🧪 TEST: Consultando el menú completo del restaurante")
print("=" * 80)
print(f"\nURL: {url}")
print(f"Business ID: {payload['business_id']}")
print(f"Mensaje: {payload['message']}\n")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nEstructura de respuesta: {list(data.keys())}")
        
        # El campo puede ser 'response' en lugar de 'bot_response'
        respuesta = data.get('bot_response') or data.get('response') or str(data)
        
        print(f"\nRespuesta del chatbot ({len(respuesta)} caracteres):")
        print("=" * 80)
        print(respuesta)
        print("=" * 80)
        
        # Verificar platos reales
        platos_reales = [
            "Esgarraet",
            "Paella Valenciana",
            "Fideuà",
            "Secreto ibérico",
            "Rape al horno"
        ]
        
        print("\n✅ VERIFICACIÓN DE PLATOS REALES:")
        for plato in platos_reales:
            if plato in respuesta:
                print(f"  ✓ {plato} - ENCONTRADO")
            else:
                print(f"  ✗ {plato} - NO ENCONTRADO")
        
        # Verificar que NO hay platos inventados
        platos_falsos = [
            "Tortilla de Patatas",
            "Pollo al Ajillo",
            "Ensalada de Tomate",
            "Sopa de Pescado",
            "Arroz con Verduras",
            "Chuleta de Cordero",
            "Crema Catalana"
        ]
        
        print("\n🚫 VERIFICACIÓN DE PLATOS INVENTADOS (NO deberían aparecer):")
        for plato in platos_falsos:
            if plato in respuesta:
                print(f"  ✗ {plato} - APARECE (PROBLEMA: inventado)")
            else:
                print(f"  ✓ {plato} - No aparece (correcto)")
                
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ EXCEPCIÓN: {str(e)}")
    import traceback
    traceback.print_exc()
