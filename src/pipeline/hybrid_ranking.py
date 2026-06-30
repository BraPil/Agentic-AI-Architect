"""
Hybrid retrieval ranking — fuse dense (vector) similarity with sparse (lexical) signal.

The persona store ranks purely by cosine similarity on `all-MiniLM-L6-v2` embeddings. Dense
retrieval is strong on paraphrase and concept overlap but weak on *exact* terms an embedding
smooths away — tool names, acronyms (MCP, RAG, RRF), API symbols, rare proper nouns. The
discovery log named retrieval ranking as the next lever: "surface the most on-point evidence
densely — not just more content."

This module adds a lexical signal (BM25 over the candidate pool) and fuses it with the vector
score as a convex blend:

    hybrid = (1 - alpha) * vector_sim + alpha * lexical_norm

The blend is used **only to re-order** the candidate pool. The reported relevance `score`
stays the raw vector similarity, so the [0,1] relevance scale (and every threshold / outcome
multiplier built on it) is unchanged — hybrid changes *which* docs lead and which land in the
returned top-N, not what "relevance" means.

**Selectivity gating (critical).** Uniform blending hurt: on a conceptual-query eval it
demoted the best dense match on 11/15 questions, because keyword overlap is noise when the
query is conceptual ("best practices for RAG architecture"). So the lexical signal only fires
on *discriminating* query terms — tokens that are rare in the candidate pool (document
frequency ≤ `selectivity_frac` of the pool). A query whose terms are all common-in-pool (or
absent) gets pure vector order, an exact no-op. This restricts lexical to the cases it helps
(exact tool names, acronyms, rare proper nouns) and leaves dense retrieval untouched elsewhere.

Pure stdlib (no new dependency), and fast: BM25 over a few dozen candidates is microseconds,
well inside the < 200ms cached-query budget.

Status: built, tested, and measured — but **OFF by default** (opt-in via AAA_HYBRID_RANKING=1).
On the current evaluation it shows no quality regression (every judgment check unchanged at
15/15) yet no demonstrable gain, because that eval cannot measure ranking quality: its pass
rate is saturated and its "avg relevance" metric is the mean top-1 *vector* similarity, which
mathematically can only fall under any reorder (a promoted doc has lower vector sim than the
max-vector doc it displaces). The mechanism is ready to enable the moment a ranking-aware eval
(graded relevance / MRR / nDCG, with exact-term questions) demonstrates benefit. See
docs/hybrid-ranking-v0.md.

Configuration:
    AAA_HYBRID_RANKING (env): set to "1" to enable fusion (default OFF → pure vector order).
    alpha: lexical weight in [0, 1]. Default 0.25 — vector stays primary, lexical breaks ties
        and rescues exact-term matches the embedding missed. The lexical signal can only
        overturn a vector lead smaller than alpha/(1-alpha) ≈ 0.33 cosine, so a clear vector
        winner is never displaced by a single keyword hit.
"""

import math
import re

# Lexical weight: how much the sparse signal moves the dense ranking. Vector-primary.
# At 0.25 a top-of-pool lexical match (normalized to 1.0) only overtakes a vector lead
# below alpha/(1-alpha) ≈ 0.33 cosine — lexical rescues near-ties, never clear winners.
DEFAULT_ALPHA = 0.25

# BM25 hyperparameters (standard defaults).
_BM25_K1 = 1.5
_BM25_B = 0.75

# Selectivity gate: a query term contributes to the lexical signal only if it appears in at
# most this fraction of the candidate pool. Common-in-pool terms (≈ the topic everyone's
# talking about) carry no discriminating signal and are ignored, so conceptual queries stay
# pure-vector. 0.5 = a term in ≤ half the pool is "selective".
DEFAULT_SELECTIVITY_FRAC = 0.5

