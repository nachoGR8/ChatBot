"""Pydantic schemas used by the API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

try:
    from pydantic import ConfigDict  # type: ignore

    PYDANTIC_V2 = True
except Exception:  # pragma: no cover - fallback for v1
    PYDANTIC_V2 = False
    ConfigDict = None  # type: ignore


class BusinessCreate(BaseModel):
    name: str
    business_type: str = "restaurant"
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    tone_override: Optional[str] = None
    welcome_message: Optional[str] = None
    generation_temperature: Optional[float] = None
    generation_top_p: Optional[float] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    tone_override: Optional[str] = None
    welcome_message: Optional[str] = None
    generation_temperature: Optional[float] = None
    generation_top_p: Optional[float] = None


class BusinessResponse(BaseModel):
    id: int
    name: str
    business_type: str
    active: bool
    tone_override: Optional[str]
    welcome_message: Optional[str]
    generation_temperature: Optional[float]
    generation_top_p: Optional[float]

    if PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:  # pragma: no cover - pydantic v1 fallback
        class Config:
            orm_mode = True
            from_attributes = True


class FAQCreate(BaseModel):
    business_id: int
    question: str
    answer: str
    category: Optional[str] = None
    priority: int = 0


class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str
    category: Optional[str]

    if PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:  # pragma: no cover
        class Config:
            orm_mode = True
            from_attributes = True


class ChatMessage(BaseModel):
    business_id: int
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime


class ConfigUpdate(BaseModel):
    max_faqs: Optional[int] = None
    faq_answer_max_chars: Optional[int] = None
    faq_question_max_chars: Optional[int] = None


__all__ = [
    "BusinessCreate",
    "BusinessUpdate",
    "BusinessResponse",
    "FAQCreate",
    "FAQResponse",
    "ChatMessage",
    "ChatResponse",
    "ConfigUpdate",
]
