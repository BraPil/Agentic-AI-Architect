#!/usr/bin/env python3
"""
Read raw YouTube transcripts from data/wiki/raw/<persona_id>/youtube_*.txt
and use Claude Haiku to extract structured ResearchSource entries, then
write them as KB entries and append to data/wiki/schema/research_sources.json.

Usage:
  ANTHROPIC_API_KEY=sk-... python3 scripts/extract_transcript_sources.py
  ANTHROPIC_API_KEY=sk-... python3 scripts/extract_transcript_sources.py --persona karpathy --dry-run

Requires: pip install anthropic
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

RAW_DIR = Path("data/wiki/raw")
SCHEMA_DIR = Path("data/wiki/schema")
SCHEMA_FILE = SCHEMA_DIR / "research_sources.json"

EXTRACTION_PROMPT = """\
You are ingesting a YouTube video transcript from {persona_name}'s channel into a structured research corpus.

Extract a ResearchSource object. Only include claims you can directly quote or clearly infer from the transcript. Do NOT hallucinate.

Return ONLY valid JSON matching this exact schema:
{{
  "directClaims": [],        // Exact paraphrased claims — precise and quotable
  "inferredBeliefs": [],     // Beliefs/philosophy inferable from patterns and word choices
  "mentionedTools": [],      // Every tool, library, platform, or product mentioned by name
  "workflowPatterns": [],    // Concrete workflow steps or patterns described
  "voiceSignals": [],        // 3-6 adjectives describing tone and communication style
  "summary": ""              // 2-3 sentence summary of what this video covers
}}

VIDEO TITLE: {title}
PUBLISHED: {published_at}
PERSONA: {persona_name}

TRANSCRIPT:
{transcript}

Return only the JSON object. No markdown, no explanation."""

PERSONA_NAMES = {
    "karpathy": "Andrej Karpathy",
    "cole_medin": "Cole Medin",
}


def confidence_for_date(date_str: str) -> str:
    if not date_str:
        return "low"
    ym = date_str[:7]
    if ym >= "2026-03":
        return "high"
    if ym >= "2026-01":
        return "medium"
    return "low"


def parse_header(text: str) -> dict:
    """Parse the YAML-like header from a raw transcript file."""
    header: dict = {}
    for line in text.split("---")[0].splitlines():
        if ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            header[k.strip()] = v.strip()
    return header


def extract_source(client: anthropic.Anthropic, persona_id: str, video_id: str,
                   title: str, published_at: str, transcript: str) -> dict | None:
    persona_name = PERSONA_NAMES.get(persona_id, persona_id)
    prompt = EXTRACTION_PROMPT.format(
        persona_name=persona_name,
        title=title,
        published_at=published_at or "unknown",
        transcript=transcript[:50_000],
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  API error: {e}")
        return None


def load_existing_ids() -> set[str]:
    if not SCHEMA_FILE.exists():
        return set()
    data = json.loads(SCHEMA_FILE.read_text())
    return {s["id"] for s in data.get("sources", [])}


def save_source(extracted: dict, persona_id: str, video_id: str,
                title: str, published_at: str) -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if SCHEMA_FILE.exists():
        existing = json.loads(SCHEMA_FILE.read_text())
    sources = existing.get("sources", [])

    entry = {
        "id": f"src-yt-{video_id}",
        "sourceType": "youtube",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": title,
        "publishedAt": published_at,
        "personaId": persona_id,
        "confidence": confidence_for_date(published_at),
        "extractedAt": datetime.now(timezone.utc).isoformat(),
        **extracted,
    }
    sources.append(entry)

    SCHEMA_FILE.write_text(json.dumps(
        {"schema_version": "1.0", "updated_at": datetime.now(timezone.utc).date().isoformat(),
         "sources": sources},
        indent=2, ensure_ascii=False,
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract structured sources from raw transcripts")
    parser.add_argument("--persona", nargs="+", default=list(PERSONA_NAMES),
                        choices=list(PERSONA_NAMES), help="Personas to process")
    parser.add_argument("--dry-run", action="store_true", help="Print extracted JSON, don't write")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    existing_ids = load_existing_ids()

    for persona_id in args.persona:
        persona_dir = RAW_DIR / persona_id
        if not persona_dir.exists():
            print(f"[SKIP] {persona_id} — no raw dir at {persona_dir}")
            continue

        transcript_files = sorted(persona_dir.glob("youtube_*.txt"), reverse=True)
        if not transcript_files:
            print(f"[SKIP] {persona_id} — no transcript files found")
            continue

        for txt_path in transcript_files:
            # Extract video_id from filename: youtube_<video_id>_<title>.txt
            parts = txt_path.stem.split("_", 2)
            video_id = parts[1] if len(parts) >= 2 else txt_path.stem

            src_id = f"src-yt-{video_id}"
            if src_id in existing_ids:
                print(f"[SKIP] {video_id} — already extracted")
                continue

            text = txt_path.read_text(encoding="utf-8")
            header = parse_header(text)
            title = header.get("# Transcript", "") or header.get("title", "") or video_id
            published_at = header.get("published_at", "")
            transcript = text.split("---\n\n", 1)[-1] if "---\n\n" in text else text

            print(f"[EXTRACT] [{persona_id}] {video_id} — {title[:70]}")
            extracted = extract_source(client, persona_id, video_id, title, published_at, transcript)

            if not extracted:
                print("  FAILED")
                continue

            claim_count = len(extracted.get("directClaims", []))
            tool_count = len(extracted.get("mentionedTools", []))
            print(f"  OK — {claim_count} claims, {tool_count} tools")

            if args.dry_run:
                print(json.dumps(extracted, indent=2))
            else:
                save_source(extracted, persona_id, video_id, title, published_at)
                existing_ids.add(src_id)

    if not args.dry_run:
        count = len(json.loads(SCHEMA_FILE.read_text()).get("sources", [])) if SCHEMA_FILE.exists() else 0
        print(f"\nresearch_sources.json now has {count} source(s).")


if __name__ == "__main__":
    main()