# A short, high-frequency stopword set. Deliberately small — domain terms must survive.
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "is", "are",
    "be", "was", "were", "it", "this", "that", "these", "those", "as", "at", "by", "from",
    "how", "what", "why", "when", "do", "does", "you", "your", "i", "we", "they", "about",
    "should", "would", "can", "could", "will", "if", "so", "than", "then", "into", "out",
})

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords and single chars."""
    return [
        tok for tok in _TOKEN_RE.findall((text or "").lower())
        if len(tok) > 1 and tok not in _STOPWORDS
    ]


def selective_terms(query: str, documents: list[str],
                    selectivity_frac: float = DEFAULT_SELECTIVITY_FRAC) -> list[str]:
    """
    Query terms that are *discriminating* in this candidate pool: present in at least one
    document but in no more than `selectivity_frac` of the pool. These are the terms whose
    lexical match carries signal (rare tool names, acronyms); common-in-pool terms are dropped.
    """
    q_terms = tokenize(query)
    if not q_terms or not documents:
        return []
    n = len(documents)
    max_df = max(1, int(selectivity_frac * n))
    doc_sets = [set(tokenize(d)) for d in documents]
    selective = []
    for term in dict.fromkeys(q_terms):  # preserve order, dedupe
        df = sum(1 for s in doc_sets if term in s)
        if 1 <= df <= max_df:
            selective.append(term)
    return selective


def bm25_scores(query: str, documents: list[str],
                term_filter: set[str] | None = None) -> list[float]:
    """
    BM25 relevance of `query` against each document, with IDF computed over the candidate
    pool itself (a standard "rerank the top-k" approximation — fast and dependency-free).

    If `term_filter` is given, only those query terms contribute (used to restrict scoring to
    selective terms). Returns one raw BM25 score per document (>= 0; higher is more relevant).
    """
    q_terms = tokenize(query)
    if term_filter is not None:
        q_terms = [t for t in q_terms if t in term_filter]
    if not q_terms or not documents:
        return [0.0] * len(documents)

    doc_tokens = [tokenize(d) for d in documents]
    doc_len = [len(toks) for toks in doc_tokens]
    n = len(documents)
    avgdl = (sum(doc_len) / n) if n else 0.0
    if avgdl == 0.0:
        return [0.0] * n

    # Document frequency per query term across the pool.
    df: dict[str, int] = {}
    doc_sets = [set(toks) for toks in doc_tokens]
    for term in set(q_terms):
        df[term] = sum(1 for s in doc_sets if term in s)

    # BM25+ style IDF — always positive, so a term present everywhere still contributes a little.
    idf = {
        term: math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
        for term in df
    }

    scores: list[float] = []
    for toks, dl in zip(doc_tokens, doc_len):
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for term in q_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            denom = f + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl)
            s += idf[term] * (f * (_BM25_K1 + 1)) / denom
        scores.append(s)
    return scores


def _minmax_norm(values: list[float]) -> list[float]:
    """Min-max normalize to [0, 1]. All-equal (incl. all-zero) → all zeros (no signal)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi <= lo:
        return [0.0] * len(values)
    span = hi - lo
    return [(v - lo) / span for v in values]


def hybrid_scores(
    query: str,
    documents: list[str],
    vector_scores: list[float],
    alpha: float = DEFAULT_ALPHA,
) -> list[float]:
    """
    Convex blend of vector similarity and normalized lexical (BM25) score.

    Args:
        query: the search query.
        documents: candidate document texts, aligned with `vector_scores`.
        vector_scores: cosine similarities in [0, 1], aligned with `documents`.
        alpha: lexical weight in [0, 1].

    Returns:
        One blended score per candidate (used only for ordering). When the query has no
        lexical signal in the pool, lexical_norm is all zeros and the blend reduces to a
        scaled vector ranking (order preserved).
    """
    if not documents:
        return []
    lexical = _minmax_norm(bm25_scores(query, documents))
    return [
        (1.0 - alpha) * vec + alpha * lex
        for vec, lex in zip(vector_scores, lexical)
    ]


def rerank_hits(
    query: str,
    hits: list[dict],
    *,
    alpha: float = DEFAULT_ALPHA,
    doc_key: str = "document",
    vector_key: str = "score",
) -> list[dict]:
    """
    Re-order `hits` by the hybrid blend, non-destructively.

    Each hit keeps its original `score` (vector relevance) and gains a `hybrid_score`
    (and `lexical_score`) for audit. The returned list is sorted by `hybrid_score`
    descending; the sort is stable, so a zero-lexical pool preserves the incoming
    (vector) order. Fewer than two hits are returned unchanged.

    Selectivity-gated: if the query has no discriminating term in the pool (the conceptual
    case), the hits are returned unchanged in pure-vector order — an exact no-op.
    """
    if len(hits) < 2:
        return hits
    documents = [h.get(doc_key, "") for h in hits]
    terms = selective_terms(query, documents)
    if not terms:
        return hits  # no discriminating lexical signal → pure vector order
    vectors = [float(h.get(vector_key, 0.0)) for h in hits]
    lexical = _minmax_norm(bm25_scores(query, documents, term_filter=set(terms)))
    blended = [(1.0 - alpha) * v + alpha * lx for v, lx in zip(vectors, lexical)]
    for h, hs, lx in zip(hits, blended, lexical):
        h["hybrid_score"] = round(hs, 6)
        h["lexical_score"] = round(lx, 6)
    # Stable sort: ties (e.g. equal hybrid scores) keep the original vector order.
    return sorted(hits, key=lambda h: h["hybrid_score"], reverse=True)
