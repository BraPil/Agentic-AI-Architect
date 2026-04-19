#!/usr/bin/env python3
"""
Automated corpus refresh — ingests new content from all configured sources and
exports an updated ChromaDB snapshot.

Runs all ingest pipelines in sequence:
  1. Blog posts (RSS/Atom feeds — all BLOG_REGISTRY sources)
  2. arXiv paper abstracts

Can be scheduled via cron or run directly as a one-shot refresh.

Usage:
  # One-shot refresh
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/refresh_corpus.py

  # Dry run (fetch feeds but skip ChromaDB writes and snapshot export)
  python3 scripts/refresh_corpus.py --dry-run

  # Daemon mode (run on a schedule using APScheduler)
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/refresh_corpus.py --daemon --interval-hours 24

  # Cron mode (add to crontab — runs once and exits)
  # 0 6 * * 1  cd /path/to/Agentic-AI-Architect && ANTHROPIC_API_KEY=sk-ant-... python3 scripts/refresh_corpus.py
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("refresh_corpus")

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))


def run_blog_ingest(api_key: str | None, dry_run: bool) -> dict:
    """Ingest new blog posts from all registered feeds."""
    logger.info("── Blog ingest ──────────────────────────────")
    if dry_run:
        logger.info("DRY RUN: skipping blog ingest")
        return {"status": "skipped", "added": 0}

    try:
        from src.pipeline.blog_ingest import BLOG_REGISTRY, BlogIngestPipeline  # noqa: PLC0415

        pipeline = BlogIngestPipeline(anthropic_api_key=api_key)
        results = pipeline.run()
        total_added = sum(r.added for r in results)
        total_skipped = sum(r.skipped for r in results)
        for r in results:
            logger.info(
                "  %s: %d added, %d skipped, %d failed",
                r.author, r.added, r.skipped, r.failed,
            )
            for err in r.errors:
                logger.warning("    Error: %s", err)
        logger.info("Blog total: %d new posts added", total_added)
        return {"status": "ok", "added": total_added, "skipped": total_skipped,
                "sources": len(BLOG_REGISTRY)}
    except Exception as exc:  # noqa: BLE001
        logger.error("Blog ingest failed: %s", exc)
        return {"status": "error", "error": str(exc), "added": 0}


def run_arxiv_ingest(api_key: str | None, dry_run: bool) -> dict:
    """Ingest new arXiv paper abstracts."""
    logger.info("── arXiv ingest ─────────────────────────────")
    if dry_run:
        logger.info("DRY RUN: skipping arXiv ingest")
        return {"status": "skipped", "added": 0}

    try:
        from src.pipeline.arxiv_ingest import ArxivIngestPipeline  # noqa: PLC0415

        pipeline = ArxivIngestPipeline(anthropic_api_key=api_key)
        result = pipeline.run()
        logger.info("arXiv total: %d new papers added", result.added)
        return {"status": "ok", "added": result.added, "skipped": result.skipped}
    except Exception as exc:  # noqa: BLE001
        logger.error("arXiv ingest failed: %s", exc)
        return {"status": "error", "error": str(exc), "added": 0}


def run_snapshot_export(dry_run: bool) -> bool:
    """Export ChromaDB snapshot to JSON."""
    logger.info("── Snapshot export ──────────────────────────")
    if dry_run:
        logger.info("DRY RUN: skipping snapshot export")
        return True
    try:
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "scripts" / "export_chromadb_snapshot.py")],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("Snapshot exported successfully")
            return True
        else:
            logger.warning("Snapshot export returned non-zero: %s", result.stderr[:200])
            return False
    except Exception as exc:  # noqa: BLE001
        logger.error("Snapshot export failed: %s", exc)
        return False


def _get_top_tools(n: int = 20) -> dict[str, int]:
    """Return {tool_name: mention_count} for the top-n tools."""
    try:
        from src.api.mcp_server import _get_store, _get_all_items  # noqa: PLC0415
        from collections import Counter  # noqa: PLC0415
        store = _get_store()
        items = _get_all_items(store)
        counter: Counter = Counter()
        for item in items:
            tools_str = item.get("metadata", {}).get("mentioned_tools", "")
            for t in tools_str.split(","):
                t = t.strip()
                if t:
                    counter[t] += 1
        return dict(counter.most_common(n))
    except Exception:  # noqa: BLE001
        return {}


def _detect_and_notify(before: dict[str, int], after: dict[str, int], corpus_size: int) -> None:
    """Compare tool rankings before/after and fire webhook alerts if significant shifts."""
    try:
        from src.api.webhook import WebhookRegistry  # noqa: PLC0415
        registry = WebhookRegistry()
        if not registry.list_subscribers():
            return

        before_ranks = {t: i for i, t in enumerate(before)}
        after_ranks = {t: i for i, t in enumerate(after)}

        new_tools = [t for t in after if t not in before]
        rank_shifts = {}
        for tool in set(before) & set(after):
            delta = before_ranks.get(tool, 99) - after_ranks.get(tool, 99)
            if abs(delta) >= 2:
                rank_shifts[tool] = delta

        if new_tools or rank_shifts:
            results = registry.notify_tool_change(
                new_tools=new_tools, rank_shifts=rank_shifts, corpus_size=corpus_size,
            )
            delivered = sum(1 for r in results if r.get("status") == "delivered")
            logger.info("Webhook alerts: %d/%d delivered", delivered, len(results))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Webhook notification failed: %s", exc)


def run_refresh_cycle(api_key: str | None, dry_run: bool) -> dict:
    """Run one full refresh cycle: blog → arXiv → snapshot."""
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("Starting corpus refresh cycle at %s", started_at)

    tools_before = _get_top_tools() if not dry_run else {}

    blog_result = run_blog_ingest(api_key, dry_run)
    arxiv_result = run_arxiv_ingest(api_key, dry_run)

    total_added = blog_result.get("added", 0) + arxiv_result.get("added", 0)

    snapshot_ok = False
    if total_added > 0 or dry_run:
        snapshot_ok = run_snapshot_export(dry_run)
    else:
        logger.info("No new content added — skipping snapshot export")

    if total_added > 0 and not dry_run:
        tools_after = _get_top_tools()
        try:
            from src.api.mcp_server import _get_store  # noqa: PLC0415
            corpus_size = _get_store().count
        except Exception:  # noqa: BLE001
            corpus_size = 0
        _detect_and_notify(tools_before, tools_after, corpus_size)

    result = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "total_added": total_added,
        "blog": blog_result,
        "arxiv": arxiv_result,
        "snapshot_exported": snapshot_ok,
        "dry_run": dry_run,
    }

    logger.info(
        "Refresh complete: %d new items added (blog=%d, arxiv=%d)",
        total_added, blog_result.get("added", 0), arxiv_result.get("added", 0),
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated AAA corpus refresh")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch feeds but skip all writes")
    parser.add_argument("--daemon", action="store_true",
                        help="Run continuously on a schedule (requires apscheduler)")
    parser.add_argument("--interval-hours", type=float, default=24.0,
                        help="Refresh interval in daemon mode (default: 24h)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — running without Claude extraction")

    if args.daemon:
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: PLC0415
        except ImportError:
            logger.error("APScheduler not installed. Run: pip install apscheduler")
            sys.exit(1)

        scheduler = BlockingScheduler()
        interval_seconds = int(args.interval_hours * 3600)

        logger.info(
            "Starting daemon mode — refresh every %.1f hours (%d seconds)",
            args.interval_hours, interval_seconds,
        )

        # Run immediately on start, then on schedule
        run_refresh_cycle(api_key, args.dry_run)

        scheduler.add_job(
            run_refresh_cycle,
            "interval",
            seconds=interval_seconds,
            args=[api_key, args.dry_run],
            id="corpus_refresh",
        )
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Daemon stopped.")
    else:
        run_refresh_cycle(api_key, args.dry_run)


if __name__ == "__main__":
    main()
