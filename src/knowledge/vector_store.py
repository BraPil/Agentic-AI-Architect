"""
Vector Store — FAISS-backed semantic similarity search.

Provides:
  - Document embedding and storage
  - k-NN semantic search across stored embeddings
  - Namespace-based index separation
  - Persistence (save/load FAISS index + metadata)

Embedding strategy (in priority order):
  1. OpenAI text-embedding-3-small (if OPENAI_API_KEY set)
  2. Sentence-Transformers all-MiniLM-L6-v2 (if sentence-transformers installed)
  3. TF-IDF sparse vector fallback (no external dependencies)
"""

import json
import logging
import math
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedding providers (lazy imports)
# ---------------------------------------------------------------------------

def _get_openai_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Get embeddings via OpenAI API."""
    import os  # noqa: PLC0415
    import openai  # noqa: PLC0415

    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]


def _get_sentence_transformer_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings via sentence-transformers."""
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


class TFIDFEmbedder:
    """
    Lightweight TF-IDF based sparse embedder.

    Used as a fallback when no neural embedding provider is available.
    Produces fixed-size dense vectors by hashing terms (random projection).
    """

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim
        self._vocab: dict[str, float] = defaultdict(float)
        self._doc_count: int = 0

    def fit(self, texts: list[str]) -> None:
        """Build IDF weights from a corpus."""
        self._doc_count = len(texts)
        for text in texts:
            seen = set(self._tokenize(text))
            for token in seen:
                self._vocab[token] += 1.0

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts as fixed-size TF-IDF hash vectors."""
        results = []
        for text in texts:
            tokens = self._tokenize(text)
            vec = [0.0] * self._dim
            token_counts: dict[str, int] = defaultdict(int)
            for t in tokens:
                token_counts[t] += 1
            for token, count in token_counts.items():
                idf = math.log((self._doc_count + 1) / (self._vocab.get(token, 0) + 1)) + 1.0
                tf = count / max(len(tokens), 1)
                weight = tf * idf
                # Hash token to bucket in vector
                bucket = hash(token) % self._dim
                vec[bucket] += weight
            # L2 normalise
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            results.append([v / norm for v in vec])
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re  # noqa: PLC0415
        return re.findall(r"\b[a-z]{2,}\b", text.lower())


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------

class VectorStore:
    """
    FAISS-backed vector store with namespace support and persistence.

    Usage::

        vs = VectorStore("data/vector_store")
        vs.initialize()

        vs.add_texts(["FAISS is a library for similarity search", "..."], namespace="tools")
        results = vs.search("vector similarity", namespace="tools", top_k=5)
        vs.save()
        vs.load()
    """

    def __init__(self, store_dir: str = "data/vector_store") -> None:
        self._store_dir = Path(store_dir)
        self._dim: int = 256  # Matches TF-IDF fallback; OpenAI model changes this
        # namespace -> FAISS index (lazy import)
        self._indexes: dict[str, Any] = {}
        # namespace -> list of metadata dicts (parallel to FAISS vectors)
        self._metadata: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._embedder: Any = None
        self._embedding_provider: str = "tfidf"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Detect best available embedding provider and set up indexes."""
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._embedder = self._select_embedder()
        logger.info("VectorStore initialized with embedder: %s", self._embedding_provider)

    def _select_embedder(self) -> Any:
        """Choose the best available embedding provider."""
        import os  # noqa: PLC0415

        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai  # noqa: PLC0415, F401
                self._embedding_provider = "openai"
                self._dim = 1536  # text-embedding-3-small
                logger.info("Using OpenAI embeddings")
                return "openai"
            except ImportError:
                pass

        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415, F401
            self._embedding_provider = "sentence_transformers"
            self._dim = 384  # all-MiniLM-L6-v2
            logger.info("Using sentence-transformers embeddings")
            return "sentence_transformers"
        except ImportError:
            pass

        logger.info("Using TF-IDF fallback embedder (no GPU/API dependencies)")
        self._embedding_provider = "tfidf"
        self._dim = 256
        embedder = TFIDFEmbedder(dim=256)
        return embedder

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add_texts(
        self,
        texts: list[str],
        namespace: str = "default",
        metadata: list[dict[str, Any]] | None = None,
    ) -> int:
        """
        Embed and store texts in the given namespace.

        Args:
            texts: List of text strings to embed.
            namespace: Index namespace (e.g. 'tools', 'frameworks').
            metadata: Optional parallel metadata dicts for each text.

        Returns:
            Number of texts added.
        """
        if not texts:
            return 0

        if metadata is None:
            metadata = [{} for _ in texts]

        embeddings = self._embed(texts)

        try:
            import faiss  # noqa: PLC0415
            import numpy as np  # noqa: PLC0415

            vectors = np.array(embeddings, dtype="float32")
            faiss.normalize_L2(vectors)

            if namespace not in self._indexes:
                self._indexes[namespace] = faiss.IndexFlatIP(self._dim)

            self._indexes[namespace].add(vectors)
            self._metadata[namespace].extend(
                {**m, "_text": t} for t, m in zip(texts, metadata, strict=True)
            )
        except ImportError:
            # FAISS not installed — store in memory as plain list for basic search
            logger.debug("FAISS not available; using in-memory list search")
            if namespace not in self._indexes:
                self._indexes[namespace] = {"vectors": [], "texts": []}
            self._indexes[namespace]["vectors"].extend(embeddings)
            self._indexes[namespace]["texts"].extend(texts)
            self._metadata[namespace].extend(
                {**m, "_text": t} for t, m in zip(texts, metadata, strict=True)
            )

        return len(texts)

    def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Semantic search for the most similar texts.

        Args:
            query: Search query text.
            namespace: Index namespace to search in.
            top_k: Number of results to return.
            min_score: Minimum cosine similarity score.

        Returns:
            List of dicts with 'text', 'score', and original metadata keys.
        """
        if namespace not in self._indexes or not self._metadata.get(namespace):
            return []

        query_embedding = self._embed([query])[0]

        try:
            import faiss  # noqa: PLC0415
            import numpy as np  # noqa: PLC0415

            q_vec = np.array([query_embedding], dtype="float32")
            faiss.normalize_L2(q_vec)
            scores, indices = self._indexes[namespace].search(q_vec, min(top_k, self._indexes[namespace].ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0], strict=True):
                if idx < 0 or score < min_score:
                    continue
                meta = self._metadata[namespace][idx].copy()
                text = meta.pop("_text", "")
                results.append({"text": text, "score": float(score), **meta})
            return results

        except ImportError:
            # Fallback: brute-force cosine similarity
            return self._brute_force_search(query_embedding, namespace, top_k, min_score)

    def _brute_force_search(
        self,
        query_vec: list[float],
        namespace: str,
        top_k: int,
        min_score: float,
    ) -> list[dict[str, Any]]:
        """Brute-force cosine similarity search for FAISS-free environments."""
        index_data = self._indexes.get(namespace, {})
        vectors: list[list[float]] = index_data.get("vectors", [])
        if not vectors:
            return []

        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=True))
            norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
            norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
            return dot / (norm_a * norm_b)

        scored = [
            (cosine(query_vec, vec), i)
            for i, vec in enumerate(vectors)
            if cosine(query_vec, vec) >= min_score
        ]
        scored.sort(reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            meta = self._metadata[namespace][idx].copy()
            text = meta.pop("_text", "")
            results.append({"text": text, "score": score, **meta})
        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Save indexes and metadata to disk."""
        try:
            import faiss  # noqa: PLC0415

            for namespace, index in self._indexes.items():
                faiss.write_index(index, str(self._store_dir / f"{namespace}.faiss"))
        except ImportError:
            # Save vectors as pickle for the fallback store
            with (self._store_dir / "indexes.pkl").open("wb") as f:
                pickle.dump(self._indexes, f)

        with (self._store_dir / "metadata.json").open("w") as f:
            json.dump(dict(self._metadata), f, indent=2)

        logger.info("VectorStore saved to %s", self._store_dir)

    def load(self) -> None:
        """Load indexes and metadata from disk."""
        meta_path = self._store_dir / "metadata.json"
        if meta_path.exists():
            with meta_path.open() as f:
                data = json.load(f)
                self._metadata = defaultdict(list, data)

        try:
            import faiss  # noqa: PLC0415

            for faiss_file in self._store_dir.glob("*.faiss"):
                namespace = faiss_file.stem
                self._indexes[namespace] = faiss.read_index(str(faiss_file))
        except ImportError:
            pkl_path = self._store_dir / "indexes.pkl"
            if pkl_path.exists():
                with pkl_path.open("rb") as f:
                    self._indexes = pickle.load(f)  # noqa: S301

        logger.info("VectorStore loaded from %s", self._store_dir)

    # ------------------------------------------------------------------
    # Embedding dispatch
    # ------------------------------------------------------------------

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using the selected provider."""
        if self._embedding_provider == "openai":
            return _get_openai_embeddings(texts)
        if self._embedding_provider == "sentence_transformers":
            return _get_sentence_transformer_embeddings(texts)
        # TF-IDF fallback
        return self._embedder.embed(texts)
