"""Test de detección de menú"""
import sys
sys.path.insert(0, '.')

from app.services.chatbot_service import chatbot_service

messages = [
    "Dime el menú",
    "¿Qué tienen en el menú?",
    "¿Cuál es la carta?",
    "¿Qué platos tienen?",
    "Muéstrame el menú",
    "menu",
    "carta",
]

print("=== TEST DE DETECCIÓN DE CONSULTA DE MENÚ ===\n")

for msg in messages:
    result = chatbot_service.is_menu_request(msg)
    emoji = "✅" if result else "❌"
    print(f"{emoji} '{msg}' -> {result}")
