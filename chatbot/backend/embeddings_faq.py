# embeddings_faq.py
from sentence_transformers import SentenceTransformer, util
import torch
from typing import List, Tuple

class EmbeddingFAQMatcher:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        # Modelo multilingüe ligero que funciona en CPU
        self.model = SentenceTransformer(model_name)
        self.faq_questions = []
        self.faq_answers = []
        self.faq_embeddings = None

    def build_index(self, faqs: List[Tuple[str, str]]):
        """
        Construye el índice de embeddings a partir de FAQs
        :param faqs: Lista de (pregunta, respuesta)
        """
        self.faq_embeddings = self.model.encode(self.faq_questions, convert_to_tensor=True)
        self.faq_questions = [q for q, _ in faqs]
        self.faq_answers = [a for _, a in faqs]
        self.faq_embeddings = self.model.encode(self.faq_questions, convert_to_tensor=True)

    def find_best_match(self, user_input: str, threshold: float = 0.65):
        """
        Busca la mejor coincidencia semántica
        :param user_input: Texto del usuario
        :param threshold: Umbral de similitud
        :return: (respuesta, score) o (None, score)
        """
        def find_best_match(self, user_input: str, threshold: float = 0.65):
            if self.faq_embeddings is None or len(self.faq_questions) == 0:
                return None, 0.0


        user_emb = self.model.encode(user_input, convert_to_tensor=True)
        scores = util.cos_sim(user_emb, self.faq_embeddings)[0]
        best_score, idx = torch.max(scores, dim=0)

        if best_score >= threshold:
            return self.faq_answers[idx], float(best_score)
        return None, float(best_score)
