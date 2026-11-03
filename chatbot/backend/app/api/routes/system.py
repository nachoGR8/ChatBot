"""Generic system routes (status, health, static helpers)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from ...config import DEFAULT_FAVICON_SVG, FRONTEND_DIR
from ...services.chatbot_service import chatbot_service

router = APIRouter(tags=["system"])


@router.get("/", include_in_schema=False)
async def root(request: Request) -> Response:
    index_path = FRONTEND_DIR / "index.html"
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and index_path.is_file():
        return FileResponse(str(index_path), media_type="text/html")

    data = {
        "msg": "Chatbot Backend funcionando",
        "version": "1.0.0",
        "endpoints": {
            "businesses": "/businesses",
            "chat": "/chat",
            "faqs": "/faqs",
        },
    }
    return JSONResponse(content=data)


@router.get("/favicon.ico", include_in_schema=False)
async def serve_favicon() -> Response:
    candidate_files = []
    if FRONTEND_DIR.is_dir():
        candidate_files = [
            FRONTEND_DIR / "favicon.ico",
            FRONTEND_DIR / "favicon.png",
            FRONTEND_DIR / "favicon.svg",
        ]

    for path in candidate_files:
        if path.is_file():
            media_type = "image/x-icon"
            if path.suffix == ".svg":
                media_type = "image/svg+xml"
            elif path.suffix == ".png":
                media_type = "image/png"
            return FileResponse(str(path), media_type=media_type)

    return Response(content=DEFAULT_FAVICON_SVG, media_type="image/svg+xml")


@router.get("/admin.html", include_in_schema=False)
async def serve_admin_html() -> FileResponse:
    admin_path = FRONTEND_DIR / "admin.html"
    if admin_path.is_file():
        return FileResponse(str(admin_path), media_type="text/html")
    raise HTTPException(status_code=404, detail="admin.html no encontrado")


@router.get("/status")
def status() -> dict[str, object]:
    return {"ok": True, "status": chatbot_service.status()}


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow(),
    }
