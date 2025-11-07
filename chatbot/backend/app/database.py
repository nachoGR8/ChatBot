"""Database utilities for the chatbot backend."""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Column, create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger("chatbot")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


EXPECTED_BUSINESS_COLUMNS = {
    "tone_override": "TEXT",
    "welcome_message": "TEXT",
    "generation_temperature": "FLOAT",
    "generation_top_p": "FLOAT",
}


def ensure_business_custom_columns(engine_ref=engine) -> None:
    """Make sure optional columns exist in the businesses table."""
    try:
        with engine_ref.connect() as conn:
            info = conn.execute(text("PRAGMA table_info(businesses)")).fetchall()
            existing = {row[1] for row in info}
            for column, sql_type in EXPECTED_BUSINESS_COLUMNS.items():
                if column not in existing:
                    try:
                        conn.execute(text(f"ALTER TABLE businesses ADD COLUMN {column} {sql_type}"))
                    except Exception:
                        logger.exception("No se pudo añadir la columna %s a businesses", column)
    except Exception:
        logger.exception("Error comprobando columnas personalizadas de businesses")


def init_db() -> None:
    """Initialize the database schema and ensure required columns exist."""
    from . import models  # noqa: F401  # Import required for model registration

    Base.metadata.create_all(bind=engine)
    ensure_business_custom_columns(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
