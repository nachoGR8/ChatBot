"""Script para cargar el PDF del menú al sistema de documentos."""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.services.document_service import DocumentService
from app.models import Business
from pathlib import Path

def upload_pdf():
    db = SessionLocal()
    try:
        # Ruta al PDF
        pdf_path = Path(r"C:\Users\nacho\Downloads\Restaurante_La_Paella_Completo.pdf")
        
        if not pdf_path.exists():
            print(f"❌ ERROR: No se encuentra el archivo: {pdf_path}")
            return
        
        print(f"📄 Procesando PDF: {pdf_path.name}")
        print(f"   Tamaño: {pdf_path.stat().st_size} bytes")
        
        # Leer el contenido del PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Obtener el negocio
        business = db.query(Business).filter(Business.id == 1).first()
        if not business:
            print(f"❌ ERROR: No existe el negocio con ID=1")
            return
        
        print(f"   Negocio: {business.name}")
        
        # Procesar el documento
        doc_service = DocumentService()
        result = doc_service.ingest_upload(
            db=db,
            data=pdf_content,
            filename=pdf_path.name,
            content_type="application/pdf",
            business=business
        )
        
        db.commit()
        
        print(f"\n✅ DOCUMENTO PROCESADO EXITOSAMENTE")
        print(f"   ID del documento: {result.document_id}")
        print(f"   Chunks creados: {result.chunks_created}")
        print(f"   Total caracteres: {result.characters}")
        print(f"   FAQs creados: {result.faqs_created}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    upload_pdf()
