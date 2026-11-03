"""Fixtures: BD SQLite temporal y un modelo falso, así los tests no necesitan GGUF ni red."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="chatbot-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["CHATBOT_PRELOAD"] = "0"
os.environ["CHATBOT_WARMUP"] = "0"
os.environ.setdefault("ADMIN_API_KEY", "test-key")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


class FakeLlama:
    """Imita la parte de llama_cpp.Llama que usa el servicio."""

    def __init__(self, reply: str = "Respuesta de prueba."):
        self.reply = reply
        self.calls = 0

    def create_chat_completion(self, messages, stream=False, **_):
        self.calls += 1
        if stream:
            return ({"choices": [{"delta": {"content": w + " "}}]} for w in self.reply.split())
        return {"choices": [{"message": {"content": self.reply}}]}


@pytest.fixture(scope="session")
def app():
    from backend.main import app as fastapi_app

    return fastapi_app


@pytest.fixture()
def fake_model():
    from backend.app.services.chatbot_service import chatbot_service as svc

    model = FakeLlama()
    svc.model, svc._backend, svc.model_failed = model, "llama_cpp", False
    svc._reply_cache.clear()
    yield model
    svc.model = None


@pytest.fixture()
def business(app):
    from backend.app.database import SessionLocal
    from backend.app.models import FAQ, Business, Conversation

    db = SessionLocal()
    db.query(Conversation).delete()
    db.query(FAQ).delete()
    db.query(Business).delete()
    biz = Business(name="Ignacio Demo", business_type="portfolio", phone="600000000")
    db.add(biz)
    db.flush()
    db.add_all(
        [
            FAQ(business_id=biz.id, question="¿Qué tecnologías usa?", answer="Python, FastAPI y SQL.", priority=0),
            FAQ(business_id=biz.id, question="¿Qué certificaciones tiene?", answer="Ninguna todavía.", priority=0),
        ]
    )
    db.commit()
    biz_id = biz.id
    db.close()
    return biz_id


@pytest.fixture()
def client(app, monkeypatch):
    from fastapi.testclient import TestClient

    async def no_delay():
        return None

    monkeypatch.setattr("backend.app.api.routes.chat._natural_delay", no_delay)
    with TestClient(app) as c:
        yield c
