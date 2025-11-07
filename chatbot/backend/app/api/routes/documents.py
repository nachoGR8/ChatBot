"""Routes to manage knowledge base documents for training."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ...models import Business
from ..dependencies import get_db, verify_admin_api_key
from ...services.document_service import DocumentProcessingError, document_service

router = APIRouter(prefix="/api", tags=["documents"], dependencies=[Depends(verify_admin_api_key)])


@router.post("/train-ia")
async def train_ia_with_documents(
    files: List[UploadFile] = File(...),
    business_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="Debes subir al menos un archivo PDF o DOCX")

    business: Optional[Business] = None
    if business_id is not None:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")

    successes = []
    errors = []

    for upload in files:
        try:
            data = await upload.read()
            result = document_service.ingest_upload(
                db=db,
                data=data,
                filename=upload.filename or "documento",
                content_type=upload.content_type,
                business=business,
            )
            db.commit()
            successes.append(result.to_dict())
        except DocumentProcessingError as exc:
            db.rollback()
            errors.append({"filename": upload.filename, "error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive
            db.rollback()
            errors.append({"filename": upload.filename, "error": str(exc)})
        finally:
            await upload.close()

    if not successes:
        raise HTTPException(
            status_code=400,
            detail={"message": "No se pudo procesar ningún archivo", "errors": errors},
        )

    response = {
        "ok": True,
        "documents_processed": len(successes),
        "business_id": business_id,
        "results": successes,
    }
    if errors:
        response["errors"] = errors

    return response
