"""Tests for the corpus refresh cycle, focused on the pre-ingest snapshot restore.

The restore-before-ingest step guards against the CI corpus-regression bug:
a fresh checkout with a stale/inconsistent live store must be reconciled to the
committed snapshot BEFORE any ingest runs, or the persona corpus and promoted
learning artifacts can be silently dropped.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_MODULE_PATH = _REPO_ROOT / "scripts" / "refresh_corpus.py"


@pytest.fixture(scope="module")
def refresh_corpus():
    """Load scripts/refresh_corpus.py as a module (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location("refresh_corpus", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_restore_dry_run_is_noop(refresh_corpus):
    """In dry-run, restore must not shell out and must report success."""
    with patch.object(refresh_corpus.subprocess, "run") as mock_run:
        assert refresh_corpus.run_snapshot_restore(dry_run=True) is True
        mock_run.assert_not_called()


def test_restore_invokes_restore_script(refresh_corpus):
    """A real restore calls the restore_chromadb_snapshot.py script."""
    completed = MagicMock(returncode=0, stderr="")
    with patch.object(refresh_corpus.subprocess, "run", return_value=completed) as mock_run:
        assert refresh_corpus.run_snapshot_restore(dry_run=False) is True
        mock_run.assert_called_once()
        argv = mock_run.call_args.args[0]
        assert any("restore_chromadb_snapshot.py" in str(a) for a in argv)


def test_restore_reports_failure_on_nonzero(refresh_corpus):
    """A non-zero return from the restore script surfaces as False, not a crash."""
    completed = MagicMock(returncode=1, stderr="boom")
    with patch.object(refresh_corpus.subprocess, "run", return_value=completed):
        assert refresh_corpus.run_snapshot_restore(dry_run=False) is False


def test_cycle_restores_before_ingest(refresh_corpus):
    """The refresh cycle must restore the snapshot BEFORE any ingest step."""
    calls: list[str] = []

    def record(name, ret):
        def _fn(*_args, **_kwargs):
            calls.append(name)
            return ret
        return _fn

    with patch.object(refresh_corpus, "run_snapshot_restore", side_effect=record("restore", True)), \
         patch.object(refresh_corpus, "run_project_learning_ingest",
                      side_effect=record("learning", {"added": 0})), \
         patch.object(refresh_corpus, "run_blog_ingest", side_effect=record("blog", {"added": 0})), \
         patch.object(refresh_corpus, "run_arxiv_ingest", side_effect=record("arxiv", {"added": 0})), \
         patch.object(refresh_corpus, "run_snapshot_export", side_effect=record("export", True)):
        result = refresh_corpus.run_refresh_cycle(api_key=None, dry_run=True)

    assert calls[0] == "restore", f"restore must run first, got order: {calls}"
    assert calls.index("restore") < calls.index("learning")
    assert calls.index("restore") < calls.index("blog")
    assert calls.index("restore") < calls.index("arxiv")
    assert result["snapshot_restored"] is True
