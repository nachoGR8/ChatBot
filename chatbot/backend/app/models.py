"""SQLAlchemy models for the chatbot backend."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from .database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(200), nullable=False)
    business_type: Mapped[str] = Column(String(100), default="restaurant")
    phone: Mapped[str | None] = Column(String(50))
    email: Mapped[str | None] = Column(String(100))
    address: Mapped[str | None] = Column(String(300))
    website: Mapped[str | None] = Column(String(200))
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = Column(Boolean, default=True)
    tone_override: Mapped[str | None] = Column(String(120))
    welcome_message: Mapped[str | None] = Column(Text)
    generation_temperature: Mapped[float | None] = Column(Float)
    generation_top_p: Mapped[float | None] = Column(Float)

    faqs: Mapped[List["FAQ"]] = relationship(
        "FAQ",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    document_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="business",
        cascade="all, delete-orphan",
    )


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = Column(Integer, ForeignKey("businesses.id"))
    question: Mapped[str] = Column(String(500), nullable=False)
    answer: Mapped[str] = Column(Text, nullable=False)
    category: Mapped[str | None] = Column(String(100))
    priority: Mapped[int] = Column(Integer, default=0)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    business: Mapped[Business] = relationship("Business", back_populates="faqs")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = Column(Integer, ForeignKey("businesses.id"))
    session_id: Mapped[str] = Column(String(100), nullable=False)
    user_message: Mapped[str] = Column(Text, nullable=False)
    bot_response: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    business: Mapped[Business] = relationship("Business", back_populates="conversations")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    business_id: Mapped[int | None] = Column(Integer, ForeignKey("businesses.id"))
    original_filename: Mapped[str] = Column(String(255), nullable=False)
    content_type: Mapped[str | None] = Column(String(120))
    size_bytes: Mapped[int] = Column(Integer, nullable=False)
    status: Mapped[str] = Column(String(40), default="processed")
    error_message: Mapped[str | None] = Column(Text)
    storage_path: Mapped[str | None] = Column(String(400))
    uploaded_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    business: Mapped[Business | None] = relationship("Business", back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    business_id: Mapped[int | None] = Column(Integer, ForeignKey("businesses.id"))
    chunk_index: Mapped[int] = Column(Integer, default=0)
    text: Mapped[str] = Column(Text, nullable=False)
    char_length: Mapped[int] = Column(Integer, default=0)
    relevance_score: Mapped[float | None] = Column(Float)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    document: Mapped[Document] = relationship("Document", back_populates="chunks")
    business: Mapped[Business | None] = relationship("Business", back_populates="document_chunks")


__all__ = ["Business", "FAQ", "Conversation", "Document", "DocumentChunk"]
