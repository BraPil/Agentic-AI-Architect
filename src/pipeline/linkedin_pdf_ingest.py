"""LinkedIn PDF ingest pipeline for post text, OCR, and research triggering.

This module processes a readable PDF export of a LinkedIn reactions/activity
feed into one centralized bundle containing:

- extracted text for each detected post
- OCR snippets from larger embedded visuals
- diagram-intent summaries
- recurring architecture patterns
- curiosity hooks for deeper follow-up research
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import tempfile
import unicodedata
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.knowledge.knowledge_base import DEFAULT_DB_PATH, KnowledgeBase, KnowledgeEntry
from src.utils.helpers import sanitize_text

logger = logging.getLogger(__name__)

POST_MARKER = re.compile(r"Feed post number\s+(\d+)", re.IGNORECASE)
SHORT_TIMESTAMP = re.compile(r"^\d+\s*(?:s|m|h|d|w|mo|y)\b.*$", re.IGNORECASE)
LONG_TIMESTAMP = re.compile(
    r"^\d+\s+(?:second|minute|hour|day|week|month|year)s?\s+ago\b.*$",
    re.IGNORECASE,
)
MIN_IMAGE_WIDTH = 500
MIN_IMAGE_HEIGHT = 300
MAX_RESEARCH_HOOKS = 20
MIN_RELEVANCE_SCORE = 4.5
DEFAULT_KNOWLEDGE_SEED_SCORE = 7.0
DEFAULT_KNOWLEDGE_SEED_LIMIT = 25
PATTERN_RULES: tuple[tuple[str, str], ...] = (
    ("context engineering", "Context engineering as a first-class architecture layer"),
    ("ontology", "Ontology or semantic digital twin as a control plane"),
    ("observability", "End-to-end observability for agentic systems"),
    ("security", "Security and governance embedded into the runtime"),
    ("governance", "Security and governance embedded into the runtime"),
    ("evaluation", "Evaluation integrated into the agent lifecycle"),
    ("prompt", "Prompt and context assets as reusable operational artifacts"),
    ("claude", "Prompt and context assets as reusable operational artifacts"),
    ("mamba", "Hybrid model architectures driving inference efficiency"),
    ("mixture-of-experts", "Sparse expert routing for high-capacity reasoning"),
    ("reasoning", "Controllable reasoning modes and cost-aware inference"),
    ("tool call", "Tool-mediated execution with traceability"),
    ("agentic architecture", "End-to-end agentic architecture as the competitive layer"),
)
DOMAIN_SIGNAL_RULES: tuple[tuple[str, float], ...] = (
    ("agentic architecture", 2.5),
    ("context engineering", 2.2),
    ("ontology", 2.0),
    ("observability", 1.8),
    ("evaluation", 1.8),
    ("security", 1.6),
    ("governance", 1.6),
    ("prompt", 1.4),
    ("claude", 1.2),
    ("codex", 1.2),
    ("mcp", 1.2),
    ("playwright", 1.0),
    ("vercel", 0.8),
    ("postgres", 0.8),
    ("redis", 0.8),
    ("llm", 1.2),
    ("model", 1.0),
    ("reasoning", 1.5),
    ("agent", 1.3),
    ("tool", 0.9),
    ("workflow", 1.0),
    ("sdk", 1.0),
    ("api", 0.8),
    ("benchmark", 1.0),
    ("inference", 1.0),
    ("mixture-of-experts", 1.6),
    ("mamba", 1.4),
    ("rag", 1.4),
    ("vector", 0.9),
    ("open source", 0.6),
)
SOCIAL_NOISE_RULES: tuple[tuple[str, float], ...] = (
    ("promotion announcement", 3.5),
    ("promoted to", 3.5),
    ("promotion", 3.0),
    ("congratulations", 2.5),
    ("congrats", 2.5),
    ("thrilled to announce", 3.0),
    ("excited to announce", 2.5),
    ("new role", 2.5),
    ("joined ", 2.0),
    ("work anniversary", 3.0),
    ("birthday", 3.0),
    ("award", 2.0),
    ("achievement", 2.0),
    ("honored to share", 1.5),
    ("grateful to share", 1.5),
)
RESEARCH_HOOK_RULES: tuple[tuple[str, str], ...] = (
    (
        "ontology",
        "Compare ontology-centric control planes with knowledge graph, event log, and RAG-first architectures.",
    ),
    (
        "context engineering",
        "Study how team-level context vaults and repository structure change agent reliability over time.",
    ),
    (
        "observability",
        "Map the minimum viable observability stack for agent tool calls, data access, and decision traces.",
    ),
    (
        "security",
        "Investigate which governance controls are essential now versus which can remain future hooks.",
    ),
    (
        "mixture-of-experts",
        "Compare sparse reasoning-model economics against dense-model quality for production agent stacks.",
    ),
    (
        "prompt",
        "Codify reusable prompt, plan-mode, and context-document patterns as versioned architecture assets.",
    ),
    (
        "agentic architecture",
        "Extract a reference architecture that separates durable seams from fast-changing tool choices.",
    ),
)


@dataclass
class OcrArtifact:
    """OCR output for one extracted visual."""

    page_number: int
    file_name: str
    width: int
    height: int
    visual_type: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "file_name": self.file_name,
            "width": self.width,
            "height": self.height,
            "visual_type": self.visual_type,
            "text": self.text,
        }


@dataclass
class LinkedInPostRecord:
    """One post reconstructed from the PDF export."""

    post_number: int
    author: str
    page_numbers: list[int]
    body_text: str
    raw_text: str
    ocr_artifacts: list[OcrArtifact] = field(default_factory=list)
    summary: str = ""
    diagram_intent: str = ""
    architecture_patterns: list[str] = field(default_factory=list)
    research_hooks: list[str] = field(default_factory=list)
    namespace: str = "general"
    signal_score: float = 0.0
    is_relevant: bool = True
    exclusion_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "post_number": self.post_number,
            "author": self.author,
            "page_numbers": self.page_numbers,
            "body_text": self.body_text,
            "raw_text": self.raw_text,
            "ocr_artifacts": [artifact.to_dict() for artifact in self.ocr_artifacts],
            "summary": self.summary,
            "diagram_intent": self.diagram_intent,
            "architecture_patterns": self.architecture_patterns,
            "research_hooks": self.research_hooks,
            "namespace": self.namespace,
            "signal_score": self.signal_score,
            "is_relevant": self.is_relevant,
            "exclusion_reason": self.exclusion_reason,
        }


@dataclass
class LinkedInPdfIngestResult:
    """Final centralized ingest bundle for one LinkedIn PDF export."""

    pdf_path: str
    output_dir: str
    page_count: int
    post_count: int
    total_posts_detected: int
    filtered_out_count: int
    recurring_patterns: list[str]
    curiosity_queue: list[str]
    posts: list[LinkedInPostRecord]
    knowledge_entries_seeded: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdf_path": self.pdf_path,
            "output_dir": self.output_dir,
            "page_count": self.page_count,
            "post_count": self.post_count,
            "total_posts_detected": self.total_posts_detected,
            "filtered_out_count": self.filtered_out_count,
            "recurring_patterns": self.recurring_patterns,
            "curiosity_queue": self.curiosity_queue,
            "posts": [post.to_dict() for post in self.posts],
            "knowledge_entries_seeded": self.knowledge_entries_seeded,
            "generated_at": self.generated_at.isoformat(),
        }


class LinkedInPdfIngestPipeline:
    """Extract text, OCR visuals, and curiosity hooks from a LinkedIn PDF export."""

    def ingest_pdf(self, pdf_path: str | Path, output_dir: str | Path | None = None) -> LinkedInPdfIngestResult:
        pdf_file = Path(pdf_path)
        resolved_output_dir = Path(output_dir) if output_dir else Path("data/ingests") / pdf_file.stem
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        metadata = self._parse_pdfinfo(self._run_command(["pdfinfo", str(pdf_file)]))
        raw_text = self._sanitize_external_text(
            self._run_command(["pdftotext", "-layout", str(pdf_file), "-"]),
            context=str(pdf_file),
        )

        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            image_rows = self._extract_image_rows(pdf_file, temp_dir)
            ocr_artifacts = self._ocr_large_images(image_rows)
            detected_posts = self._build_posts(raw_text=raw_text, ocr_artifacts=ocr_artifacts)

        posts = self._filter_relevant_posts(detected_posts)
        recurring_patterns = self._recurring_patterns(posts)
        curiosity_queue = self._curiosity_queue(posts)
        result = LinkedInPdfIngestResult(
            pdf_path=str(pdf_file),
            output_dir=str(resolved_output_dir),
            page_count=int(metadata.get("Pages", 0)),
            post_count=len(posts),
            total_posts_detected=len(detected_posts),
            filtered_out_count=max(len(detected_posts) - len(posts), 0),
            recurring_patterns=recurring_patterns,
            curiosity_queue=curiosity_queue,
            posts=posts,
        )
        self._write_bundle(result=result, raw_text=raw_text)
        return result

    def seed_knowledge_base(
        self,
        result: LinkedInPdfIngestResult,
        db_path: str = DEFAULT_DB_PATH,
        min_signal_score: float = DEFAULT_KNOWLEDGE_SEED_SCORE,
        limit: int = DEFAULT_KNOWLEDGE_SEED_LIMIT,
    ) -> int:
        selected_posts = self.select_high_signal_posts(
            result.posts,
            min_signal_score=min_signal_score,
            limit=limit,
        )
        entries = [
            self._post_to_knowledge_entry(post=post, result=result)
            for post in selected_posts
        ]
        if not entries:
            result.knowledge_entries_seeded = 0
            self._write_bundle(result=result, raw_text=(Path(result.output_dir) / "raw_text.txt").read_text(encoding="utf-8"))
            return 0

        kb = KnowledgeBase(db_path=db_path)
        kb.initialize()
        try:
            stored = kb.store_many(entries)
        finally:
            kb.close()

        result.knowledge_entries_seeded = stored
        self._write_bundle(result=result, raw_text=(Path(result.output_dir) / "raw_text.txt").read_text(encoding="utf-8"))
        return stored

    def select_high_signal_posts(
        self,
        posts: list[LinkedInPostRecord],
        min_signal_score: float = DEFAULT_KNOWLEDGE_SEED_SCORE,
        limit: int = DEFAULT_KNOWLEDGE_SEED_LIMIT,
    ) -> list[LinkedInPostRecord]:
        selected = [
            post for post in posts
            if post.is_relevant and post.signal_score >= min_signal_score
        ]
        selected.sort(key=lambda post: post.signal_score, reverse=True)
        return selected[:limit]

    def _build_posts(self, raw_text: str, ocr_artifacts: list[OcrArtifact]) -> list[LinkedInPostRecord]:
        page_to_post, post_pages = self._split_posts(raw_text)
        ocr_by_post: dict[int, list[OcrArtifact]] = {}
        for artifact in ocr_artifacts:
            post_number = page_to_post.get(artifact.page_number)
            if post_number is None:
                continue
            ocr_by_post.setdefault(post_number, []).append(artifact)

        posts: list[LinkedInPostRecord] = []
        for post_number in sorted(post_pages):
            raw_post_text = "\n".join(post_pages[post_number])
            body_text = self._extract_body_text(raw_post_text)
            artifacts = ocr_by_post.get(post_number, [])
            combined_ocr_text = "\n".join(artifact.text for artifact in artifacts if artifact.text)
            pattern_input = f"{body_text}\n{combined_ocr_text}"
            patterns = self._extract_patterns(pattern_input)
            hooks = self._derive_research_hooks(pattern_input)
            post = LinkedInPostRecord(
                post_number=post_number,
                author=self._extract_author(raw_post_text),
                page_numbers=[page for page, post_id in page_to_post.items() if post_id == post_number],
                body_text=body_text,
                raw_text=raw_post_text,
                ocr_artifacts=artifacts,
                summary=self._summarize_post(body_text),
                diagram_intent=self._summarize_diagram_intent(body_text, artifacts),
                architecture_patterns=patterns,
                research_hooks=hooks,
            )
            post.namespace = self._infer_namespace(post)
            post.signal_score = self._score_post_signal(post)
            post.is_relevant, post.exclusion_reason = self._judge_post_relevance(post)
            posts.append(post)
        return posts

    def _split_posts(self, raw_text: str) -> tuple[dict[int, int], dict[int, list[str]]]:
        page_to_post: dict[int, int] = {}
        post_pages: dict[int, list[str]] = {}
        current_post: int | None = None

        for page_number, page_text in enumerate(raw_text.split("\f"), start=1):
            match = POST_MARKER.search(page_text)
            if match:
                current_post = int(match.group(1))
            if current_post is None:
                continue
            page_to_post[page_number] = current_post
            post_pages.setdefault(current_post, []).append(page_text)
        return page_to_post, post_pages

    def _extract_author(self, raw_post_text: str) -> str:
        lines = self._normalized_lines(raw_post_text)
        body_start_index = self._find_body_start_index(lines)
        header_lines = lines[:body_start_index] if body_start_index is not None else lines

        for index, line in enumerate(header_lines):
            if not self._is_author_candidate(line):
                continue
            window = header_lines[index + 1:index + 4]
            if any(self._is_header_status_line(candidate) for candidate in window):
                return line

        for line in header_lines:
            if self._is_author_candidate(line):
                return line
        return "Unknown author"

    def _extract_body_text(self, raw_post_text: str) -> str:
        lines = self._normalized_lines(raw_post_text)
        body_start_index = self._find_body_start_index(lines)
        candidate_lines = lines[body_start_index:] if body_start_index is not None else lines
        candidate_lines = self._strip_embedded_profile_headers(candidate_lines)
        body_lines: list[str] = []
        for line in candidate_lines:
            if self._should_skip_body_line(line):
                continue
            body_lines.append(line)
        return "\n".join(body_lines)

    def _strip_embedded_profile_headers(self, lines: list[str]) -> list[str]:
        cleaned: list[str] = []
        index = 0
        while index < len(lines):
            if self._looks_like_embedded_profile_header(lines, index):
                index = self._advance_past_embedded_profile_header(lines, index)
                continue
            cleaned.append(lines[index])
            index += 1
        return cleaned

    def _looks_like_embedded_profile_header(self, lines: list[str], index: int) -> bool:
        line = lines[index]
        if not self._is_author_candidate(line):
            return False
        status_window = lines[index + 1:index + 4]
        timestamp_window = lines[index + 1:index + 8]
        return any(self._is_header_status_line(candidate) for candidate in status_window) and any(
            self._is_timestamp_line(candidate) for candidate in timestamp_window
        )

    def _advance_past_embedded_profile_header(self, lines: list[str], index: int) -> int:
        cursor = index + 1
        while cursor < len(lines) and not self._is_timestamp_line(lines[cursor]):
            cursor += 1
        if cursor < len(lines) and self._is_timestamp_line(lines[cursor]):
            cursor += 1
        while cursor < len(lines) and self._is_pre_body_line(lines[cursor]):
            cursor += 1
        return cursor

    def _normalized_lines(self, raw_text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in raw_text.splitlines():
            line = unicodedata.normalize("NFKC", raw_line).replace("\u200b", " ")
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                lines.append(line)
        return lines

    def _find_body_start_index(self, lines: list[str]) -> int | None:
        for index, line in enumerate(lines):
            if self._is_timestamp_line(line):
                cursor = index + 1
                while cursor < len(lines) and self._is_pre_body_line(lines[cursor]):
                    cursor += 1
                return cursor
        return None

    def _is_timestamp_line(self, line: str) -> bool:
        return bool(SHORT_TIMESTAMP.match(line) or LONG_TIMESTAMP.match(line))

    def _is_header_status_line(self, line: str) -> bool:
        return any(
            token in line
            for token in (
                "• Following",
                "Premium",
                "Verified",
                "Influencer",
                "1st",
                "2nd",
                "3rd+",
                "Following",
            )
        )

    def _is_author_candidate(self, line: str) -> bool:
        if len(line) < 2 or len(line) > 80:
            return False
        if any(char.isdigit() for char in line):
            return False
        if re.search(r"[!?:;]", line):
            return False
        if self._should_skip_body_line(line) or self._is_pre_body_line(line):
            return False
        if self._is_header_status_line(line):
            return False
        if any(token in line for token in ("http://", "https://", "|", "@", "Views", "stars")):
            return False
        if line.lower() in {"all activity", "postscommentsimagesreactions"}:
            return False
        return any(char.isalpha() for char in line)

    def _is_pre_body_line(self, line: str) -> bool:
        return any(
            token in line
            for token in (
                "Visible to anyone",
                "Follow",
                "View my blog",
                "Visit my website",
                "View my newsletter",
                "Edited •",
            )
        )

    def _should_skip_body_line(self, line: str) -> bool:
        if line in {"Like", "Comment", "Repost", "Send", "…more"}:
            return True
        if re.fullmatch(r"[\d,]+", line):
            return True
        if re.fullmatch(r"[\d,]+\s+(comments|reposts)", line, flags=re.IGNORECASE):
            return True
        return any(
            token in line
            for token in (
                "Feed post number",
                "Brandt Pileggi likes this",
                "Brandt Pileggi liked",
                "Activate to view larger image",
                "Visible to anyone",
                "PostsCommentsImagesReactions",
                "Loaded ",
                "Author",
            )
        )

    def _infer_namespace(self, post: LinkedInPostRecord) -> str:
        lowered = f"{post.summary}\n{post.body_text}\n{post.diagram_intent}".lower()
        if any(keyword in lowered for keyword in ("architecture", "pattern", "context engineering", "ontology", "governance", "evaluation", "reasoning", "mixture-of-experts", "mamba")):
            return "frameworks"
        if any(keyword in lowered for keyword in ("repo", "github", "install", "sdk", "cli", "tool", "server", "browser", "api", "package", "deploy")):
            return "tools"
        if any(keyword in lowered for keyword in ("benchmark", "trend", "adoption", "stars", "launched", "dropped", "released", "open-sourced", "growing")):
            return "trends"
        return "general"

    def _score_post_signal(self, post: LinkedInPostRecord) -> float:
        lowered = f"{post.summary}\n{post.body_text}\n{post.diagram_intent}".lower()
        score = 0.0
        for keyword, weight in DOMAIN_SIGNAL_RULES:
            if keyword in lowered:
                score += weight
        score += len(post.architecture_patterns) * 1.3
        score += len(post.research_hooks) * 0.6
        score += sum(
            1.6 if artifact.visual_type == "architecture_diagram"
            else 1.1 if artifact.visual_type == "prompt_asset"
            else 0.6
            for artifact in post.ocr_artifacts
        )
        body_word_count = len(post.body_text.split())
        if body_word_count >= 180:
            score += 1.6
        elif body_word_count >= 80:
            score += 1.0
        elif body_word_count >= 30:
            score += 0.4
        for keyword, penalty in SOCIAL_NOISE_RULES:
            if keyword in lowered:
                score -= penalty
        return round(score, 2)

    def _judge_post_relevance(self, post: LinkedInPostRecord) -> tuple[bool, str]:
        lowered = f"{post.summary}\n{post.body_text}\n{post.diagram_intent}".lower()
        domain_relevant = any(keyword in lowered for keyword, _ in DOMAIN_SIGNAL_RULES)
        if not domain_relevant and not post.architecture_patterns and not post.ocr_artifacts:
            return False, "No meaningful AI/ML/agentics signals detected"
        if post.signal_score < MIN_RELEVANCE_SCORE:
            return False, "Below architectural insight threshold"
        return True, ""

    def _filter_relevant_posts(self, posts: list[LinkedInPostRecord]) -> list[LinkedInPostRecord]:
        filtered = [post for post in posts if post.is_relevant]
        filtered.sort(key=lambda post: (post.signal_score, post.post_number), reverse=True)
        filtered.sort(key=lambda post: post.post_number)
        return filtered

    def _post_to_knowledge_entry(
        self,
        post: LinkedInPostRecord,
        result: LinkedInPdfIngestResult,
    ) -> KnowledgeEntry:
        title_stem = post.summary.split(".")[0].strip() or f"LinkedIn post {post.post_number}"
        entry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{result.pdf_path}:{post.post_number}"))
        content = "\n".join(
            [
                f"Summary: {post.summary}",
                f"Diagram intent: {post.diagram_intent}",
                f"Architecture patterns: {', '.join(post.architecture_patterns) or 'None detected'}",
                f"Research hooks: {', '.join(post.research_hooks) or 'None detected'}",
                "Post body:",
                post.body_text,
            ]
        ).strip()
        confidence = min(0.98, 0.72 + (min(post.signal_score, 12.0) / 40.0))
        return KnowledgeEntry(
            entry_id=entry_id,
            title=f"{post.author} — {title_stem[:120]}",
            content=content,
            namespace=post.namespace,
            content_type="linkedin_pdf_post",
            source_name=f"LinkedIn PDF Export ({Path(result.pdf_path).name})",
            confidence=round(confidence, 2),
            metadata={
                "author": post.author,
                "post_number": post.post_number,
                "page_numbers": post.page_numbers,
                "pdf_path": result.pdf_path,
                "diagram_intent": post.diagram_intent,
                "architecture_patterns": post.architecture_patterns,
                "research_hooks": post.research_hooks,
                "signal_score": post.signal_score,
                "seeded_from": "linkedin_pdf_ingest",
            },
        )

    def _extract_patterns(self, text: str) -> list[str]:
        lowered = text.lower()
        patterns = [label for keyword, label in PATTERN_RULES if keyword in lowered]
        return sorted(dict.fromkeys(patterns))

    def _summarize_post(self, body_text: str) -> str:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", body_text) if segment.strip()]
        if not sentences:
            return "No body text was recoverable from this post export."
        return " ".join(sentences[:2])[:500]

    def _summarize_diagram_intent(self, body_text: str, artifacts: list[OcrArtifact]) -> str:
        if not artifacts:
            return "No diagram OCR was recovered for this post; interpret the visual from surrounding text only."

        visual_types = {artifact.visual_type for artifact in artifacts}
        combined_text = " ".join(artifact.text for artifact in artifacts)
        if "architecture_diagram" in visual_types:
            return (
                "The visual is communicating a systems or layered architecture view, emphasizing "
                f"components, flows, and operational boundaries. OCR recovered labels such as: {combined_text[:220]}"
            )
        if "prompt_asset" in visual_types:
            return (
                "The visual is communicating a reusable prompt, context, or operating template rather than "
                f"a runtime architecture diagram. OCR recovered labels such as: {combined_text[:220]}"
            )
        if "benchmark_or_chart" in visual_types:
            return (
                "The visual is communicating comparative performance or model-economics evidence that supports "
                f"the post's claim. OCR recovered labels such as: {combined_text[:220]}"
            )
        return (
            "The visual appears to reinforce the post's core point, but its structure is only partially "
            f"recoverable. OCR recovered labels such as: {combined_text[:220]}"
        )

    def _derive_research_hooks(self, text: str) -> list[str]:
        lowered = text.lower()
        hooks = [hook for keyword, hook in RESEARCH_HOOK_RULES if keyword in lowered]
        if not hooks:
            hooks.append(
                "Extract the strongest claims from this post and compare them against durable architecture seams in the repo."
            )
        return hooks[:4]

    def _recurring_patterns(self, posts: list[LinkedInPostRecord]) -> list[str]:
        counter = Counter(pattern for post in posts for pattern in post.architecture_patterns)
        return [pattern for pattern, _ in counter.most_common(10)]

    def _curiosity_queue(self, posts: list[LinkedInPostRecord]) -> list[str]:
        queue: list[str] = []
        for post in posts:
            queue.extend(post.research_hooks)
        return list(dict.fromkeys(queue))[:MAX_RESEARCH_HOOKS]

    def _extract_image_rows(self, pdf_path: Path, temp_dir: Path) -> list[dict[str, Any]]:
        image_list_output = self._run_command(["pdfimages", "-list", str(pdf_path)])
        self._run_command(["pdfimages", "-all", str(pdf_path), str(temp_dir / "img")])
        extracted_files = sorted(path.name for path in temp_dir.iterdir() if path.is_file())
        rows = self._parse_pdfimages_list(image_list_output)
        for row, file_name in zip(rows, extracted_files, strict=False):
            row["file_name"] = file_name
            row["file_path"] = str(temp_dir / file_name)
        return rows

    def _ocr_large_images(self, image_rows: list[dict[str, Any]]) -> list[OcrArtifact]:
        artifacts: list[OcrArtifact] = []
        for row in image_rows:
            width = int(row.get("width", 0))
            height = int(row.get("height", 0))
            if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                continue
            text = self._sanitize_external_text(
                self._run_command(["tesseract", row["file_path"], "stdout"]),
                context=row["file_name"],
            )
            artifacts.append(
                OcrArtifact(
                    page_number=int(row["page"]),
                    file_name=row["file_name"],
                    width=width,
                    height=height,
                    visual_type=self._classify_visual(text),
                    text=text.strip(),
                )
            )
        return artifacts

    def _classify_visual(self, ocr_text: str) -> str:
        lowered = ocr_text.lower()
        if any(keyword in lowered for keyword in ("architecture", "layer", "ontology", "agentic")):
            return "architecture_diagram"
        if any(keyword in lowered for keyword in ("prompt", "claude", "context", "document")):
            return "prompt_asset"
        if any(keyword in lowered for keyword in ("benchmark", "tokens per second", "tps", "faster")):
            return "benchmark_or_chart"
        return "visual_support"

    def _parse_pdfinfo(self, output: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        return metadata

    def _parse_pdfimages_list(self, output: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for line in output.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("page") or stripped.startswith("-"):
                continue
            parts = stripped.split()
            if len(parts) < 10:
                continue
            rows.append(
                {
                    "page": int(parts[0]),
                    "width": int(parts[3]),
                    "height": int(parts[4]),
                    "encoding": parts[8],
                }
            )
        return rows

    def _sanitize_external_text(self, text: str, context: str) -> str:
        sanitized = sanitize_text(text)
        if sanitized != text:
            logger.warning("Sanitized external text while processing %s", context)
        return sanitized

    def _write_bundle(self, result: LinkedInPdfIngestResult, raw_text: str) -> None:
        output_dir = Path(result.output_dir)
        (output_dir / "raw_text.txt").write_text(raw_text, encoding="utf-8")
        (output_dir / "ingest_result.json").write_text(
            json.dumps(result.to_dict(), indent=2),
            encoding="utf-8",
        )
        (output_dir / "centralized_report.md").write_text(
            self._render_report(result),
            encoding="utf-8",
        )

    def _render_report(self, result: LinkedInPdfIngestResult) -> str:
        lines = [
            f"# LinkedIn PDF Ingest Report — {Path(result.pdf_path).name}",
            "",
            "## Source",
            "",
            f"- PDF: `{result.pdf_path}`",
            f"- Pages: `{result.page_count}`",
            f"- Posts detected: `{result.total_posts_detected}`",
            f"- Posts retained: `{result.post_count}`",
            f"- Posts filtered out: `{result.filtered_out_count}`",
            f"- Knowledge entries seeded: `{result.knowledge_entries_seeded}`",
            f"- Generated at: `{result.generated_at.isoformat()}`",
            "",
            "## Recurring Architecture Patterns",
            "",
        ]
        lines.extend(f"- {pattern}" for pattern in result.recurring_patterns)
        lines.extend(["", "## Curiosity Queue", ""])
        lines.extend(f"- {hook}" for hook in result.curiosity_queue)
        lines.extend(["", "## Post Records", ""])

        for post in result.posts:
            lines.extend(
                [
                    f"### Post {post.post_number} — {post.author}",
                    "",
                    f"- Pages: `{', '.join(str(page) for page in post.page_numbers)}`",
                    f"- Namespace: `{post.namespace}`",
                    f"- Signal score: `{post.signal_score}`",
                    f"- Summary: {post.summary}",
                    f"- Diagram intent: {post.diagram_intent}",
                    "- Architecture patterns:",
                ]
            )
            lines.extend(f"  - {pattern}" for pattern in post.architecture_patterns)
            lines.append("- Research hooks:")
            lines.extend(f"  - {hook}" for hook in post.research_hooks)
            if post.ocr_artifacts:
                lines.append("- OCR snippets:")
                lines.extend(
                    f"  - `{artifact.file_name}` ({artifact.visual_type}): {artifact.text[:180]}"
                    for artifact in post.ocr_artifacts[:3]
                )
            lines.extend(["", "#### Body Extract", "", post.body_text[:1200], ""])

        return "\n".join(lines).strip() + "\n"

    def _run_command(self, args: list[str]) -> str:
        completed = subprocess.run(args, check=True, capture_output=True, text=True)
        return completed.stdout


def main() -> None:
    """CLI entry point for the LinkedIn PDF ingest pipeline."""
    parser = argparse.ArgumentParser(description="Ingest a LinkedIn PDF export into structured artifacts.")
    parser.add_argument("pdf_path", help="Path to the readable LinkedIn PDF export.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to data/ingests/<pdf-stem>.",
    )
    parser.add_argument(
        "--seed-knowledge-base",
        action="store_true",
        help="Persist the highest-signal posts into the SQLite knowledge base.",
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help="Knowledge base path used when --seed-knowledge-base is set.",
    )
    parser.add_argument(
        "--min-signal-score",
        type=float,
        default=DEFAULT_KNOWLEDGE_SEED_SCORE,
        help="Minimum signal score required for knowledge-base seeding.",
    )
    parser.add_argument(
        "--seed-limit",
        type=int,
        default=DEFAULT_KNOWLEDGE_SEED_LIMIT,
        help="Maximum number of high-signal posts to seed into the knowledge base.",
    )
    args = parser.parse_args()

    pipeline = LinkedInPdfIngestPipeline()
    result = pipeline.ingest_pdf(args.pdf_path, output_dir=args.output_dir)
    if args.seed_knowledge_base:
        pipeline.seed_knowledge_base(
            result=result,
            db_path=args.db_path,
            min_signal_score=args.min_signal_score,
            limit=args.seed_limit,
        )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()