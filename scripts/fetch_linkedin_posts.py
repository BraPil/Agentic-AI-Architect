#!/usr/bin/env python3
"""
Ingest LinkedIn posts for AAA priority personas into data/wiki/raw/<persona_id>/

── WHAT LINKEDIN POST DATA IS AVAILABLE ───────────────────────────────────

LinkedIn is auth-blocked for anonymous scraping. Three practical paths:

PATH A — Your own posts (LinkedIn data export):
  1. Go to linkedin.com → Me → Settings & Privacy → Data Privacy
  2. "Get a copy of your data" → select "Posts" → Request archive
  3. You'll receive a .zip file within 10 minutes to a few days
  4. Extract it; you'll find posts.csv inside
  5. Run:  python3 scripts/fetch_linkedin_posts.py --csv path/to/posts.csv --persona brandtpileggi

PATH B — Other people's posts (manual copy + paste):
  For priority personas (Karpathy, Cole Medin, etc.) LinkedIn posts are
  auth-blocked. Options:
  a. Copy post text manually and place in data/wiki/raw/<persona_id>/linkedin_posts.txt
     (one post per line, or separated by ---), then run:
       python3 scripts/fetch_linkedin_posts.py --txt data/wiki/raw/karpathy/linkedin_posts.txt --persona karpathy
  b. Use a LinkedIn Sales Navigator cookie + curl (advanced)
  c. Wait for persona to mirror posts to public platforms

PATH C — LinkedIn PDF export (already supported):
  Use the existing linkedin_pdf_ingest.py pipeline if you exported your own
  LinkedIn data as a PDF (see docs/linkedin-pdf-ingest-pipeline-v1.md).

─────────────────────────────────────────────────────────────────────────────

After ingestion, run:
  ANTHROPIC_API_KEY=sk-... python3 scripts/extract_linkedin_sources.py
"""

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RAW_DIR = Path("data/wiki/raw")


def ingest_csv(csv_path: Path, persona_id: str) -> int:
    """Ingest LinkedIn data export CSV (posts.csv format)."""
    persona_dir = RAW_DIR / persona_id
    persona_dir.mkdir(parents=True, exist_ok=True)

    posts = []
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # LinkedIn data export CSV columns vary; try common ones
            text = (
                row.get("ShareCommentary") or
                row.get("Content") or
                row.get("Text") or
                row.get("text") or ""
            ).strip()
            date = (
                row.get("Date") or
                row.get("date") or
                row.get("Timestamp") or ""
            ).strip()
            url = (
                row.get("ShareLink") or
                row.get("URL") or
                row.get("url") or ""
            ).strip()
            if text:
                posts.append({"text": text, "date": date, "url": url})

    if not posts:
        print(f"No posts found in {csv_path}. Check column names.")
        return 0

    out_path = persona_dir / f"linkedin_posts_csv_{datetime.now(timezone.utc).date().isoformat()}.json"
    import json
    out_path.write_text(json.dumps({"persona_id": persona_id, "source": "csv_export",
                                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                                    "posts": posts}, indent=2))
    print(f"Wrote {len(posts)} posts → {out_path}")
    return len(posts)


def ingest_txt(txt_path: Path, persona_id: str) -> int:
    """Ingest manually copied LinkedIn posts from a plain text file."""
    persona_dir = RAW_DIR / persona_id
    persona_dir.mkdir(parents=True, exist_ok=True)

    raw = txt_path.read_text(encoding="utf-8")
    # Split on --- separators or double newlines between obvious post boundaries
    chunks = [c.strip() for c in re.split(r"\n---+\n|\n{3,}", raw) if c.strip()]
    posts = [{"text": chunk, "date": "", "url": ""} for chunk in chunks]

    if not posts:
        print("No posts found in txt file.")
        return 0

    out_path = persona_dir / f"linkedin_posts_manual_{datetime.now(timezone.utc).date().isoformat()}.json"
    import json
    out_path.write_text(json.dumps({"persona_id": persona_id, "source": "manual_copy",
                                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                                    "posts": posts}, indent=2))
    print(f"Wrote {len(posts)} posts → {out_path}")
    return len(posts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest LinkedIn posts for AAA personas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--csv", help="Path to LinkedIn data export posts.csv")
    parser.add_argument("--txt", help="Path to manually copied posts text file")
    parser.add_argument("--persona", required=True,
                        help="Persona ID (e.g. karpathy, cole_medin, brandtpileggi)")
    args = parser.parse_args()

    if not args.csv and not args.txt:
        parser.print_help()
        print("\nERROR: provide --csv or --txt")
        sys.exit(1)

    count = 0
    if args.csv:
        count += ingest_csv(Path(args.csv), args.persona)
    if args.txt:
        count += ingest_txt(Path(args.txt), args.persona)

    if count:
        print(f"\n{count} post(s) ingested.")
        print("Next: ANTHROPIC_API_KEY=sk-... python3 scripts/extract_linkedin_sources.py")
    else:
        print("No posts ingested. Check the file format.")


if __name__ == "__main__":
    main()
