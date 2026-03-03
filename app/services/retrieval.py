import logging
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sqlalchemy.orm import Session

from app.models import Chunk

logger = logging.getLogger("retrieval")


class TFIDFRetriever:
    def __init__(self, max_features: int = 20000):
        self.vectorizer = TfidfVectorizer(max_features=max_features)

    def retrieve(
        self,
        db: Session,
        tenant_id: str,
        question: str,
        top_k: int,
    ) -> List[Tuple[Chunk, float]]:
        chunks: List[Chunk] = (
            db.query(Chunk)
            .filter(Chunk.tenant_id == tenant_id)
            .order_by(Chunk.id)
            .all()
        )
        if not chunks:
            logger.info("检索时未找到任何分片 tenant_id=%s", tenant_id)
            return []

        question = (question or "").strip()
        if not question:
            return []

        top_k = int(top_k) if top_k else 4
        if top_k <= 0:
            top_k = 4

        texts = [c.text for c in chunks]
        corpus = texts + [question]

        logger.info("开始 TF-IDF 检索 tenant_id=%s chunk_count=%s", tenant_id, len(chunks))

        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        question_vec = tfidf_matrix[-1]
        chunk_matrix = tfidf_matrix[:-1]

        similarities = linear_kernel(question_vec, chunk_matrix).flatten()

        indexed_scores = list(enumerate(similarities))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        top_results: List[Tuple[Chunk, float]] = []
        for idx, score in indexed_scores[: max(top_k, 1)]:
            top_results.append((chunks[idx], float(score)))

        logger.info(
            "TF-IDF 检索完成 tenant_id=%s top_k=%s best_score=%.4f",
            tenant_id,
            top_k,
            top_results[0][1] if top_results else 0.0,
        )
        return top_results


retriever = TFIDFRetriever()