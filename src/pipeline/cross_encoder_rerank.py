"""
Cross-encoder reranking — an optional second stage that re-scores top candidates with a
query-document cross-encoder.

Bi-encoder retrieval (the store's `all-MiniLM-L6-v2` embeddings) encodes query and document
*independently*, so it misses fine-grained interactions. A cross-encoder scores the (query,
document) *pair* jointly and is markedly more accurate at ordering — at a cost: it runs the
transformer once per candidate, so it only reranks a small top-k, and it adds latency and a
model load.

This stage sits after hybrid lexical+vector ranking: hybrid (cheap) selects and orders the
candidate pool; the cross-encoder (expensive, accurate) re-orders the top-k of that pool. The
reported `score` stays the vector similarity; the cross-encoder only changes order and attaches
`cross_encoder_score` for audit.

**Optional + graceful.** The model (`sentence-transformers` CrossEncoder) is a heavy optional
dependency loaded lazily; if it is unavailable (not installed, no model, offline), reranking is
a no-op and the hybrid order stands. **Off by default** — enable with `AAA_CROSS_ENCODER=1`.
Default model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (small, ~80MB).

Latency note: cross-encoding ~20 candidates on CPU is tens-to-~150ms, which can approach the
< 200ms cached-query budget — another reason it is opt-in.
"""

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_TOP_K = 20  # rerank at most this many top candidates (cost is linear in this)


def reorder_by_scores(hits: list[dict], ce_scores: list[float], top_k: int) -> list[dict]:
    """
    Re-order the first `top_k` hits by their cross-encoder scores; leave the tail untouched.

    Pure function (no model) — the reranker's ordering logic, testable in isolation. Each
    reranked hit gains `cross_encoder_score`; `score` is preserved. Stable within ties.
    """
    if len(hits) < 2 or not ce_scores:
        return hits
    k = min(top_k, len(hits), len(ce_scores))
    head = list(hits[:k])
    for h, s in zip(head, ce_scores[:k]):
        h["cross_encoder_score"] = round(float(s), 6)
    # Stable sort by CE score desc, preserving incoming order on ties.
    head_sorted = sorted(head, key=lambda h: h["cross_encoder_score"], reverse=True)
    return head_sorted + list(hits[k:])


class CrossEncoderReranker:
    """
    Lazy, optional cross-encoder reranker. Construct freely (cheap); the model loads on first
    use. If the model can't load, `available` is False and `rerank_hits` is a no-op.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, top_k: int = DEFAULT_TOP_K) -> None:
        self.model_name = model_name
        self.top_k = top_k
        self._model = None
        self._load_attempted = False
        self._available = False

    def _load(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            from sentence_transformers import CrossEncoder  # noqa: PLC0415
            self._model = CrossEncoder(self.model_name)
            self._available = True
            logger.info("CrossEncoderReranker loaded model %s", self.model_name)
        except Exception as exc:  # noqa: BLE001 — any failure → graceful no-op
            logger.warning(
                "CrossEncoderReranker unavailable (%s) — falling back to upstream order.", exc
            )
            self._available = False

    @property
    def available(self) -> bool:
        self._load()
        return self._available

    def score(self, query: str, documents: list[str]) -> list[float]:
        """Cross-encoder relevance score for each (query, document) pair. [] if unavailable."""
        self._load()
        if not self._available or not documents:
            return []
        pairs = [[query, d] for d in documents]
        return [float(s) for s in self._model.predict(pairs)]

    def rerank_hits(self, query: str, hits: list[dict], doc_key: str = "document") -> list[dict]:
        """
        Re-order the top-k hits by cross-encoder score. No-op (returns hits unchanged) when the
        model is unavailable or there are fewer than two hits.
        """
        self._load()
        if not self._available or len(hits) < 2:
            return hits
        k = min(self.top_k, len(hits))
        ce_scores = self.score(query, [hits[i].get(doc_key, "") for i in range(k)])
        if not ce_scores:
            return hits
        return reorder_by_scores(hits, ce_scores, self.top_k)


# Process-wide singleton so the model loads at most once.
_RERANKER: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    """Return the shared reranker (constructed once; model still loads lazily)."""
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoderReranker()
    return _RERANKER


def enabled() -> bool:
    """True if cross-encoder reranking is switched on (AAA_CROSS_ENCODER=1)."""
    return os.environ.get("AAA_CROSS_ENCODER", "0") == "1"
