"""Script para crear las tablas documents y document_chunks en la base de datos."""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine
from app import models  # Para cargar todos los modelos

def create_tables():
    print("📦 Creando tablas de documentos en la base de datos...")
    
    # Esto crea todas las tablas definidas en los modelos que no existan ya
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tablas creadas exitosamente")
    print("   - documents")
    print("   - document_chunks")

if __name__ == "__main__":
    create_tables()
