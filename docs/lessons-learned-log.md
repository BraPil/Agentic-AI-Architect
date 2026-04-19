# Lessons Learned Log

## Purpose

This file records mistakes, surprises, and durable lessons so the repository does not repeat avoidable confusion or wasted work.

## Lesson Ledger

| Date | Lesson | What Triggered It | Preventive Action |
|------|--------|-------------------|-------------------|
| 2026-03 | Chat history alone is not durable memory | Important decisions and rationale were at risk of remaining only in conversation context | Record accepted decisions and work outcomes in repo files and index them in `docs/work-index.md` |
| 2026-03 | A strong long-term ecosystem vision can still create short-term overdesign | Multi-system thinking repeatedly pulled planning away from a bounded first product | Keep current work centered on AI Architect MVP and require explicit entry criteria before opening the next specialist repo |
| 2026-03 | Review artifacts are useful, but they do not replace a compact operational ledger | Decisions were spread across review docs, memos, and conversation summaries | Maintain compact decision, discovery, lesson, and work logs alongside longer narrative documents |
| 2026-03 | For future sibling systems, separate fast spike work from ontology-forming research work | Architecture experiments and durable doctrine serve different purposes and should not be merged mentally or operationally too early | Use a spike branch to test shape and a research branch to codify validated patterns into AAA's durable ontology |
| 2026-03 | Static data-backed Next.js routes can serve stale cycle records if generated artifacts change after the last production build | The new ExMorbus cycle-history ledger was regenerated correctly, but `/cycles` still rendered old values until the frontend was rebuilt and restarted | After regenerating snapshot or cycle-history artifacts, rerun the frontend production build before treating browser validation as authoritative |
| 2026-04 | yt-dlp subtitle download fails silently when a comma-separated `--sub-lang` value is combined with `-f sb3`; the format selector parses the comma as part of the format string | All 20 YouTube transcript fetches returned no subtitle files until the bug was caught; the fix (`--sub-lang en` only, no comma) immediately resolved it | Always validate yt-dlp subtitle output with `ls tmpdir/*.json3 *.vtt` before trusting a silent success exit code |
| 2026-04 | Dedup checks that write to a persistent store on first ingest will silently skip re-enrichment unless the check is enrichment-aware | 92 LinkedIn posts were added text-only in the first pass, then permanently skipped by subsequent enrichment runs because `research_sources.json` already had their IDs | Design ingest dedup at field-level quality (e.g., skip only if `mentioned_tools` is non-empty), not just at ID presence |
| 2026-04 | A Chrome extension content script injected via popup requires `requireVersion` gating or the popup may run stale cached script from the prior session | Earlier extension versions sometimes executed against stale DOM state after a manifest or content-script update | Always increment `AAA_CONTENT_VERSION` in both `content.js` and `popup.js` on any scraping-logic change, and gate execution with a version check |
