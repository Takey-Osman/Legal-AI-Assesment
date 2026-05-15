from __future__ import annotations

from typing import Iterable, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import DocumentChunk, RetrievedEvidence


class TfidfRetriever:
    """Simple grounded retrieval layer.

    TF-IDF is not state-of-the-art, but it is transparent, fast, cheap, and works offline.
    The class can later be swapped with FAISS/Chroma + sentence embeddings.
    """

    def __init__(self, chunks: Iterable[DocumentChunk]):
        self.chunks: List[DocumentChunk] = list(chunks)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        corpus = [chunk.text for chunk in self.chunks] or [""]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, k: int = 5) -> List[RetrievedEvidence]:
        if not self.chunks:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)[:k]

        evidence: List[RetrievedEvidence] = []
        for rank, (idx, score) in enumerate(ranked, start=1):
            chunk = self.chunks[idx]
            evidence.append(
                RetrievedEvidence(
                    evidence_id=f"E{rank}",
                    chunk_id=chunk.chunk_id,
                    source_file=chunk.source_file,
                    page=chunk.page,
                    score=float(score),
                    text=chunk.text,
                )
            )
        return evidence
