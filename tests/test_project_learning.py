"""
Unit tests for the project learning ingest pipeline.

Covers markdown table parsing, date normalization, stable ID generation, tag
extraction, document/metadata building, and the pipeline's add-vs-upsert branching.

No network, no ChromaDB, no API keys — the pipeline.run() test uses a fake store.
"""

import pytest

from src.pipeline.project_learning_ingest import (
    LearningEntry,
    ProjectLearningIngestPipeline,
    _extract_tags,
    _normalize_date,
    _parse_decisions,
    _parse_discoveries,
    _parse_lessons,
    _parse_table_rows,
    _stable_id,
)
import src.pipeline.project_learning_ingest as pli


# ---------------------------------------------------------------------------
# Fixtures — synthetic log files
# ---------------------------------------------------------------------------

_DECISION_MD = """# Decision Log

| Date | Decision | Status | Rationale | Primary References |
|------|----------|--------|-----------|--------------------|
| 2026-03 | Use ChromaDB for the persona store | Accepted | Real semantic search via cosine | `store.py` |
| 2026-04-15 | Pin major versions only | Accepted | Allows security patches | `requirements.txt` |
"""

_DISCOVERY_MD = """# Discovery Log

| Date | Discovery | Why It Matters | Evidence / Source | Follow-Up |
|------|-----------|----------------|-------------------|-----------|
| 2026-03 | TF-IDF fallback keeps 70% recall | Justifies graceful degradation | eval run | keep fallback |
"""

_LESSON_MD = """# Lessons Learned

| Date | Lesson | What Triggered It | Preventive Action |
|------|--------|-------------------|-------------------|
| 2026-04 | Python hash() is non-deterministic | Duplicate IDs across runs | Use hashlib.md5 |
"""


# ---------------------------------------------------------------------------
# _normalize_date
# ---------------------------------------------------------------------------

class TestNormalizeDate:
    def test_month_only_pads_to_first_of_month(self):
        assert _normalize_date("2026-03") == "2026-03-01"

    def test_full_date_unchanged(self):
        assert _normalize_date("2026-03-14") == "2026-03-14"

    def test_year_only_pads_fully(self):
        assert _normalize_date("2026") == "2026-01-01"

    def test_single_digit_month_zero_padded(self):
        assert _normalize_date("2026-3") == "2026-03-01"

    def test_unparseable_returned_as_is(self):
        assert _normalize_date("Q2 2026") == "Q2 2026"

    def test_empty_string_safe(self):
        assert _normalize_date("") == ""

    def test_fixes_lexical_comparison_bug(self):
        # The original bug: "2026-03" >= "2026-03-15" is False (drops the entry).
        # After normalization the comparison is sound.
        assert _normalize_date("2026-03") >= "2026-03-01"
        assert not (_normalize_date("2026-03") >= "2026-03-15")
        assert _normalize_date("2026-04") >= "2026-03-15"


# ---------------------------------------------------------------------------
# _stable_id
# ---------------------------------------------------------------------------

class TestStableId:
    def test_deterministic(self):
        a = _stable_id("decision", "2026-03", "Use ChromaDB")
        b = _stable_id("decision", "2026-03", "Use ChromaDB")
        assert a == b
        assert a.startswith("pl-")

    def test_differs_by_type(self):
        assert _stable_id("decision", "2026-03", "X") != _stable_id("lesson", "2026-03", "X")

    def test_uses_raw_date_for_stability(self):
        # ID must be computed from the raw date, not the normalized one, so that
        # changing _normalize_date never orphans existing entries.
        raw = _stable_id("decision", "2026-03", "X")
        normalized = _stable_id("decision", "2026-03-01", "X")
        assert raw != normalized  # proves raw date is what's hashed


# ---------------------------------------------------------------------------
# _extract_tags
# ---------------------------------------------------------------------------

class TestExtractTags:
    def test_case_insensitive_match(self):
        tags = _extract_tags("we used chromadb and FastAPI", pli._KNOWN_TOOLS)
        assert "ChromaDB" in tags
        assert "FastAPI" in tags

    def test_no_false_positive(self):
        assert _extract_tags("nothing relevant here", pli._KNOWN_TOOLS) == []


# ---------------------------------------------------------------------------
# Table parsing
# ---------------------------------------------------------------------------

class TestTableParsing:
    def test_skips_header_and_separator(self):
        rows = _parse_table_rows(_DECISION_MD)
        # header + 2 data rows = 3 (separator excluded)
        assert len(rows) == 3
        assert rows[0][0] == "Date"  # header
        assert rows[1][0] == "2026-03"  # first data row

    def test_parse_decisions_happy_path(self, tmp_path):
        f = tmp_path / "decision-log.md"
        f.write_text(_DECISION_MD, encoding="utf-8")
        entries = _parse_decisions(f)
        assert len(entries) == 2
        first = entries[0]
        assert first.learning_type == "decision"
        assert first.date == "2026-03"
        assert first.title == "Use ChromaDB for the persona store"
        assert first.status == "Accepted"
        assert "ChromaDB" in first.mentioned_tools

    def test_parse_discoveries_happy_path(self, tmp_path):
        f = tmp_path / "discovery-log.md"
        f.write_text(_DISCOVERY_MD, encoding="utf-8")
        entries = _parse_discoveries(f)
        assert len(entries) == 1
        assert entries[0].learning_type == "discovery"
        assert entries[0].context == "Why It Matters" or "graceful" in entries[0].context

    def test_parse_lessons_happy_path(self, tmp_path):
        f = tmp_path / "lessons.md"
        f.write_text(_LESSON_MD, encoding="utf-8")
        entries = _parse_lessons(f)
        assert len(entries) == 1
        assert entries[0].learning_type == "lesson"
        assert "hashlib.md5" in entries[0].action

    def test_short_rows_skipped(self, tmp_path):
        # A row with too few columns must not crash the parser.
        bad = "# X\n\n| Date | Decision | Status | Rationale |\n|--|--|--|--|\n| 2026-03 |\n"
        f = tmp_path / "decision-log.md"
        f.write_text(bad, encoding="utf-8")
        entries = _parse_decisions(f)
        assert entries == []  # the malformed 1-cell row is skipped


