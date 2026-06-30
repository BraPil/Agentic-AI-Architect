#!/usr/bin/env python3
"""
Benchmark MCP query latency against the < 200ms cached-query budget (the ExMorbus SLA).

Measures `search_knowledge` wall-clock latency across reranking configurations so the latency
cost of each stage is reproducible — this is the tool behind the 2026-06-30 finding that the
cross-encoder (~6s/query on CPU) is far over budget while hybrid (~60ms) is not.

Reports median / p95 / max over a fixed query set, warm (models loaded) by default. The first,
cold call (model + index load) is reported separately when --cold is passed.

Usage:
  python3 scripts/benchmark_mcp.py                  # hybrid-off, hybrid-on, hybrid+CE
  python3 scripts/benchmark_mcp.py --runs 10        # more queries per config
  python3 scripts/benchmark_mcp.py --no-cross-encoder
  python3 scripts/benchmark_mcp.py --json out.json

Tip: export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 to skip HF Hub HTTP checks.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BUDGET_MS = 200  # ExMorbus cached-query SLA

# Representative queries spanning conceptual + exact-term retrieval.
QUERIES = [
    "How should I design memory for a multi-agent system?",
    "What are the best practices for RAG architecture?",
    "prompt injection defense for LLM agents",
    "Which quantization methods does vLLM support?",
    "How should I evaluate agentic systems?",
    "What does Lilian Weng say about reward hacking?",
    "multi-agent orchestration patterns",
    "fine-tuning versus RAG tradeoffs",
]


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (pct in [0, 100]). Empty → 0.0."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * len(ordered) + 0.5)) - 1))
    return ordered[k]


def summarize(times_ms: list[float]) -> dict:
    """Aggregate a list of latencies (ms) into median / p95 / max / mean / n."""
    if not times_ms:
        return {"n": 0, "median": 0.0, "p95": 0.0, "max": 0.0, "mean": 0.0}
    return {
        "n": len(times_ms),
        "median": round(percentile(times_ms, 50), 1),
        "p95": round(percentile(times_ms, 95), 1),
        "max": round(max(times_ms), 1),
        "mean": round(sum(times_ms) / len(times_ms), 1),
    }


def _bench_config(search_knowledge, runs: int) -> dict:
    times = []
    for i in range(runs):
        q = QUERIES[i % len(QUERIES)]
        t = time.perf_counter()
        search_knowledge(q, n_results=8)
        times.append((time.perf_counter() - t) * 1000.0)
    return summarize(times)


def run(runs: int, with_cross_encoder: bool, cold: bool) -> dict:
    from src.api.mcp_server import search_knowledge  # noqa: PLC0415

    configs = [
        ("hybrid-off (pure vector)", {"AAA_HYBRID_RANKING": "0", "AAA_CROSS_ENCODER": "0"}),
        ("hybrid-on (default)", {"AAA_HYBRID_RANKING": "1", "AAA_CROSS_ENCODER": "0"}),
    ]
    if with_cross_encoder:
        configs.append(("hybrid + cross-encoder",
                        {"AAA_HYBRID_RANKING": "1", "AAA_CROSS_ENCODER": "1"}))

    results: dict[str, dict] = {}
    cold_ms = None

    # Cold call (model + index load) before any warmup.
    if cold:
        os.environ["AAA_HYBRID_RANKING"] = "1"
        os.environ["AAA_CROSS_ENCODER"] = "0"
        t = time.perf_counter()
        search_knowledge(QUERIES[0], n_results=8)
        cold_ms = round((time.perf_counter() - t) * 1000.0, 1)

    for label, env in configs:
        os.environ.update(env)
        search_knowledge(QUERIES[0], n_results=8)  # warm this config
        results[label] = _bench_config(search_knowledge, runs)

    return {"budget_ms": BUDGET_MS, "runs": runs, "cold_first_call_ms": cold_ms,
            "configs": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark MCP search_knowledge latency")
    parser.add_argument("--runs", type=int, default=8, help="Queries per config")
    parser.add_argument("--no-cross-encoder", action="store_true",
                        help="Skip the cross-encoder config (avoids its model load)")
    parser.add_argument("--cold", action="store_true", help="Also report the cold first-call time")
    parser.add_argument("--json", dest="json_out", help="Write full results JSON to this path")
    args = parser.parse_args()

    report = run(args.runs, with_cross_encoder=not args.no_cross_encoder, cold=args.cold)

    print(f"\nMCP query latency — budget < {report['budget_ms']}ms, {report['runs']} runs/config")
    if report["cold_first_call_ms"] is not None:
        print(f"  cold first call: {report['cold_first_call_ms']}ms (model + index load)\n")
    print(f"  {'config':<28}{'median':>9}{'p95':>9}{'max':>9}   budget")
    for label, s in report["configs"].items():
        ok = "OK" if s["median"] < report["budget_ms"] else f"OVER {s['median']/report['budget_ms']:.0f}x"
        print(f"  {label:<28}{s['median']:>8.0f}ms{s['p95']:>8.0f}ms{s['max']:>8.0f}ms   {ok}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2))
        print(f"\nWritten → {args.json_out}")


if __name__ == "__main__":
    main()
