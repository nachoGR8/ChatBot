"""Application configuration and logging utilities."""
from __future__ import annotations

import logging
import os
from pathlib import Path

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
LOG_DIR = PROJECT_ROOT / "logs"
STORAGE_DIR = PROJECT_ROOT / "storage"
DOCUMENTS_DIR = STORAGE_DIR / "documents"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Environment driven flags
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# Default favicon content used if no file exists in the frontend directory
DEFAULT_FAVICON_SVG = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"64\" height=\"64\" viewBox=\"0 0 64 64\">
    <defs>
        <linearGradient id=\"bg\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"100%\">
            <stop offset=\"0%\" stop-color=\"#0ea5e9\" />
            <stop offset=\"100%\" stop-color=\"#2563eb\" />
        </linearGradient>
    </defs>
    <rect width=\"64\" height=\"64\" rx=\"14\" fill=\"url(#bg)\" />
    <text x=\"50%\" y=\"58%\" font-size=\"34\" font-family=\"Segoe UI, Arial, sans-serif\" font-weight=\"700\" text-anchor=\"middle\" fill=\"#ffffff\">C</text>
</svg>
"""


def ensure_directories() -> None:
    """Create directories that should always be present."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Best effort; logging configuration will still attempt to use the file handler.
        pass

    try:
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def configure_logging() -> logging.Logger:
    """Configure root logging for the backend application."""
    ensure_directories()

    log_path = LOG_DIR / "chatbot.log"
    logger = logging.getLogger("chatbot")

    if not logger.handlers:
        # Configurar el StreamHandler con encoding UTF-8 para Windows
        import sys
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        
        # Configurar el formato sin emojis para compatibilidad con Windows
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        stream_handler.setFormatter(formatter)
        
        # Configurar el FileHandler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            handlers=[file_handler, stream_handler]
        )
        logger = logging.getLogger("chatbot")
    return logger
