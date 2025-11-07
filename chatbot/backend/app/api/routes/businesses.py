"""Business management routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ...models import Business
from ...schemas import BusinessCreate, BusinessResponse, BusinessUpdate
from ..dependencies import get_db

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessResponse)
def create_business(business: BusinessCreate, db: Session = Depends(get_db)):
    name = business.name.strip()
    existing = db.query(Business).filter(func.lower(Business.name) == name.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Negocio con ese nombre ya existe")

    payload = business.dict()
    payload["name"] = name
    db_business = Business(**payload)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business


@router.get("", response_model=List[BusinessResponse])
def get_businesses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Business).filter(Business.active == True).offset(skip).limit(limit).all()  # noqa: E712


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.patch("/{business_id}", response_model=BusinessResponse)
def update_business(business_id: int, payload: BusinessUpdate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    data = payload.dict(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        name = data["name"].strip()
        existing = (
            db.query(Business)
            .filter(func.lower(Business.name) == name.lower(), Business.id != business_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Otro negocio con ese nombre ya existe")
        business.name = name

    for field in (
        "business_type",
        "phone",
        "email",
        "address",
        "website",
        "tone_override",
        "welcome_message",
        "generation_temperature",
        "generation_top_p",
    ):
        if field in data:
            setattr(business, field, data[field])

    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.put("/{business_id}", response_model=BusinessResponse)
def update_business_full(business_id: int, payload: BusinessUpdate, db: Session = Depends(get_db)):
    """Update business (alias for PATCH, for frontend compatibility)."""
    return update_business(business_id, payload, db)


@router.delete("/{business_id}")
def delete_business(business_id: int, db: Session = Depends(get_db)):
    """Delete business and all its related data (documents, FAQs, etc.)."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    # Delete the business (cascading will handle related records if configured)
    db.delete(business)
    db.commit()
    
    return {"msg": f"Negocio '{business.name}' eliminado exitosamente"}
