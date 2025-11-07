from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from fastapi.testclient import TestClient

from backend.main import (
    Business,
    Document,
    DocumentChunk,
    SessionLocal,
    app,
)
from backend.app.services.document_service import document_service


def _build_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = DocxDocument()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_train_ia_upload_creates_document_and_chunks():
    client = TestClient(app)
    db = SessionLocal()
    business = Business(name="Docs Biz", business_type="gym")

    try:
        db.add(business)
        db.commit()
        db.refresh(business)

        file_bytes = _build_docx_bytes([
            "Horario: Abrimos de lunes a viernes de 6:00 a 23:00.",
            "Servicios: Clases de yoga, pilates y spinning para todos los niveles.",
        ])

        response = client.post(
            "/api/train-ia",
            data={"business_id": str(business.id)},
            files=[
                (
                    "files",
                    (
                        "conocimiento.docx",
                        file_bytes,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ),
                )
            ],
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["documents_processed"] == 1
        assert payload["business_id"] == business.id

        document = db.query(Document).filter(Document.business_id == business.id).first()
        assert document is not None
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
        assert len(chunks) >= 1

        snippets = document_service.get_relevant_chunks(
            db=db,
            business_id=business.id,
            query="¿Tenéis clases de yoga?",
            limit=2,
        )
        assert snippets
        assert any("yoga" in snippet["text"].lower() for snippet in snippets)

    finally:
        try:
            docs = db.query(Document).filter(Document.business_id == business.id).all()
            for doc in docs:
                if doc.storage_path:
                    try:
                        Path(doc.storage_path).unlink(missing_ok=True)
                    except Exception:
                        pass
            db.query(DocumentChunk).filter(DocumentChunk.business_id == business.id).delete()
            db.query(Document).filter(Document.business_id == business.id).delete()
            db.delete(business)
            db.commit()
        except Exception:
            db.rollback()
        db.close()
