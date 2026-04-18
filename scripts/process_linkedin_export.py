#!/usr/bin/env python3
"""
Process a LinkedIn export JSON file (produced by the AAA LinkedIn Exporter Chrome extension).

For each post:
  1. Extract and sanitize post text
  2. For each image: download and analyze with Claude Vision (if ANTHROPIC_API_KEY set)
  3. Combine text + vision analysis into a structured ResearchSource entry
  4. Write raw artifacts to data/wiki/raw/<persona_id>/
  5. Append to data/wiki/schema/research_sources.json
  6. Seed into KnowledgeBase

Usage:
  # Full pipeline with vision analysis
  ANTHROPIC_API_KEY=sk-... python3 scripts/process_linkedin_export.py \\
    --export downloads/linkedin_export_reactions_2026-04-18.json \\
    --persona brandtpileggi

  # Dry run (print extracted data, don't write)
  ANTHROPIC_API_KEY=sk-... python3 scripts/process_linkedin_export.py \\
    --export downloads/linkedin_export_reactions_2026-04-18.json \\
    --persona brandtpileggi --dry-run

  # Skip vision analysis (text only)
  python3 scripts/process_linkedin_export.py \\
    --export downloads/linkedin_export_reactions_2026-04-18.json \\
    --persona brandtpileggi --no-vision
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).parent.parent))

RAW_DIR = Path("data/wiki/raw")
SCHEMA_DIR = Path("data/wiki/schema")
SCHEMA_FILE = SCHEMA_DIR / "research_sources.json"

# ---------------------------------------------------------------------------
# Vision analysis prompt
# ---------------------------------------------------------------------------

VISION_PROMPT = """\
This is an image from a LinkedIn post. Describe what you see in detail, focusing on:

1. Any text visible in the image (charts, slides, infographics, captions, headlines)
2. The type of visualization (chart, diagram, screenshot, photo, infographic, table, etc.)
3. The key data or insight being communicated
4. Any notable statistics, percentages, or specific claims shown

Be specific and extract all readable text. This analysis will be used for knowledge base ingestion.
Keep your response under 300 words."""

TEXT_EXTRACTION_PROMPT = """\
Extract a structured ResearchSource from this LinkedIn post.

Return ONLY valid JSON:
{{
  "directClaims": [],      // Specific factual claims made — precise and quotable
  "inferredBeliefs": [],   // Beliefs/stances inferable from framing and word choice
  "mentionedTools": [],    // Tools, frameworks, platforms, companies mentioned
  "topics": [],            // Topic tags (e.g. "agentic-ai", "evaluation", "memory")
  "voiceSignals": [],      // 2-4 words describing tone (e.g. "technical", "practical")
  "summary": ""            // 1-2 sentence summary
}}

POST AUTHOR: {author}
POST TEXT:
{text}

IMAGE DESCRIPTIONS (if any):
{image_descriptions}

Return only the JSON object."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_existing_ids() -> set[str]:
    if not SCHEMA_FILE.exists():
        return set()
    data = json.loads(SCHEMA_FILE.read_text())
    return {s["id"] for s in data.get("sources", [])}


def save_source(entry: dict) -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if SCHEMA_FILE.exists():
        existing = json.loads(SCHEMA_FILE.read_text())
    sources = existing.get("sources", [])
    sources.append(entry)
    SCHEMA_FILE.write_text(json.dumps(
        {"schema_version": "1.0",
         "updated_at": datetime.now(timezone.utc).date().isoformat(),
         "sources": sources},
        indent=2, ensure_ascii=False,
    ))


def fetch_image_b64(url: str, timeout: int = 10) -> tuple[str, str] | None:
    """Download image, return (base64_data, media_type) or None."""
    if not url or url.startswith("data:"):
        return None
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AAA-Ingest/1.0)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            data = resp.read()
            if len(data) < 1000:
                return None
            return base64.b64encode(data).decode(), content_type
    except Exception:  # noqa: BLE001
        return None


