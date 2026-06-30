"""
Tests for hybrid retrieval ranking (src/pipeline/hybrid_ranking.py).

Pure-function tests — no store, no network, no model. The headline test proves the lever
deterministically: a lexically exact match that the embedding under-ranked is promoted.
"""

from src.pipeline.hybrid_ranking import (
    DEFAULT_ALPHA,
    bm25_scores,
    hybrid_scores,
    rerank_hits,
    selective_terms,
    tokenize,
)


class TestTokenize:
    def test_lowercases_and_splits(self):
        assert tokenize("MCP Tool-Use, RAG!") == ["mcp", "tool", "use", "rag"]

    def test_drops_stopwords_and_single_chars(self):
        assert tokenize("how do I build a RAG system") == ["build", "rag", "system"]

    def test_empty(self):
        assert tokenize("") == []
        assert tokenize(None) == []


class TestBM25:
    def test_doc_with_query_terms_scores_higher(self):
        docs = [
            "an essay about cooking pasta and italian food",
            "the model context protocol MCP standardizes tool use for agents",
        ]
        scores = bm25_scores("MCP tool use", docs)
        assert scores[1] > scores[0]

    def test_no_query_terms_all_zero(self):
        scores = bm25_scores("", ["some document text", "another"])
        assert scores == [0.0, 0.0]

    def test_rare_term_outweighs_common_term(self):
        # "agents" appears in every doc (low IDF); "rrf" appears in one (high IDF).
        docs = [
            "agents agents agents orchestration",
            "agents reciprocal rank fusion rrf for agents",
            "agents memory agents planning",
        ]
        scores = bm25_scores("rrf agents", docs)
        assert scores[1] == max(scores)


class TestHybridScores:
    def test_blend_promotes_lexical_match(self):
        # Doc A: higher vector but no lexical hit. Doc B: lower vector, exact lexical hit.
        documents = [
            "a general discussion of machine learning systems",
            "reciprocal rank fusion rrf combines rankings",
        ]
        vector = [0.60, 0.45]
        blended = hybrid_scores("rrf reciprocal rank fusion", documents, vector, alpha=0.5)
        assert blended[1] > blended[0]

    def test_no_lexical_signal_preserves_vector_order(self):
        documents = ["totally unrelated text one", "totally unrelated text two"]
        vector = [0.5, 0.3]
        blended = hybrid_scores("xyzzy nonexistent term", documents, vector)
        # lexical all-zero → blend is a scaled vector ranking, order preserved
        assert blended[0] > blended[1]

    def test_alpha_zero_is_pure_vector(self):
        documents = ["has the term rrf", "no match here"]
        vector = [0.2, 0.9]
        blended = hybrid_scores("rrf", documents, vector, alpha=0.0)
        assert blended == [0.2 * 1.0, 0.9 * 1.0] or blended[1] > blended[0]

    def test_empty(self):
        assert hybrid_scores("q", [], []) == []


class TestSelectiveTerms:
    def test_rare_term_is_selective(self):
        docs = [
            "general text about agents and orchestration",
            "general text about agents and memory",
            "vllm turboquant quantization kernel",  # 'turboquant' in 1/3 docs
        ]
        terms = selective_terms("vllm turboquant", docs)
        assert "turboquant" in terms

    def test_common_in_pool_term_is_not_selective(self):
        # 'agents' appears in every doc → carries no discriminating signal.
        docs = ["agents one", "agents two", "agents three", "agents four"]
        assert selective_terms("agents", docs) == []

    def test_absent_term_is_not_selective(self):
        docs = ["alpha", "beta", "gamma"]
        assert selective_terms("zzz", docs) == []


class TestRerankHits:
    def _hits(self):
        return [
            {"post_id": "a", "document": "broad overview of agent memory design", "score": 0.60},
            {"post_id": "b", "document": "the MCP model context protocol tool spec", "score": 0.42},
        ]

    def test_lexical_match_promoted_to_rank_1(self):
        """The headline lever: B (lower vector, exact 'MCP' match) leads after rerank."""
        ranked = rerank_hits("MCP model context protocol", self._hits(), alpha=0.5)
        assert ranked[0]["post_id"] == "b"
        # Reported relevance is still the vector score (unchanged semantics).
        assert ranked[0]["score"] == 0.42
        assert "hybrid_score" in ranked[0] and "lexical_score" in ranked[0]

    def test_single_hit_unchanged(self):
        one = [{"post_id": "a", "document": "x", "score": 0.5}]
        assert rerank_hits("q", one) is one

    def test_no_lexical_signal_keeps_vector_order(self):
        ranked = rerank_hits("zzz nonexistent", self._hits())
        assert [h["post_id"] for h in ranked] == ["a", "b"]

    def test_default_alpha_keeps_vector_primary(self):
        # With the production default alpha, a strong vector lead is NOT overturned by a
        # weak lexical signal.
        hits = [
            {"post_id": "strong", "document": "agent orchestration patterns", "score": 0.80},
            {"post_id": "weak", "document": "mentions rag once", "score": 0.40},
        ]
        ranked = rerank_hits("rag", hits, alpha=DEFAULT_ALPHA)
        assert ranked[0]["post_id"] == "strong"
