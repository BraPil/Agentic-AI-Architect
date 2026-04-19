#!/usr/bin/env python3
"""
Fetch YouTube transcripts for AAA priority personas and write raw artifacts
to data/wiki/raw/<persona_id>/youtube_<video_id>_<title>.txt

── HOW TO GET THIS WORKING ─────────────────────────────────────────────────

OPTION A — Browser cookies (recommended, free, works from Codespace):
  1. In Chrome/Edge, install: "Get cookies.txt LOCALLY"
     https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
  2. Go to https://www.youtube.com and make sure you're signed in to Google.
  3. Click the extension icon → "Export" → save as scripts/cookies.txt
  4. In the Codespace terminal:
       pip install yt-dlp
       python3 scripts/fetch_youtube_transcripts.py --cookies scripts/cookies.txt

OPTION B — Run locally (no setup required if youtube-transcript-api works):
  On your local machine (non-cloud IP):
       pip install youtube-transcript-api yt-dlp
       python3 scripts/fetch_youtube_transcripts.py

OPTION C — Residential proxy (~$5/mo via Webshare or similar):
       PROXY_URL=http://user:pass@host:port python3 scripts/fetch_youtube_transcripts.py

After fetching, run the LLM extraction step:
  ANTHROPIC_API_KEY=sk-... python3 scripts/extract_transcript_sources.py

─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.youtube_ingest import YouTubeIngestPipeline, VideoTarget

# ---------------------------------------------------------------------------
# Video registries — add/update as channels publish new content
# ---------------------------------------------------------------------------

KARPATHY_VIDEOS = [
    # Newest first. Update by re-running the channel discovery script.
    {"id": "EWvNQjAaOHw", "title": "Vibe coding and why it's important"},
    {"id": "7xTGNNLPyMI", "title": "autoresearch - autonomous AI research overview"},
    {"id": "l8pRSuU81PU", "title": "LLM OS talk"},
    {"id": "zduSFxRajkE", "title": "Stanford / Lex podcast"},
    {"id": "zjkBMFhNj_g", "title": "GPT-4 era talk"},
    {"id": "kCc8FmEb1nY", "title": "Let's build GPT from scratch"},
    {"id": "t3YJ5hKiMQ0", "title": "State of GPT"},
    {"id": "q8SA3rM6ckI", "title": "Intro to Large Language Models"},
    {"id": "P6sfmUTpUmc", "title": "Neural networks: zero to hero intro"},
    {"id": "TCH_1BHY58I", "title": "How I think about LLM prompt engineering"},
]

COLE_MEDIN_VIDEOS = [
    # From ColeBot's verified video list (newest first)
    {"id": "HAkSUBdsd6M", "title": "Coding Agent Reliability EXPLODES When They Argue (Adversarial Dev)", "date": "2026-04-09"},
    {"id": "qMnClynCAmM", "title": "The Next Evolution of AI Coding Is Harnesses - Archon", "date": "2026-04-09"},
    {"id": "7huCP6RkcY4", "title": "I Built Self-Evolving Claude Code Memory w/ Karpathy's LLM Knowledge Bases", "date": "2026-04-07"},
    {"id": "1FiER-40zng", "title": "Full Guide - Build Your Own AI Second Brain with Claude Code", "date": "2026-04-02"},
    {"id": "gmaHRwijOXs", "title": "Everything You Thought About Building AI Agents is Wrong", "date": "2026-03-26"},
    {"id": "uegyRTOrXSU", "title": "You're Hardly Using What Claude Code Has to Offer", "date": "2026-03-23"},
    {"id": "nxHKBq5ZU9U", "title": "I've Used Claude Code for 2,000+ Hours - Here's How I Build Anything", "date": "2026-03-17"},
    {"id": "NMWgXvm--to", "title": "Stripe's Coding Agents Ship 1,300 PRs EVERY Week", "date": "2026-03-14"},
    {"id": "tjBpm91ZQM0", "title": "Is Software Engineering Finally Dead?", "date": "2026-03-11"},
    {"id": "goOZSXmrYQ4", "title": "My COMPLETE Agentic Coding Workflow to Build Anything", "date": "2026-02-20"},
]

PERSONA_MAP = {
    "karpathy": KARPATHY_VIDEOS,
    "cole_medin": COLE_MEDIN_VIDEOS,
}


def build_targets(persona_ids: list[str]) -> list[VideoTarget]:
    targets = []
    for pid in persona_ids:
        videos = PERSONA_MAP.get(pid, [])
        for v in videos:
            targets.append(VideoTarget(
                video_id=v["id"],
                persona_id=pid,
                title=v.get("title", ""),
                published_at=v.get("date", ""),
            ))
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts for AAA priority personas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("─" * 5)[0],
    )
    parser.add_argument("--persona", choices=list(PERSONA_MAP), nargs="+",
                        default=list(PERSONA_MAP), help="Personas to ingest (default: all)")
    parser.add_argument("--video", help="Single video ID (must match a video in the registry)")
    parser.add_argument("--cookies", help="Path to cookies.txt exported from browser")
    parser.add_argument("--proxy", help="Proxy URL (overrides PROXY_URL env var)")
    parser.add_argument("--raw-dir", default="data/wiki/raw", help="Raw artifact output directory")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between requests")
    args = parser.parse_args()

    proxy_url = args.proxy or os.environ.get("PROXY_URL")
    cookies_path = args.cookies

    if not cookies_path and not proxy_url:
        if os.path.exists("/.dockerenv") or os.environ.get("CODESPACE_NAME"):
            print("⚠  Running in a cloud environment with no cookies or proxy.")
            print("   YouTube will block requests from this IP.")
            print("   See the instructions at the top of this script.\n")

    targets = build_targets(args.persona)
    if args.video:
        targets = [t for t in targets if t.video_id == args.video]
        if not targets:
            print(f"Video ID '{args.video}' not found in registry for personas: {args.persona}")
            sys.exit(1)

    pipeline = YouTubeIngestPipeline(
        raw_dir=args.raw_dir,
        cookies_path=cookies_path,
        proxy_url=proxy_url,
        request_delay=args.delay,
    )

    print(f"Fetching {len(targets)} transcript(s)...\n")
    results = pipeline.run(targets)

    ok = [r for r in results if r.success]
    fail = [r for r in results if not r.success]

    print(f"\n── Summary {'─' * 40}")
    for r in ok:
        if r.transcript_chars:
            print(f"  ✓  [{r.persona_id}] {r.video_id} — {r.transcript_chars:,} chars → {r.raw_path}")
    for r in fail:
        print(f"  ✗  [{r.persona_id}] {r.video_id} — {r.error[:100]}")
    print(f"\n  OK: {len(ok)}  Failed: {len(fail)}")

    new_transcripts = [r for r in ok if r.transcript_chars]
    if new_transcripts:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        mode = "--no-extract" if not api_key else ""
        print(f"\nAuto-embedding {len(new_transcripts)} transcript(s) into ChromaDB "
              f"({'text-only' if not api_key else 'with Claude extraction'})…")
        import subprocess  # noqa: PLC0415
        cmd = [sys.executable, "scripts/extract_transcript_sources.py"]
        if mode:
            cmd.append(mode)
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
