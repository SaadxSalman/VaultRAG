from dataclasses import asdict
from pathlib import Path
import json
import uuid

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .ingestion import Chunk


class LocalIndex:
    """FAISS-ready local index with a reliable TF-IDF fallback for first run/offline use."""

    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.metadata_path = index_dir / "metadata.json"
        self.chunks: list[Chunk] = []
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = None
        self._load()

    @property
    def backend_name(self) -> str:
        return "tfidf-local"

    def _load(self) -> None:
        if self.metadata_path.exists():
            self.chunks = [Chunk(**item) for item in json.loads(self.metadata_path.read_text())]
            if self.chunks:
                self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in self.chunks])

    def add(self, chunks: list[Chunk]) -> int:
        self.chunks.extend(chunks)
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in self.chunks])
        self.index_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.metadata_path.with_suffix(".json.tmp")
        temporary_path.write_text(json.dumps([asdict(chunk) for chunk in self.chunks], indent=2), encoding="utf-8")
        temporary_path.replace(self.metadata_path)
        return len(chunks)

    def search(self, query: str, top_k: int) -> list[dict]:
        if not self.chunks or self.matrix is None:
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        ranked = np.argsort(scores)[::-1][:top_k]
        return [{"rank": rank, "chunk": asdict(self.chunks[index]), "score": round(float(scores[index]), 4)} for rank, index in enumerate(ranked, start=1) if scores[index] > 0]

    def clear(self) -> None:
        self.chunks = []
        self.matrix = None
        if self.metadata_path.exists():
            self.metadata_path.unlink()


def new_document_id() -> str:
    return uuid.uuid4().hex[:12]
