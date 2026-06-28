#!/usr/bin/env python3
"""
Run one end-to-end AAA learning cycle.

This is the operational entry point for the regulated learning loop. It honors the
AAA ↔ OAA boundary:

    AAA  → seed + ground   (build a seed spec, attach corpus evidence)
    OAA  → run (subprocess) (the MoltBook cycle produces KnowledgeRecordV0 artifacts)
    AAA  → harvest          (artifacts land in the quarantined `experimental` tier)

Promotion of any harvested artifact remains a separate, human-gated step
(scripts/promote_learnings.py or the MCP tools).

Usage:
  python3 scripts/run_learning_cycle.py \
      --question "When should an AI architecture use a curated markdown index over a vector DB?" \
      --oaa-path ../Organic_Agentic_AutoDev

Grounding only ever draws from trusted tiers (external / internal / grounded) — never
from unpromoted experimental artifacts, so the loop cannot feed on its own output.
"""

import argparse
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("run_learning_cycle")

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

_TRUSTED_TIERS = {"external", "internal", "grounded", None, ""}


def _build_grounding(question: str, top_k: int) -> str:
    """Retrieve trusted-tier evidence snippets from AAA's corpus for grounding."""
    from src.pipeline.linkedin_persona_store import LinkedInPersonaStore  # noqa: PLC0415
    store = LinkedInPersonaStore()
    store.initialize()
    hits = store.search(query=question, n_results=top_k + 10)
    lines: list[str] = []
    for h in hits:
        meta = h.get("metadata", {})
        if meta.get("source_tier") not in _TRUSTED_TIERS:
            continue  # never ground on experimental (unpromoted) artifacts
        author = meta.get("author", meta.get("persona_id", "unknown"))
        snippet = h.get("document", "")[:400].replace("\n", " ")
        lines.append(f"- ({author}) {snippet}")
        if len(lines) >= top_k:
            break
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one AAA learning cycle (seed → OAA → harvest)")
    parser.add_argument("--question", required=True, help="Architecture question for the cycle")
    parser.add_argument("--oaa-path", default="",
                        help="Optional: run from an OAA checkout instead of the installed "
                             "package (dev override). Default: use the pip-installed "
                             "organic_agentic_autodev package.")
    parser.add_argument("--personas", default="", help="Comma-separated persona ids (default: core set)")
    parser.add_argument("--top-k", type=int, default=8, help="Grounding snippets to retrieve")
    # Default to Sonnet: learning artifacts get promoted into the permanent corpus,
    # so artifact quality matters more than per-run cost. Override with --model for
    # cheap dry runs (haiku) or maximum quality (opus).
    parser.add_argument("--model", default="claude-sonnet-4-6", help="LLM model for cognition")
    parser.add_argument("--no-harvest", action="store_true", help="Run the cycle but skip harvesting")
    args = parser.parse_args()

    from src.learning.seeder import build_seed_spec  # noqa: PLC0415

    persona_ids = [p.strip() for p in args.personas.split(",") if p.strip()] or None
    spec = build_seed_spec(args.question, persona_ids=persona_ids)

    logger.info("Retrieving grounding evidence from AAA corpus (trusted tiers only)…")
    spec["grounding"] = _build_grounding(args.question, args.top_k)
    logger.info("Grounding: %d chars", len(spec["grounding"]))

    work = Path(tempfile.mkdtemp(prefix="aaa_cycle_"))
    seed_path = work / "seed.json"
    artifacts_path = work / "artifacts.jsonl"
    seed_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

    # OAA runs as its own process (process isolation). Default: the pip-installed
    # organic_agentic_autodev package. Optional --oaa-path runs from a dev checkout.
    module = "organic_agentic_autodev.cognition.run_cycle"
    cwd: str | None = None
    if args.oaa_path:
        oaa = Path(args.oaa_path).resolve()
        if not (oaa / "organic_agentic_autodev" / "cognition" / "run_cycle.py").exists():
            logger.error("OAA cognition runner not found at %s", oaa)
            sys.exit(1)
        cwd = str(oaa)
    else:
        try:
            import organic_agentic_autodev  # noqa: F401, PLC0415
        except ImportError:
            logger.error("organic_agentic_autodev is not installed. Either "
                         "`pip install git+https://github.com/BraPil/Organic_Agentic_AutoDev.git` "
                         "or pass --oaa-path to a checkout.")
            sys.exit(1)

    logger.info("Running OAA cycle (subprocess, process-isolated)…")
    proc = subprocess.run(
        [sys.executable, "-m", module,
         "--seed", str(seed_path), "--out", str(artifacts_path), "--model", args.model],
        cwd=cwd, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        logger.error("OAA cycle failed:\n%s", proc.stderr[-2000:])
        sys.exit(1)
    logger.info("OAA cycle output:\n%s", proc.stdout.strip())

    if args.no_harvest:
        logger.info("Artifacts at %s (harvest skipped)", artifacts_path)
        return

    from src.learning.harvester import HarvestPipeline  # noqa: PLC0415
    from src.pipeline.linkedin_persona_store import LinkedInPersonaStore  # noqa: PLC0415
    store = LinkedInPersonaStore()
    store.initialize()
    result = HarvestPipeline(store._collection).run(artifacts_path)
    logger.info("Harvest: %d added, %d updated, %d failed (tier=experimental, quarantined)",
                result.added, result.skipped, result.failed)
    logger.info("Review with: python3 scripts/promote_learnings.py --list")


if __name__ == "__main__":
    main()
