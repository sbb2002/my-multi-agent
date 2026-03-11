import numpy as np
from services.request import request_embedding


def measure_cosine_similarity(emb_a, emb_b):
    """진술 A, B를 임베딩 처리한 것을 바탕으로 cosine similarity를 계산하는 메서드."""
    emb_a = np.array(emb_a)
    emb_b = np.array(emb_b)
    return np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b))


def get_similarity(question: str, summary: str) -> float:
    """질문-요약 간 cosine similarity를 반환하는 메서드."""
    emb_message = request_embedding(question)
    emb_summary = request_embedding(summary)
    return measure_cosine_similarity(emb_message, emb_summary)