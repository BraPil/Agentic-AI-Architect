"""
Tests for the wiki maintenance scripts (scripts/lint_wiki.py).

Loads the script by path (it isn't a package) and points its path constants at a tmp wiki,
mirroring tests/test_refresh_corpus.py. Covers the error-raising checks: broken links and
index/catalog count drift.
"""

import importlib.util
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MODULE_PATH = _REPO_ROOT / "scripts" / "lint_wiki.py"


def _load_lint(tmp: Path):
    spec = importlib.util.spec_from_file_location("lint_wiki_under_test", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Redirect all paths into the tmp wiki.
    mod.WIKI_DIR = tmp
    mod.INDEX = tmp / "index.md"
    mod.PAGES_DIR = tmp / "pages"
    mod.CATALOG = tmp / "schema" / "persona_catalog.json"
    mod.PAGES_DIR.mkdir(parents=True, exist_ok=True)
    (tmp / "schema").mkdir(parents=True, exist_ok=True)
    return mod


def _write_catalog(mod, total_posts: int, total_personas: int) -> None:
    mod.CATALOG.write_text(json.dumps({
        "total_posts": total_posts, "total_personas": total_personas, "personas": [],
    }))


class TestCheckLinks:
    def test_broken_link_is_error(self, tmp_path):
        mod = _load_lint(tmp_path)
        mod.INDEX.write_text("See [Foo](pages/foo.md) and [[bar]]")
        errors: list[str] = []
        mod.check_links(errors)
        assert any("foo.md" in e for e in errors)
        assert any("bar" in e for e in errors)

    def test_existing_link_passes(self, tmp_path):
        mod = _load_lint(tmp_path)
        (mod.PAGES_DIR / "foo.md").write_text("# Foo")
        mod.INDEX.write_text("See [Foo](pages/foo.md)")
        errors: list[str] = []
        mod.check_links(errors)
        assert errors == []


class TestCheckOrphans:
    def test_unreferenced_page_warns(self, tmp_path):
        mod = _load_lint(tmp_path)
        (mod.PAGES_DIR / "lonely.md").write_text("# Lonely")
        mod.INDEX.write_text("nothing links here")
        warnings: list[str] = []
        mod.check_orphans(warnings)
        assert any("lonely.md" in w for w in warnings)


class TestCheckCounts:
    def test_count_drift_is_error(self, tmp_path):
        mod = _load_lint(tmp_path)
        _write_catalog(mod, total_posts=415, total_personas=105)
        mod.INDEX.write_text("> **Total items**: 999\n\n## Personas (42 Indexed)\n")
        errors: list[str] = []
        warnings: list[str] = []
        mod.check_counts(errors, warnings)
        assert any("Total items" in e for e in errors)
        assert any("Personas" in e for e in errors)

    def test_matching_counts_pass(self, tmp_path):
        mod = _load_lint(tmp_path)
        _write_catalog(mod, total_posts=415, total_personas=105)
        mod.INDEX.write_text("> **Total items**: 415\n\n## Personas (105 Indexed)\n")
        errors: list[str] = []
        warnings: list[str] = []
        mod.check_counts(errors, warnings)
        assert errors == []

    def test_missing_catalog_warns_not_errors(self, tmp_path):
        mod = _load_lint(tmp_path)
        mod.INDEX.write_text("> **Total items**: 415\n")
        errors: list[str] = []
        warnings: list[str] = []
        mod.check_counts(errors, warnings)
        assert errors == []
        assert any("persona_catalog" in w for w in warnings)
