# simonw/browser-compat-db
url: https://simonwillison.net/2026/Jun/24/browser-compat-db/#atom-everything
author: Simon Willison
published_at: 2026-06-24
persona_id: simon_willison

---

simonw/browser-compat-db Inspired by Mozilla's new MDN MCP service - source code here - I decided to try converting their comprehensive mdn/browser-compat-data repository full of browser compatibility data into a SQLite database. This new GitHub repo includes a Claude Code for web (Opus 4.8) generated script for doing that using sqlite-utils . I wanted the resulting ~66MB SQLite database to be available via the GitHub CDN with open CORS headers. GitHub releases don't have those, but any file stored in a regular GitHub repository does - so I had Codex Desktop (GPT-5.5) build a GitHub Actions workflow that builds the database and then force-pushes it to a db "orphan" branch. You can download the resulting database from here , and since it's hosted with open CORS headers you can also explore it with Datasette Lite . Tags: github , mozilla , projects , github-actions , datasette-lite , ai-assisted-programming , model-context-protocol , mdn
