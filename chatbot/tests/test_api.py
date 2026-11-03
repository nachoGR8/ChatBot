import json

ADMIN = {"X-API-KEY": "test-key"}


def stream_events(client, payload):
    with client.stream("POST", "/chat/stream", json=payload) as r:
        assert r.status_code == 200
        body = "".join(r.iter_text())
    return [json.loads(l[5:]) for l in body.splitlines() if l.startswith("data:")]


def payload(biz, text, session="t1"):
    return {"business_id": biz, "session_id": session, "message": text}


def test_health(client):
    assert client.get("/health").status_code == 200


def test_unknown_business_is_404(client, fake_model):
    assert client.post("/chat", json=payload(9999, "hola")).status_code == 404


def test_chat_uses_model_and_saves_conversation(client, fake_model, business):
    r = client.post("/chat", json=payload(business, "Cuéntame algo sobre tu experiencia con bases de datos"))
    assert r.status_code == 200
    assert r.json()["response"]
    saved = client.get(f"/conversations/{business}", headers=ADMIN)
    assert saved.status_code == 200 and len(saved.json()) >= 1


def test_direct_faq_skips_the_model(client, fake_model, business):
    r = client.post("/chat", json=payload(business, "¿Qué tecnologías usa?"))
    assert "FastAPI" in r.json()["response"]
    assert fake_model.calls == 0


def test_stream_emits_deltas_then_final(client, fake_model, business):
    events = stream_events(client, payload(business, "Háblame de tus proyectos de ingeniería"))
    assert events[-1].get("done") is True and events[-1]["final"]
    assert any("delta" in e for e in events[:-1])


def test_stream_second_identical_question_is_cached(client, fake_model, business):
    q = payload(business, "Háblame de tus proyectos de ingeniería", "s-cache")
    stream_events(client, q)
    calls = fake_model.calls
    events = stream_events(client, {**q, "session_id": "s-cache-2"})
    assert fake_model.calls == calls  # sin llamar al modelo
    assert events[-1]["final"]


def test_stream_direct_faq(client, fake_model, business):
    events = stream_events(client, payload(business, "¿Qué tecnologías usa?"))
    assert "FastAPI" in events[-1]["final"] and fake_model.calls == 0


