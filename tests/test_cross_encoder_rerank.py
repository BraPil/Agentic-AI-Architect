"""
Tests for cross-encoder reranking (src/pipeline/cross_encoder_rerank.py).

No model is loaded: the pure reorder logic is tested directly, and the reranker's graceful
no-op path is exercised by forcing the model unavailable. No network, no heavy dependency.
"""

from src.pipeline.cross_encoder_rerank import (
    CrossEncoderReranker,
    enabled,
    reorder_by_scores,
)


class TestReorderByScores:
    def test_reorders_top_k_by_ce_score(self):
        hits = [
            {"post_id": "a", "score": 0.9},
            {"post_id": "b", "score": 0.8},
            {"post_id": "c", "score": 0.7},
        ]
        # CE prefers c, then a, then b.
        out = reorder_by_scores(hits, [0.1, 0.0, 0.9], top_k=3)
        assert [h["post_id"] for h in out] == ["c", "a", "b"]

    def test_preserves_reported_score(self):
        hits = [{"post_id": "a", "score": 0.9}, {"post_id": "b", "score": 0.4}]
        out = reorder_by_scores(hits, [0.0, 1.0], top_k=2)
        assert out[0]["post_id"] == "b"
        assert out[0]["score"] == 0.4  # vector score untouched
        assert "cross_encoder_score" in out[0]

    def test_tail_beyond_top_k_is_untouched(self):
        hits = [
            {"post_id": "a", "score": 0.9},
            {"post_id": "b", "score": 0.8},
            {"post_id": "c", "score": 0.7},
        ]
        # Only rerank top 2; 'c' stays last regardless of CE.
        out = reorder_by_scores(hits, [0.0, 1.0], top_k=2)
        assert out[-1]["post_id"] == "c"
        assert [h["post_id"] for h in out[:2]] == ["b", "a"]

    def test_single_hit_unchanged(self):
        hits = [{"post_id": "a", "score": 0.5}]
        assert reorder_by_scores(hits, [0.9], top_k=5) is hits

    def test_no_scores_unchanged(self):
        hits = [{"post_id": "a", "score": 0.5}, {"post_id": "b", "score": 0.4}]
        assert reorder_by_scores(hits, [], top_k=5) is hits


class TestGracefulFallback:
    def _unavailable(self) -> CrossEncoderReranker:
        r = CrossEncoderReranker(model_name="does-not-exist/none")
        # Force the load to have happened and failed, without touching the network.
        r._load_attempted = True
        r._available = False
        return r

    def test_rerank_is_noop_when_unavailable(self):
        r = self._unavailable()
        hits = [{"post_id": "a", "score": 0.9}, {"post_id": "b", "score": 0.4}]
        out = r.rerank_hits("query", hits)
        assert out is hits  # unchanged, no exception

    def test_score_empty_when_unavailable(self):
        r = self._unavailable()
        assert r.score("query", ["doc one", "doc two"]) == []

    def test_available_property(self):
        r = self._unavailable()
        assert r.available is False


class TestEnabledFlag:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("AAA_CROSS_ENCODER", raising=False)
        assert enabled() is False

    def test_on_when_set(self, monkeypatch):
        monkeypatch.setenv("AAA_CROSS_ENCODER", "1")
        assert enabled() is True
