"""FastAPI dependencies shared across routers."""
from __future__ import annotations

import hmac
import logging
import os
import threading
import time
from collections import defaultdict, deque
from typing import Iterator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..database import SessionLocal

logger = logging.getLogger("chatbot")


def verify_admin_api_key(request: Request) -> bool:
    """Exige la cabecera X-API-KEY en las rutas de administración.

    Fail-closed: si el servidor no tiene ADMIN_API_KEY, la administración queda deshabilitada (503)
    en vez de abierta a cualquiera. Se lee en cada petición para poder cambiarla sin reiniciar el proceso.
    """
    expected = os.getenv("ADMIN_API_KEY") or ""
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Administración deshabilitada: define ADMIN_API_KEY en el servidor.",
        )
    key = request.headers.get("x-api-key") or ""
    if not hmac.compare_digest(key.encode("utf-8"), expected.encode("utf-8")):
        logger.warning("Clave de administración incorrecta o ausente desde %s", client_ip(request))
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-KEY")
    return True


def client_ip(request: Request) -> str:
    """IP del cliente. Detrás de un proxy (CHATBOT_TRUST_PROXY=1) se usa X-Forwarded-For."""
    if os.getenv("CHATBOT_TRUST_PROXY", "0") == "1":
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconocida"


class RateLimiter:
    """Ventana deslizante en memoria: como mucho `limit` peticiones por IP cada `window` segundos.

    Suficiente para un único proceso (la generación ya está serializada); con varios procesos haría falta Redis.
    """

    def __init__(self, limit: int, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def retry_after(self, key: str) -> int:
        """0 si la petición puede pasar (y la cuenta); si no, segundos hasta que vuelva a poder."""
        if self.limit <= 0:
            return 0
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(1, int(self.window - (now - hits[0])) + 1)
            hits.append(now)
            if len(self._hits) > 10_000:  # evita crecer sin límite con muchas IPs distintas
                for ip in [ip for ip, h in self._hits.items() if not h]:
                    del self._hits[ip]
            return 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


chat_rate_limiter = RateLimiter(int(os.getenv("CHATBOT_RATE_LIMIT_PER_MIN", "20")))


def limit_chat_rate(request: Request) -> None:
    """Dependencia de /chat y /chat/stream: 429 si una IP supera CHATBOT_RATE_LIMIT_PER_MIN (0 = sin límite)."""
    wait = chat_rate_limiter.retry_after(client_ip(request))
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Demasiados mensajes seguidos. Espera un momento y vuelve a intentarlo.",
            headers={"Retry-After": str(wait)},
        )


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
