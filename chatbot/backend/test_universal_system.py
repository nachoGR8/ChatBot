"""
🧪 Test Universal System - Validación del Sistema Universal

Este script prueba la detección de información crítica para múltiples tipos de negocios.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.chatbot_service import ChatbotService

def test_detection():
    """Prueba la detección de diferentes tipos de consultas críticas"""
    
    service = ChatbotService()
    
    # Test cases: (message, expected_type)
    test_cases = [
        # RESTAURANTES
        ("¿Qué tienen en el menú?", "menú"),
        ("Cuál es la carta de platos", "menú"),
        ("Quiero ver el menú completo", "menú"),
        ("¿Qué hay para comer?", "menú"),
        
        # GIMNASIOS
        ("¿Qué clases tienen?", "clases"),
        ("Horario de actividades", "clases"),
        ("¿Cuáles son las clases disponibles?", "clases"),
        ("Lista de entrenamientos", "clases"),
        
        # TIENDAS
        ("¿Qué productos venden?", "productos"),
        ("Catálogo completo", "productos"),
        ("¿Qué tienen en inventario?", "productos"),
        ("Lista de artículos disponibles", "productos"),
        
        # SERVICIOS
        ("¿Qué servicios ofrecen?", "servicios"),
        ("Lista de tratamientos", "servicios"),
        ("¿Qué paquetes tienen?", "servicios"),
        
        # HOTELES
        ("¿Qué tipos de habitaciones hay?", "habitaciones"),
        ("Lista de suites disponibles", "habitaciones"),
        ("Opciones de alojamiento", "habitaciones"),
        
        # TARIFAS
        ("¿Cuáles son los precios?", "tarifas"),
        ("¿Cuánto cuesta?", "tarifas"),
        ("Lista de tarifas", "tarifas"),
        
        # PLANES
        ("¿Qué planes tienen?", "planes"),
        ("Opciones de membresía", "planes"),
        
        # NEGATIVOS (no debería detectar nada)
        ("Hola, ¿cómo estás?", None),
        ("¿Dónde están ubicados?", None),
        ("¿A qué hora abren?", None),
    ]
    
    print("=" * 80)
    print("🧪 PRUEBA DEL SISTEMA UNIVERSAL DE DETECCIÓN")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for message, expected_type in test_cases:
        result = service.is_critical_info_request(message)
        detected_type = result['type'] if result else None
        
        if detected_type == expected_type:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} | Mensaje: '{message}'")
        print(f"         Esperado: {expected_type}, Detectado: {detected_type}")
        if result:
            print(f"         Keywords: {result.get('keywords', [])}")
            print(f"         Emoji: {result.get('emoji', '')}")
        print()
    
    print("=" * 80)
    print(f"📊 RESULTADOS: {passed} pasaron, {failed} fallaron de {len(test_cases)} tests")
    print("=" * 80)
    
    if failed == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        return True
    else:
        print(f"⚠️  {failed} tests fallaron. Revisa la configuración.")
        return False

def test_keywords():
    """Prueba que las keywords estén correctamente configuradas"""
    
    service = ChatbotService()
    
    print("\n" + "=" * 80)
    print("🔍 VERIFICACIÓN DE KEYWORDS CONFIGURADAS")
    print("=" * 80)
    print()
    
    # Simular detección y mostrar keywords
    test_types = [
        "¿Qué tienen en el menú?",
        "¿Qué clases hay?",
        "Productos disponibles",
        "¿Qué servicios ofrecen?",
        "Tipos de habitaciones",
        "¿Cuánto cuesta?",
        "Planes de membresía"
    ]
    
    for message in test_types:
        result = service.is_critical_info_request(message)
        if result:
            print(f"📋 Tipo: {result['type']}")
            print(f"   Keywords: {', '.join(result['keywords'])}")
            print(f"   Emoji: {result['emoji']}")
            print()

def test_menu_backward_compatibility():
    """Prueba que is_menu_request() siga funcionando (backward compatibility)"""
    
    service = ChatbotService()
    
    print("\n" + "=" * 80)
    print("🔄 PRUEBA DE RETROCOMPATIBILIDAD (is_menu_request)")
    print("=" * 80)
    print()
    
    menu_messages = [
        "¿Qué tienen en el menú?",
        "Carta de platos",
        "Ver menú completo"
    ]
    
    non_menu_messages = [
        "¿Qué clases hay?",
        "Productos disponibles",
        "Hola"
    ]
    
    print("✅ Mensajes que DEBERÍAN ser detectados como menú:")
    for msg in menu_messages:
        result = service.is_menu_request(msg)
        status = "✅" if result else "❌"
        print(f"   {status} '{msg}' → {result}")
    
    print("\n❌ Mensajes que NO deberían ser detectados como menú:")
    for msg in non_menu_messages:
        result = service.is_menu_request(msg)
        status = "✅" if not result else "❌"
        print(f"   {status} '{msg}' → {result}")

if __name__ == "__main__":
    print("\n🚀 Iniciando pruebas del Sistema Universal...\n")
    
    # Ejecutar todas las pruebas
    success = test_detection()
    test_keywords()
    test_menu_backward_compatibility()
    
    print("\n✨ Pruebas completadas.\n")
    
    if not success:
        sys.exit(1)