def analyze_image(client, url: str, img_info: dict) -> str:
    """Use Claude Vision to describe an image from a post."""
    img_data = fetch_image_b64(url)
    if img_data is None:
        return f"[Image could not be downloaded: {url[:80]}]"

    b64, media_type = img_data
    if media_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        media_type = "image/jpeg"

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }],
        )
        return msg.content[0].text.strip()
    except Exception as e:  # noqa: BLE001
        return f"[Vision analysis failed: {e}]"


def extract_structure(client, author: str, text: str, image_descriptions: list[str]) -> dict | None:
    """Use Claude Haiku to extract structured ResearchSource from post text + image descriptions."""
    image_block = "\n".join(f"- {d}" for d in image_descriptions) if image_descriptions else "None"
    prompt = TEXT_EXTRACTION_PROMPT.format(
        author=author or "unknown",
        text=text[:8000],
        image_descriptions=image_block,
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
    except Exception as e:  # noqa: BLE001
        print(f"  Extraction error: {e}")
        return None


def post_id_from_url(url: str) -> str:
    m = re.search(r"activity[:-](\d+)", url or "")
    if m:
        return f"li-{m.group(1)}"
    return f"li-{abs(hash(url or ''))}"


def sanitize(text: str) -> str:
    """Basic text sanitization."""
    text = re.sub(r"\s{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Process LinkedIn Chrome extension export")
    parser.add_argument("--export", required=True, help="Path to the JSON export file")
    parser.add_argument("--persona", required=True, help="Persona ID (e.g. brandtpileggi, karpathy)")
    parser.add_argument("--dry-run", action="store_true", help="Print extracted data, don't write")
    parser.add_argument("--no-vision", action="store_true", help="Skip image analysis")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N posts (0 = all)")
    args = parser.parse_args()

    export_path = Path(args.export)
    if not export_path.exists():
        print(f"ERROR: Export file not found: {export_path}")
        sys.exit(1)

    export = json.loads(export_path.read_text())
    posts = export.get("posts", [])
    page_url = export.get("page_url", "")
    scraped_at = export.get("scraped_at", "")

    print(f"Loaded {len(posts)} posts from {export_path.name}")
    print(f"Source page: {page_url}")
    print(f"Scraped at:  {scraped_at}\n")

    if args.limit:
        posts = posts[:args.limit]

    # Set up clients
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = None
    use_vision = not args.no_vision and api_key
    use_extraction = bool(api_key)

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print("anthropic not installed. Text/vision extraction disabled.")
            print("Run: pip install anthropic\n")
    elif not args.no_vision:
        print("ANTHROPIC_API_KEY not set — running in text-only mode (no vision/extraction).\n")

    existing_ids = load_existing_ids()
    persona_dir = RAW_DIR / args.persona
    if not args.dry_run:
        persona_dir.mkdir(parents=True, exist_ok=True)

    processed = skipped = failed = 0

    for i, post in enumerate(posts):
        post_url = post.get("post_url", "")
        author = post.get("author", "")
        text = sanitize(post.get("text", ""))
        images = post.get("images", [])
        timestamp = post.get("timestamp", "")

        src_id = post_id_from_url(post_url)
        if src_id in existing_ids:
            print(f"[SKIP] {src_id} ({author[:30]})")
            skipped += 1
            continue

        author_display = author[:50] or "unknown"
        print(f"[{i+1}/{len(posts)}] {src_id} — {author_display}")
        if text:
            print(f"  Text: {text[:80]}{'…' if len(text) > 80 else ''}")

        # Vision analysis for images
        image_descriptions: list[str] = []
        for j, img in enumerate(images[:5]):  # cap at 5 images per post
            img_url = img.get("src", "")
            if not img_url:
                continue
            if use_vision and client:
                print(f"  Vision: image {j+1}/{min(len(images), 5)}…")
                desc = analyze_image(client, img_url, img)
                image_descriptions.append(desc)
                time.sleep(0.5)
            else:
                alt = img.get("alt", "")
                image_descriptions.append(f"[Image: {alt or img_url[:60]}]")

        # Structured extraction
        extracted: dict = {}
        if use_extraction and client and (text or image_descriptions):
            extracted = extract_structure(client, author, text, image_descriptions) or {}
            if extracted:
                print(f"  Extracted: {len(extracted.get('directClaims', []))} claims, "
                      f"{len(extracted.get('mentionedTools', []))} tools")

        # Build raw artifact content
        raw_content = (
            f"# LinkedIn Post\n"
            f"post_url: {post_url}\n"
            f"author: {author}\n"
            f"author_url: {post.get('author_url', '')}\n"
            f"timestamp: {timestamp}\n"
            f"post_type: {post.get('post_type', 'text')}\n"
            f"scraped_at: {scraped_at}\n"
            f"image_count: {len(images)}\n\n"
            "---\n\n"
            f"{text}\n"
        )
        if image_descriptions:
            raw_content += "\n\n## Image Analyses\n\n"
            for k, desc in enumerate(image_descriptions, 1):
                raw_content += f"### Image {k}\n{desc}\n\n"

        if not args.dry_run:
            # Write raw artifact
            safe_id = re.sub(r"[^\w\-]", "_", src_id)
            raw_path = persona_dir / f"linkedin_{safe_id}.md"
            raw_path.write_text(raw_content, encoding="utf-8")

            # Build schema entry
            entry = {
                "id": src_id,
                "sourceType": "linkedin",
                "url": post_url,
                "author": author,
                "authorUrl": post.get("author_url", ""),
                "timestamp": timestamp,
                "postType": post.get("post_type", "text"),
                "personaId": args.persona,
                "pageUrl": page_url,
                "text": text,
                "imageDescriptions": image_descriptions,
                "confidence": "high" if text else "medium",
                "extractedAt": datetime.now(timezone.utc).isoformat(),
                "rawPath": str(raw_path),
                **extracted,
            }
            save_source(entry)
            existing_ids.add(src_id)

            # Seed into KnowledgeBase
            try:
                from src.knowledge.knowledge_base import KnowledgeBase, KnowledgeEntry
                from src.utils.helpers import sanitize_text
                kb = KnowledgeBase()
                kb.initialize()
                combined = text
                if image_descriptions:
                    combined += "\n\nImage analyses:\n" + "\n".join(image_descriptions)
                kb.store(KnowledgeEntry(
                    title=f"LinkedIn: {author} — {text[:60]}",
                    content=sanitize_text(combined)[:10_000],
                    namespace="general",
                    content_type="linkedin_post",
                    source_url=post_url,
                    source_name=f"linkedin_{src_id}",
                    confidence=0.8,
                    metadata={"persona_id": args.persona, "author": author,
                               "post_type": post.get("post_type", "text"),
                               "image_count": len(images)},
                ))
            except Exception as e:  # noqa: BLE001
                print(f"  KB seed warning: {e}")
        else:
            print(f"  DRY RUN — would write: {src_id}")
            if image_descriptions:
                for desc in image_descriptions:
                    print(f"    IMG: {desc[:100]}")
            if extracted:
                print(f"    {json.dumps(extracted, indent=6)[:300]}")

        processed += 1
        time.sleep(0.3)

    print(f"\n── Summary {'─' * 40}")
    print(f"  Processed: {processed}  Skipped: {skipped}  Failed: {failed}")
    if not args.dry_run and processed:
        count = len(json.loads(SCHEMA_FILE.read_text()).get("sources", [])) if SCHEMA_FILE.exists() else 0
        print(f"  research_sources.json now has {count} source(s).")
        print(f"  Raw artifacts in: {persona_dir}/")


if __name__ == "__main__":
    main()
