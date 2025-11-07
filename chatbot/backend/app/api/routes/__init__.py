"""Utility helpers to register API routers."""
from __future__ import annotations

from fastapi import FastAPI

from . import admin, businesses, chat, demo, documents, faqs, system

ROUTERS = [
    system.router,
    businesses.router,
    faqs.router,
    chat.router,
    demo.router,
    documents.router,
    admin.router,
]


def register_routes(app: FastAPI) -> None:
    for router in ROUTERS:
        app.include_router(router)
