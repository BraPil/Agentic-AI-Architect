#!/usr/bin/env python3
"""
Re-enrich blog posts that were indexed without Claude extraction.

Identifies ChromaDB blog_post entries where topics is empty (text-only ingest),
then runs Claude Haiku extraction on their stored document text and patches the
metadata in-place using ChromaDB's update() — no delete or feed re-fetch needed.

This approach works even for posts that have rotated out of the live RSS/Atom feed.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/reenrich_blogs.py
  python3 scripts/reenrich_blogs.py --dry-run   # show what would be re-enriched
  python3 scripts/reenrich_blogs.py --persona simon-willison  # single persona slug
  python3 scripts/reenrich_blogs.py --limit 20  # process at most N posts
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("reenrich_blogs")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.linkedin_persona_store import LinkedInPersonaStore

_REQUEST_DELAY = 1.5
_MAX_CONTENT_CHARS = 8000

_EXTRACTION_PROMPT = """\
You are ingesting a blog post into a structured AI architecture knowledge base.

Extract a ResearchSource object. Only include what you can directly infer from the text.

Return ONLY valid JSON:
{{
  "directClaims": [],      // Specific factual or technical claims — precise and quotable
  "inferredBeliefs": [],   // Beliefs/stances inferable from framing and word choice
  "mentionedTools": [],    // Every tool, library, framework, platform mentioned by name
  "topics": [],            // Topic tags (e.g. "agentic-ai", "RAG", "evaluation", "memory")
  "voiceSignals": [],      // 2-4 adjectives describing tone (e.g. "analytical", "practical")
  "summary": ""            // 2-3 sentence summary of the post's key insight
}}

AUTHOR: {author}
TITLE: {title}

TEXT:
{text}

Return only the JSON object. No markdown."""


def _extract(client, doc_text: str, author: str, title: str) -> dict | None:
    """Run Claude Haiku extraction on stored document text."""
    prompt = _EXTRACTION_PROMPT.format(
        author=author,
        title=title,
        text=doc_text[:_MAX_CONTENT_CHARS],
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Extraction failed: %s", exc)
        return None


def find_unenriched(store: LinkedInPersonaStore, persona_filter: str | None) -> list[dict]:
    """Return blog_post entries with empty topics — not yet enriched by Claude."""
    result = store._collection.get(
        where={"post_type": "blog_post"},
        include=["documents", "metadatas"],
    )
    unenriched = []
    for pid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"]):
        if meta.get("topics", "").strip():
            continue  # already enriched
        if persona_filter and meta.get("persona_id") != persona_filter:
            continue
        unenriched.append({"post_id": pid, "document": doc, "metadata": meta})
    return unenriched


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-enrich unenriched blog posts in-place")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--persona", help="Restrict to persona slug, e.g. simon-willison")
    parser.add_argument("--limit", type=int, default=0, help="Max posts to process (0 = all)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        logger.error("ANTHROPIC_API_KEY not set. Set it or use --dry-run.")
        sys.exit(1)

    store = LinkedInPersonaStore()
    store.initialize()

    entries = find_unenriched(store, args.persona)
    if not entries:
        logger.info("No unenriched blog posts found.")
        return

    if args.limit:
        entries = entries[: args.limit]

    # Group for display
    by_persona: dict[str, int] = {}
    for e in entries:
        pid = e["metadata"].get("persona_id", "?")
        by_persona[pid] = by_persona.get(pid, 0) + 1

    print(f"\nFound {len(entries)} unenriched blog posts to re-enrich:")
    for pid, count in sorted(by_persona.items(), key=lambda x: -x[1]):
        print(f"  {pid:<35}  {count:>3} posts")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    import anthropic  # noqa: PLC0415
    client = anthropic.Anthropic(api_key=api_key)

    enriched = 0
    failed = 0

    print()
    for i, entry in enumerate(entries):
        post_id = entry["post_id"]
        meta = entry["metadata"]
        doc = entry["document"]
        author = meta.get("author", meta.get("persona_id", "unknown"))
        # Title is usually the first line of the document
        title_guess = doc.split("\n")[0][:80] if doc else ""

        if i > 0:
            time.sleep(_REQUEST_DELAY)

        extracted = _extract(client, doc, author, title_guess)
        if not extracted:
            failed += 1
            logger.warning("  [%d/%d] Failed: %s", i + 1, len(entries), post_id)
            continue

        # Patch metadata in-place — ChromaDB update() preserves the embedding
        new_meta = dict(meta)
        new_meta["mentioned_tools"] = ", ".join(extracted.get("mentionedTools", []))
        new_meta["topics"] = ", ".join(extracted.get("topics", []))
        new_meta["voice_signals"] = ", ".join(extracted.get("voiceSignals", []))
        if extracted.get("summary"):
            new_meta["summary"] = extracted["summary"][:500]

        # Rebuild document to include extracted content (improves retrieval)
        extra_parts = []
        if extracted.get("summary"):
            extra_parts.append(extracted["summary"])
        if extracted.get("directClaims"):
            extra_parts.append("Key claims: " + " | ".join(extracted["directClaims"][:5]))
        if extracted.get("mentionedTools"):
            extra_parts.append("Tools: " + ", ".join(extracted["mentionedTools"]))
        if extracted.get("topics"):
            extra_parts.append("Topics: " + ", ".join(extracted["topics"]))

        new_doc = doc.strip()
        if extra_parts:
            new_doc = new_doc + "\n\n" + "\n".join(extra_parts)

        try:
            store._collection.update(
                ids=[post_id],
                documents=[new_doc],
                metadatas=[new_meta],
            )
            enriched += 1
            n_tools = len(extracted.get("mentionedTools", []))
            n_topics = len(extracted.get("topics", []))
            logger.info(
                "  [%d/%d] %s — %d tools, %d topics",
                i + 1, len(entries), title_guess[:55], n_tools, n_topics,
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logger.warning("  [%d/%d] Update failed (%s): %s", i + 1, len(entries), post_id, exc)

    print(f"\n── Re-enrichment complete: {enriched} updated, {failed} failed ──")

    if enriched > 0:
        print("\nExporting updated ChromaDB snapshot…")
        import subprocess  # noqa: PLC0415
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "export_chromadb_snapshot.py")],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Snapshot exported.")
        else:
            logger.warning("Snapshot export failed: %s", result.stderr[:200])


if __name__ == "__main__":
    main()
