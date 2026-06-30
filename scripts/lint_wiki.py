#!/usr/bin/env python3
"""
Lint the AAA knowledge wiki for consistency.

Checks (errors fail the run with a non-zero exit; warnings do not):
  - broken internal links   [ERROR]  a `(pages/foo.md)` or `[[foo]]` target that doesn't exist
  - orphan pages            [WARN]   a `pages/*.md` not referenced from index.md or any page
  - count drift             [ERROR]  index.md's "Total items" / "Personas (N Indexed)" claims
                                     disagree with the store-derived persona_catalog.json

Usage:
  python3 scripts/lint_wiki.py
  python3 scripts/lint_wiki.py --strict   # treat warnings as errors too
"""

import argparse
import json
import re
import sys
from pathlib import Path

WIKI_DIR = Path("data/wiki")
INDEX = WIKI_DIR / "index.md"
PAGES_DIR = WIKI_DIR / "pages"
CATALOG = WIKI_DIR / "schema" / "persona_catalog.json"

# (text)(path) markdown links pointing into pages/, and [[wikilinks]].
_MD_LINK = re.compile(r"\]\((pages/[\w./-]+\.md)\)")
_WIKILINK = re.compile(r"\[\[([\w-]+)\]\]")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_links(errors: list[str]) -> None:
    sources = [INDEX, *sorted(PAGES_DIR.glob("*.md"))]
    for src in sources:
        text = _read(src)
        for rel in _MD_LINK.findall(text):
            if not (WIKI_DIR / rel).exists():
                errors.append(f"broken link in {src.name}: {rel} → missing")
        for slug in _WIKILINK.findall(text):
            if not (PAGES_DIR / f"{slug}.md").exists():
                errors.append(f"broken wikilink in {src.name}: [[{slug}]] → no pages/{slug}.md")


def check_orphans(warnings: list[str]) -> None:
    referenced: set[str] = set()
    for src in [INDEX, *sorted(PAGES_DIR.glob("*.md"))]:
        text = _read(src)
        referenced.update(Path(r).name for r in _MD_LINK.findall(text))
        referenced.update(f"{s}.md" for s in _WIKILINK.findall(text))
    for page in sorted(PAGES_DIR.glob("*.md")):
        if page.name not in referenced:
            warnings.append(f"orphan page (no inbound link): pages/{page.name}")


def check_counts(errors: list[str], warnings: list[str]) -> None:
    if not CATALOG.exists():
        warnings.append("persona_catalog.json missing — run scripts/build_wiki_schema.py "
                        "(skipping count checks)")
        return
    catalog = json.loads(CATALOG.read_text())
    text = _read(INDEX)

    m = re.search(r"\*\*Total items\*\*:\s*([\d,]+)", text)
    if m:
        claimed = int(m.group(1).replace(",", ""))
        actual = catalog["total_posts"]
        if claimed != actual:
            errors.append(f"index.md 'Total items' = {claimed} but store has {actual} posts")

    m = re.search(r"##\s*Personas\s*\((\d+)\s*Indexed\)", text)
    if m:
        claimed = int(m.group(1))
        actual = catalog["total_personas"]
        if claimed != actual:
            errors.append(f"index.md 'Personas ({claimed} Indexed)' but store has "
                          f"{actual} personas")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lint the AAA knowledge wiki")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    if not INDEX.exists():
        print(f"ERROR: {INDEX} not found")
        sys.exit(2)

    errors: list[str] = []
    warnings: list[str] = []
    check_links(errors)
    check_orphans(warnings)
    check_counts(errors, warnings)

    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [ERROR] {e}")

    n_pages = len(list(PAGES_DIR.glob("*.md")))
    print(f"\nLinted {n_pages} pages — {len(errors)} error(s), {len(warnings)} warning(s).")

    fail = bool(errors) or (args.strict and bool(warnings))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
