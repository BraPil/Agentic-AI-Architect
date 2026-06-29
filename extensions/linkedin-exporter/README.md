# AAA LinkedIn Exporter — Chrome Extension

Exports LinkedIn posts (text + images, with **absolute timestamps**) from your reactions page, feed, or any profile's recent-activity page, then feeds them into the AAA knowledge pipeline. **v1.1 adds batch mode** to walk many profiles in one run.

> **What automation is possible:** This runs in *your* logged-in browser, so it works with LinkedIn auth. Fully headless/server-side scraping is **not** viable — LinkedIn auth-walls anonymous access, blocks datacenter IPs, and bans automated scraping. Batch mode is the safe middle ground: one click, your session, all profiles. Keep the pace polite (delays are built in); aggressive scraping risks your account.

## Install

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked** → select this folder (`extensions/linkedin-exporter/`)
4. The extension icon appears in the toolbar

## Use

1. Navigate to any LinkedIn page you want to export, e.g.:
   - Your reactions: `https://www.linkedin.com/in/brandtpileggi/recent-activity/reactions/`
   - Your posts: `https://www.linkedin.com/in/brandtpileggi/recent-activity/posts/`
   - Any profile feed, company page, or search results
2. Click the extension icon
3. Choose your action:
   - **Scroll + Scrape all** — auto-scrolls to load all posts, then scrapes (recommended)
   - **Scroll** alone — just loads more posts into the page without scraping
   - **Scrape visible posts** — scrapes whatever is currently on screen

4. After scraping, click **Download JSON**
   - File saves to your Downloads folder as `linkedin_export_<page>_<timestamp>.json`

### Batch mode (walk many profiles)

For multiple people, use the **Batch mode** box:
1. Paste one handle or profile URL per line (e.g. `alliekmiller`, `brennhill`, `https://www.linkedin.com/in/ownyourai/`).
2. Set **Max age months** (e.g. `2` for the last 2 months) and the other options above.
3. Click **▶ Run batch**. The extension navigates the active tab through each person's
   `/recent-activity/all/`, scrolls, scrapes, and downloads one JSON per profile.
4. Stay logged in and keep the tab focused while it runs.

Then ingest each downloaded file with `process_linkedin_export.py` (or loop over them).

## Process the export in AAA

```bash
# Full pipeline: text extraction + Claude Vision for images
ANTHROPIC_API_KEY=sk-... python3 scripts/process_linkedin_export.py \
  --export ~/Downloads/linkedin_export_reactions_2026-04-18.json \
  --persona brandtpileggi

# Text only (no API key needed)
python3 scripts/process_linkedin_export.py \
  --export ~/Downloads/linkedin_export_reactions_2026-04-18.json \
  --persona brandtpileggi --no-vision

# Dry run to preview
ANTHROPIC_API_KEY=sk-... python3 scripts/process_linkedin_export.py \
  --export ~/Downloads/linkedin_export_reactions_2026-04-18.json \
  --persona brandtpileggi --dry-run --limit 5
```

## What gets exported

Each post in the JSON contains:
- `post_url` — direct link to the post
- `author` + `author_url` — who wrote it
- `text` — full text (with "Read more" expanded automatically)
- `images` — array of `{ src, alt, width, height }` for all images in the post
- `post_type` — `text | image | video | article | document`
- `external_links` — any non-LinkedIn URLs referenced in the post
- `timestamp` — relative timestamp from LinkedIn UI (e.g. "2mo")
- `published_at` — **absolute ISO 8601 timestamp**, decoded from the activity URN
  (LinkedIn IDs are snowflake-encoded: `id >> 22` = creation time in ms). Drift-proof,
  and what enables real date filtering / "last N months" cutoffs.
- `published_ms` — the same as epoch milliseconds

## Notes

- Images are **URLs only** in the export (not downloaded). The `process_linkedin_export.py` script downloads and analyzes them via Claude Vision.
- LinkedIn DOM classes change periodically. If scraping produces zero posts, open an issue — the selectors in `content.js` may need updating.
- The extension only runs when you're on `linkedin.com`. It cannot access other sites.
