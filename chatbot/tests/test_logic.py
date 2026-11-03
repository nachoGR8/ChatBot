from types import SimpleNamespace

from backend.app.api.routes.chat import _best_faq_match
from backend.app.services.chatbot_service import ChatbotService, GenerationPlan, chatbot_service
from backend.app.services.document_service import DocumentService


def faq(q, a="x", priority=0):
    return SimpleNamespace(question=q, answer=a, priority=priority)


def test_content_words_strips_accents_and_stopwords():
    words = chatbot_service.content_words("¿Qué estudios tiene Ignacio?")
    assert "estudios" in words and "ignacio" in words
    assert "que" not in words and "qué" not in words


def test_rank_faqs_puts_relevant_first():
    faqs = [faq("¿Qué certificaciones tiene?"), faq("¿Qué tecnologías usa?", "Python")]
    ranked = chatbot_service._rank_faqs(faqs, "¿Qué tecnologías conoce?")
    assert ranked[0].question == "¿Qué tecnologías usa?"


def test_rank_faqs_without_query_uses_priority():
    faqs = [faq("a", priority=1), faq("b", priority=5)]
    assert chatbot_service._rank_faqs(faqs, None)[0].question == "b"


def test_best_faq_match_accepts_rephrasing_and_typos():
    faqs = [faq("¿Qué tecnologías usa?"), faq("¿Qué certificaciones tiene?")]
    assert _best_faq_match(faqs, "que tecnologias usa").question == "¿Qué tecnologías usa?"


def test_best_faq_match_rejects_different_question():
    # Regresión: "estudios" no debe casar con "certificaciones".
    faqs = [faq("¿Qué certificaciones tiene?")]
    assert _best_faq_match(faqs, "¿Qué estudios tiene?") is None


def test_snippet_is_bounded_and_centered_on_query():
    text = ("relleno " * 200) + "Python avanzado con FastAPI " + ("relleno " * 200)
    snippet = DocumentService._snippet_around(text, "¿Sabe python?", 350)
    assert len(snippet) <= 352 and "Python" in snippet


def test_snippet_short_text_untouched():
    assert DocumentService._snippet_around("hola  mundo", "x", 350) == "hola mundo"


def test_reply_cache_hit_and_lru_eviction():
    svc = ChatbotService()
    svc.reply_cache_size = 2
    plans = [GenerationPlan(system="s", user=f"u{i}", max_tokens=10, temperature=0.1, top_p=0.9, wants_menu=False) for i in range(3)]
    svc.store_reply(plans[0], "r0")
    svc.store_reply(plans[1], "r1")
    assert svc.cached_reply(plans[0]) == "r0"  # refresca plans[0]
    svc.store_reply(plans[2], "r2")  # expulsa plans[1]
    assert svc.cached_reply(plans[1]) is None
    assert svc.cached_reply(plans[0]) == "r0" and svc.cached_reply(plans[2]) == "r2"


def test_reply_cache_key_depends_on_every_field():
    base = dict(system="s", user="u", max_tokens=10, temperature=0.1, top_p=0.9, wants_menu=False)
    key = ChatbotService._cache_key(GenerationPlan(**base))
    assert key != ChatbotService._cache_key(GenerationPlan(**{**base, "user": "otro"}))
    assert key != ChatbotService._cache_key(GenerationPlan(**{**base, "temperature": 0.7}))


def test_clean_response_trims_and_keeps_text():
    out = ChatbotService._clean_response("  Trabaja con Python.  ", wants_menu=False)
    assert out == "Trabaja con Python."
