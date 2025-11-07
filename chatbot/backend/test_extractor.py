"""Test del extractor de menú"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.services.chatbot_service import chatbot_service
import logging

# Activar logging
logging.basicConfig(level=logging.INFO)

db = SessionLocal()

print("=== TEST DEL EXTRACTOR DE MENÚ ===\n")

try:
    menu = chatbot_service.extract_menu_from_documents(db, business_id=1)

    if menu:
        print("✅ Menú extraído exitosamente:")
        print("="*80)
        print(menu)
        print("="*80)
    else:
        print("❌ No se pudo extraer el menú")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

db.close()
