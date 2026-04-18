# AAA LinkedIn Exporter — Chrome Extension

Exports LinkedIn posts (text + images) from your reactions page, feed, or any LinkedIn profile page, then feeds them into the AAA knowledge pipeline.

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
- `timestamp` — relative timestamp from LinkedIn UI

## Notes

- Images are **URLs only** in the export (not downloaded). The `process_linkedin_export.py` script downloads and analyzes them via Claude Vision.
- LinkedIn DOM classes change periodically. If scraping produces zero posts, open an issue — the selectors in `content.js` may need updating.
- The extension only runs when you're on `linkedin.com`. It cannot access other sites.
