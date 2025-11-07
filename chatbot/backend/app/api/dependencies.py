"""FastAPI dependencies shared across routers."""
from __future__ import annotations

import logging
from typing import Iterator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..config import ADMIN_API_KEY
from ..database import SessionLocal

logger = logging.getLogger("chatbot")
_admin_key_warning_emitted = False


def verify_admin_api_key(request: Request) -> bool:
    """Validate the X-API-KEY header for admin endpoints."""
    global _admin_key_warning_emitted

    if ADMIN_API_KEY is None:
        if not _admin_key_warning_emitted:
            logger.warning(
                "ADMIN_API_KEY no definida; permitiendo petición administrativa sin clave (solo para desarrollo)."
            )
            _admin_key_warning_emitted = True
        return True

    key = (
        request.headers.get("x-api-key")
        or request.headers.get("x_api_key")
        or request.headers.get("X-API-KEY")
    )
    if not key or key != ADMIN_API_KEY:
        masked = (key[:4] + "..." + key[-4:]) if key and len(key) > 8 else key
        logger.warning("Admin API key invalid or missing. Received: %s", masked)
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-KEY")
    return True


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
