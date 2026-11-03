import time

import pytest

from backend.app.api.dependencies import RateLimiter, chat_rate_limiter

ADMIN = {"X-API-KEY": "test-key"}


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/businesses", {"name": "Intruso"}),
        ("delete", "/businesses/1", None),
        ("put", "/businesses/1", {"name": "x"}),
        ("patch", "/businesses/1", {"name": "x"}),
        ("post", "/faqs", {"business_id": 1, "question": "q", "answer": "a"}),
        ("delete", "/faqs/1", None),
        ("post", "/seed-demo", None),
        ("get", "/conversations/1", None),
        ("get", "/admin/config", None),
        ("post", "/api/train-ia", None),
    ],
)
def test_admin_routes_reject_missing_or_wrong_key(client, method, path, body):
    kwargs = {"json": body} if body is not None else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401
    assert getattr(client, method)(path, headers={"X-API-KEY": "mala"}, **kwargs).status_code == 401


def test_admin_is_disabled_without_server_key(client, monkeypatch):
    # Fail-closed: sin ADMIN_API_KEY no se puede administrar (antes quedaba abierto a cualquiera).
    monkeypatch.delenv("ADMIN_API_KEY")
    assert client.post("/businesses", json={"name": "x"}, headers=ADMIN).status_code == 503


def test_admin_with_key_works(client, business):
    r = client.post("/faqs", json={"business_id": business, "question": "¿Horario?", "answer": "9-14"}, headers=ADMIN)
    assert r.status_code == 200


def test_public_reads_need_no_key(client, business):
    assert client.get("/businesses").status_code == 200
    assert client.get(f"/faqs?business_id={business}").status_code == 200


def test_chat_rate_limit_returns_429_with_retry_after(client, fake_model, business, monkeypatch):
    monkeypatch.setattr(chat_rate_limiter, "limit", 2)
    body = {"business_id": business, "session_id": "rl", "message": "¿Qué tecnologías usa?"}
    assert client.post("/chat", json=body).status_code == 200
    assert client.post("/chat/stream", json=body).status_code == 200  # comparten el mismo cupo
    r = client.post("/chat", json=body)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1


@pytest.mark.parametrize("message", ["", "x" * 1001])
def test_chat_rejects_empty_or_huge_messages(client, business, message):
    body = {"business_id": business, "session_id": "len", "message": message}
    assert client.post("/chat", json=body).status_code == 422
    assert client.post("/chat/stream", json=body).status_code == 422


def test_rate_limiter_window_expires_and_ips_are_independent():
    limiter = RateLimiter(limit=1, window=0.05)
    assert limiter.retry_after("a") == 0
    assert limiter.retry_after("a") > 0
    assert limiter.retry_after("b") == 0  # otra IP no se ve afectada
    time.sleep(0.06)
    assert limiter.retry_after("a") == 0


def test_rate_limiter_zero_disables():
    limiter = RateLimiter(limit=0)
    assert all(limiter.retry_after("a") == 0 for _ in range(100))


def test_cors_only_allows_needed_headers(client):
    r = client.options(
        "/chat",
        headers={"Origin": "https://cliente.com", "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"},
    )
    assert r.status_code == 200
    assert "content-type" in r.headers["access-control-allow-headers"].lower()
