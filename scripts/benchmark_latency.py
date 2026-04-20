#!/usr/bin/env python3
"""
Latency benchmark for MCP tool calls.

Measures warm-query latency (after first-call cold-start) for all three tools.
Target: < 200ms per call for cached queries.

Usage:
  python3 scripts/benchmark_latency.py
"""

import sys
import time
from pathlib import Path
from statistics import mean, median, stdev

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

QUERIES = [
    "multi-agent orchestration patterns",
    "RAG retrieval augmented generation",
    "LLM evaluation and testing",
    "agentic coding workflows",
    "vector database embeddings",
]

N_WARMUP = 1
N_BENCH  = 5


def bench(label: str, fn, *args, **kwargs) -> list[float]:
    # Warm-up
    for _ in range(N_WARMUP):
        fn(*args, **kwargs)

    times = []
    for _ in range(N_BENCH):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        times.append((time.perf_counter() - t0) * 1000)
    return times


def report(label: str, times: list[float]) -> None:
    ok = "✅" if max(times) < 200 else "⚠️ "
    print(
        f"{ok}  {label:<40}  "
        f"mean={mean(times):6.1f}ms  "
        f"median={median(times):6.1f}ms  "
        f"max={max(times):6.1f}ms  "
        f"stddev={stdev(times) if len(times) > 1 else 0:5.1f}ms"
    )


def main() -> None:
    print("Loading store (cold start)…")
    t0 = time.perf_counter()
    from src.api.mcp_server import search_knowledge, get_trending_tools, get_architecture_recommendation, _get_store
    _get_store()  # force init
    cold_ms = (time.perf_counter() - t0) * 1000
    print(f"  Cold start: {cold_ms:.0f}ms\n")

    print("─" * 80)
    print("Warm-query benchmarks (each tool, 5 runs after 1 warm-up call)")
    print("─" * 80)

    # search_knowledge — one query repeated
    for q in QUERIES[:2]:
        times = bench(f"search_knowledge({q[:30]})", search_knowledge, query=q)
        report(f"search_knowledge: {q[:30]}", times)

    # get_trending_tools
    times = bench("get_trending_tools()", get_trending_tools)
    report("get_trending_tools (all)", times)

    times = bench("get_trending_tools(persona=andrej)", get_trending_tools, persona="andrej-karpathy")
    report("get_trending_tools (persona filter)", times)

    print("─" * 80)
    target = 200
    print(f"Target: < {target}ms for all warm calls (synthesis excluded — involves LLM API)")


if __name__ == "__main__":
    main()
