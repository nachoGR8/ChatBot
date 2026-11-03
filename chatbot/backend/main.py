"""FastAPI application entrypoint for the chatbot backend."""
from __future__ import annotations

import argparse
import io
import os
import sys

# Configurar UTF-8 en Windows para que los emojis funcionen correctamente
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass  # Si falla, continuar sin emojis

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .app.api.routes import register_routes
from .app.config import FRONTEND_DIR, configure_logging
from .app.database import init_db
from .app.services.chatbot_service import chatbot_service

logger = configure_logging()
init_db()

app = FastAPI(
    title="Chatbot Backend API",
    description="Backend para chatbot de empresas con IA local",
    version="1.0.0",
)

if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# El widget se incrusta en webs de terceros, por eso "*" por defecto.
# En producción: CHATBOT_CORS_ORIGINS=https://minegocio.com,https://www.minegocio.com
CORS_ORIGINS = [o.strip() for o in os.getenv("CHATBOT_CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-API-KEY"],
)

register_routes(app)

# Debe ir después de las rutas de la API: sirve demo.html, widget.js, etc. desde la raíz.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.on_event("startup")
def preload_model_on_startup() -> None:
    if os.getenv("CHATBOT_PRELOAD", "0") != "1":
        logger.info("[startup] Preload de modelo omitido (CHATBOT_PRELOAD!=1). Se cargará on-demand en /chat.")
        return
    try:
        logger.info("[startup] Preload de modelo solicitado (CHATBOT_PRELOAD=1)")
        chatbot_service.initialize_model()
    except Exception:
        logger.exception("[startup] modelo no pudo inicializarse en preload; se intentará lazy en /chat")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Chatbot backend or initialize database")
    parser.add_argument("--init-db", action="store_true", help="Only initialize the database (create tables) and exit")
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

    uvicorn.run("backend.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
