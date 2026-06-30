"""
Tests for the pure aggregation helpers in scripts/benchmark_mcp.py.

Loaded by path (scripts isn't a package), mirroring tests/test_wiki_scripts.py. The latency
measurement itself needs the store/model and isn't unit-tested; the summary math is.
"""

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "benchmark_mcp.py"


def _load():
    spec = importlib.util.spec_from_file_location("benchmark_mcp_under_test", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPercentile:
    def test_median_of_known_set(self):
        mod = _load()
        assert mod.percentile([10, 20, 30, 40, 50], 50) == 30

    def test_p95_is_near_top(self):
        mod = _load()
        vals = list(range(1, 101))  # 1..100
        assert mod.percentile(vals, 95) >= 95

    def test_empty_is_zero(self):
        mod = _load()
        assert mod.percentile([], 50) == 0.0

    def test_clamps_to_range(self):
        mod = _load()
        assert mod.percentile([5], 99) == 5
        assert mod.percentile([5], 1) == 5


class TestSummarize:
    def test_basic_stats(self):
        mod = _load()
        s = mod.summarize([100.0, 200.0, 300.0])
        assert s["n"] == 3
        assert s["max"] == 300.0
        assert s["mean"] == 200.0
        assert s["median"] == 200.0

    def test_empty(self):
        mod = _load()
        s = mod.summarize([])
        assert s == {"n": 0, "median": 0.0, "p95": 0.0, "max": 0.0, "mean": 0.0}
