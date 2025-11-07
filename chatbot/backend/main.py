"""FastAPI application entrypoint for the chatbot backend."""
from __future__ import annotations

import argparse
import os
import sys
import io

# Configurar UTF-8 en Windows para que los emojis funcionen correctamente
if sys.platform == 'win32':
    try:
        # Configurar la salida estándar y error para UTF-8
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Intentar configurar la página de códigos de la consola a UTF-8
        os.system('chcp 65001 >nul 2>&1')
    except Exception:
        pass  # Si falla, continuar sin emojis

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .app.api.routes import register_routes
from .app.config import FRONTEND_DIR, configure_logging
from .app.database import SessionLocal, init_db
from .app.models import Business, Conversation, Document, DocumentChunk, FAQ
from .app.services.chatbot_service import ChatbotService, chatbot_service


logger = configure_logging()
init_db()


app = FastAPI(
    title="Chatbot Backend API",
    description="Backend para chatbot de empresas con IA local",
    version="1.0.0",
)


if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_routes(app)


@app.on_event("startup")
def preload_model_on_startup() -> None:
    if os.getenv("CHATBOT_PRELOAD", "0") != "1":
        logger.info(
            "[startup] Preload de modelo omitido (CHATBOT_PRELOAD!=1). Se cargará on-demand en /chat."
        )
        return
    try:
        logger.info("[startup] Preload de modelo solicitado (CHATBOT_PRELOAD=1)")
        chatbot_service.initialize_model()
    except Exception:
        logger.exception("[startup] modelo no pudo inicializarse en preload; se intentará lazy en /chat")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Chatbot backend or initialize database"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Only initialize the database (create tables) and exit",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind uvicorn")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind uvicorn")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload")
    return parser.parse_args()


def main() -> None:
    os.environ.setdefault("CHATBOT_PRELOAD", "1")
    args = _parse_args()
    if args.init_db:
        init_db()
        return

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "app",
    "main",
    "Business",
    "FAQ",
    "Conversation",
    "Document",
    "DocumentChunk",
    "SessionLocal",
    "ChatbotService",
    "chatbot_service",
]
