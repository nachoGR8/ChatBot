from fastapi.testclient import TestClient

from typing import List

from backend.main import (
    Business,
    ChatbotService,
    Conversation,
    FAQ,
    SessionLocal,
    app,
    chatbot_service,
)


def test_chat_returns_matching_faq_answer():
    client = TestClient(app)
    db = SessionLocal()
    answer_text = "Abrimos de lunes a viernes de 06:00 a 23:00."
    session_id = "test-faq-session"

    business = Business(
        name="Test Gym",
        business_type="gym",
        phone="+34 600 000 001",
        email="test@example.com",
        address="Calle Test 123",
        website="www.test.com",
    )

    try:
        db.add(business)
        db.commit()
        db.refresh(business)

        faq = FAQ(
            business_id=business.id,
            question="¿Cuál es vuestro horario?",
            answer=answer_text,
            priority=10,
        )
        db.add(faq)
        db.commit()

        # Evitar que el endpoint devuelva mensaje de inicialización del modelo
        chatbot_service.model = object()
        chatbot_service.model_failed = False
        chatbot_service._initializing = False

        payload = {
            "business_id": business.id,
            "session_id": session_id,
            "message": "¿Cuál es vuestro horario?",
        }

        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == answer_text

        # Se guarda conversación
        stored = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id, Conversation.business_id == business.id)
            .first()
        )
        assert stored is not None
        assert stored.bot_response == answer_text

    finally:
        # Limpieza de datos
        try:
            db.query(Conversation).filter(Conversation.session_id == session_id).delete()
            db.query(FAQ).filter(FAQ.business_id == business.id).delete()
            db.delete(business)
            db.commit()
        except Exception:
            db.rollback()
        chatbot_service.model = None
        db.close()


def test_format_history_limits_turns_and_truncates():
    service = ChatbotService()
    service.max_history_turns = 2
    service.history_message_max_chars = 12

    history_items = [
        Conversation(
            business_id=1,
            session_id="s",
            user_message="Primer mensaje muy largo",  # debería truncar
            bot_response="Respuesta uno también larga",
        ),
        Conversation(
            business_id=1,
            session_id="s",
            user_message="Segundo mensaje",
            bot_response="Respuesta dos",
        ),
        Conversation(
            business_id=1,
            session_id="s",
            user_message="Tercero",
            bot_response="Respuesta tres",
        ),
    ]

    text = service.format_history(history_items)

    # Solo debe incluir los dos últimos turnos (Cliente aparece dos veces)
    assert text.count("Cliente:") == 2
    # Se espera truncamiento con elipsis
    assert "…" in text


def test_build_context_uses_custom_tone_and_welcome():
    service = ChatbotService()
    biz = Business(
        name="Cafe Alegre",
        business_type="restaurant",
        tone_override="Habla como un barista entusiasta con guiños a la carta.",
        welcome_message="¡Bienvenido a Cafe Alegre! ☕ ¿Listo para algo delicioso?",
        website="https://cafealegre.test",
    )

    context = service.build_context(biz, faqs=[], max_faqs=2)

    assert "Habla como un barista entusiasta" in context
    assert "MENSAJE DE BIENVENIDA" in context
    assert "https://cafealegre.test" in context


def test_extract_customer_name_from_history():
    service = ChatbotService()
    history = [
        Conversation(
            business_id=1,
            session_id="s1",
            user_message="Hola, me llamo ignacio",
            bot_response="Encantado",
        ),
        Conversation(
            business_id=1,
            session_id="s1",
            user_message="Gracias",
            bot_response="Un placer",
        ),
    ]

    detected = service.extract_customer_name(history, None)
    assert detected == "Ignacio"


def test_extract_customer_name_from_current_message():
    service = ChatbotService()
    history: List[Conversation] = []
    detected = service.extract_customer_name(history, "Soy Laura, necesito ayuda")
    assert detected == "Laura"


def test_is_recommendation_request_detects_keywords():
    service = ChatbotService()
    assert service.is_recommendation_request("¿Qué me recomiendas para cenar?")
    assert service.is_recommendation_request("¿Puedes sugerirme algo especial hoy?")
    assert service.is_recommendation_request("Aconséjame un plan para entrenar")


def test_is_recommendation_request_ignores_other_queries():
    service = ChatbotService()
    assert not service.is_recommendation_request("Necesito información sobre los precios")
    assert not service.is_recommendation_request("")
    assert not service.is_recommendation_request(None)


def test_get_response_handles_repeated_greeting_with_name():
    service = ChatbotService()

    # Evitar carga del modelo durante la prueba
    service.initialize_model = lambda: None  # type: ignore

    # Con suppress_greeting y nombre, debe devolver una respuesta directa sin usar el modelo
    response = service.get_response(
        message="hola",
        context="Información del negocio",
        suppress_greeting=True,
        customer_name="Ignacio",
        welcome_message=None,
    )

    assert "Ignacio" in response
    assert "hola" not in response.lower().split()[0]


def test_get_response_avoids_reusing_name_when_already_used():
    service = ChatbotService()

    service.initialize_model = lambda: None  # type: ignore

    response = service.get_response(
        message="hola",
        context="Información del negocio",
        suppress_greeting=True,
        customer_name="Ignacio",
        welcome_message=None,
        name_already_used=True,
    )

    assert "Ignacio" not in response
    assert "hola" not in response.lower().split()[0]
