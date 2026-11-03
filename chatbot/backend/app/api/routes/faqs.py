"""FAQ management routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...models import Business, FAQ
from ...schemas import FAQCreate, FAQResponse
from ..dependencies import get_db, verify_admin_api_key

router = APIRouter(prefix="/faqs", tags=["faqs"])


@router.post("", response_model=FAQResponse, dependencies=[Depends(verify_admin_api_key)])
def create_faq(faq: FAQCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == faq.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    db_faq = FAQ(**faq.dict())
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq


@router.get("", response_model=List[FAQResponse])
def get_faqs(business_id: int = Query(..., description="ID del negocio"), db: Session = Depends(get_db)):
    """Get FAQs by business_id query parameter."""
    return (
        db.query(FAQ)
            .filter(FAQ.business_id == business_id)
            .order_by(FAQ.priority.desc())
            .all()
    )


@router.get("/{business_id}", response_model=List[FAQResponse])
def get_faqs_by_path(business_id: int, db: Session = Depends(get_db)):
    """Get FAQs by business_id path parameter (legacy support)."""
    return (
        db.query(FAQ)
            .filter(FAQ.business_id == business_id)
            .order_by(FAQ.priority.desc())
            .all()
    )


@router.delete("/{faq_id}", dependencies=[Depends(verify_admin_api_key)])
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada")

    db.delete(faq)
    db.commit()
    return {"msg": "FAQ eliminada exitosamente"}