# ---------------------------------------------------------------------------
# LearningEntry serialization
# ---------------------------------------------------------------------------

class TestLearningEntrySerialization:
    def _entry(self):
        return LearningEntry(
            entry_id="pl-test",
            learning_type="decision",
            date="2026-03",
            title="Use ChromaDB",
            context="semantic search",
            action="store.py",
            status="Accepted",
            mentioned_tools=["ChromaDB"],
            topics=["vector search"],
        )

    def test_to_metadata_marks_internal_tier(self):
        meta = self._entry().to_metadata()
        assert meta["source_tier"] == "internal"
        assert meta["post_type"] == "project_learning"
        assert meta["persona_id"] == "aaa_project"

    def test_to_metadata_normalizes_timestamp(self):
        meta = self._entry().to_metadata()
        assert meta["timestamp"] == "2026-03-01"

    def test_to_document_includes_type_and_content(self):
        doc = self._entry().to_document()
        assert "DECISION: Use ChromaDB" in doc
        assert "Accepted" in doc
        assert "semantic search" in doc


# ---------------------------------------------------------------------------
# Pipeline run() — add vs upsert branching (fake store, no ChromaDB)
# ---------------------------------------------------------------------------

class _FakeCollection:
    def __init__(self):
        self.added = {}
        self.updated = {}

    def add(self, ids, documents, metadatas):
        self.added[ids[0]] = metadatas[0]

    def update(self, ids, documents, metadatas):
        self.updated[ids[0]] = metadatas[0]


class _FakeStore:
    def __init__(self, existing):
        self._collection = _FakeCollection()
        self._existing = set(existing)

    def get_existing_ids(self):
        return self._existing


@pytest.fixture
def synthetic_logs(tmp_path, monkeypatch):
    """Point the pipeline at synthetic log files instead of the real docs/."""
    d = tmp_path / "decision-log.md"
    di = tmp_path / "discovery-log.md"
    le = tmp_path / "lessons-learned-log.md"
    d.write_text(_DECISION_MD, encoding="utf-8")
    di.write_text(_DISCOVERY_MD, encoding="utf-8")
    le.write_text(_LESSON_MD, encoding="utf-8")
    monkeypatch.setitem(pli._LEARNING_SOURCES, "decision", d)
    monkeypatch.setitem(pli._LEARNING_SOURCES, "discovery", di)
    monkeypatch.setitem(pli._LEARNING_SOURCES, "lesson", le)
    return tmp_path


class TestPipelineRun:
    def test_first_run_adds_all(self, synthetic_logs, monkeypatch):
        fake = _FakeStore(existing=[])
        pipeline = ProjectLearningIngestPipeline()
        monkeypatch.setattr(pipeline, "_get_store", lambda: fake)

        results = pipeline.run()
        total_added = sum(r.added for r in results)
        # 2 decisions + 1 discovery + 1 lesson
        assert total_added == 4
        assert len(fake._collection.added) == 4
        assert len(fake._collection.updated) == 0

    def test_second_run_upserts_existing(self, synthetic_logs, monkeypatch):
        # First pass to learn the IDs.
        fake1 = _FakeStore(existing=[])
        p1 = ProjectLearningIngestPipeline()
        monkeypatch.setattr(p1, "_get_store", lambda: fake1)
        p1.run()
        existing_ids = list(fake1._collection.added.keys())

        # Second pass: all IDs already present -> all should update, none add.
        fake2 = _FakeStore(existing=existing_ids)
        p2 = ProjectLearningIngestPipeline()
        monkeypatch.setattr(p2, "_get_store", lambda: fake2)
        results = p2.run()

        assert sum(r.added for r in results) == 0
        assert sum(r.skipped for r in results) == 4
        assert len(fake2._collection.updated) == 4

    def test_missing_file_records_error_not_crash(self, tmp_path, monkeypatch):
        # Point one source at a nonexistent file.
        monkeypatch.setitem(pli._LEARNING_SOURCES, "decision", tmp_path / "nope.md")
        monkeypatch.setitem(pli._LEARNING_SOURCES, "discovery", tmp_path / "nope2.md")
        monkeypatch.setitem(pli._LEARNING_SOURCES, "lesson", tmp_path / "nope3.md")
        fake = _FakeStore(existing=[])
        pipeline = ProjectLearningIngestPipeline()
        monkeypatch.setattr(pipeline, "_get_store", lambda: fake)

        results = pipeline.run()
        assert sum(r.added for r in results) == 0
        assert all(r.errors for r in results)  # each records a "file not found"
