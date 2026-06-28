# datasette.io news preview
url: https://simonwillison.net/2026/Apr/16/datasette-io-preview/#atom-everything
author: Simon Willison
published_at: 2026-04-16
persona_id: simon_willison

---

Tool: datasette.io news preview The datasette.io website has a news section built from this news.yaml file in the underlying GitHub repository. The YAML format looks like this: - date: 2026-04-15 body: |- [Datasette 1.0a27](https://docs.datasette.io/en/latest/changelog.html#a27-2026-04-15) changes how CSRF protection works in a way that simplifies form and API integration, and introduces a new `RenameTableEvent` for when a table is renamed by a SQL query.
- date: 2026-03-18 body: |- ... This format is a little hard to edit, so I finally had Claude build a custom preview UI to make checking for errors have slightly less friction. I built it using standard claude.ai and Claude Artifacts, taking advantage of Claude's ability to clone GitHub repos and look at their content as part of a regular chat: Clone https://github.com/simonw/datasette.io and look at the news.yaml file and how it is rendered on the homepage. Build an artifact I can paste that YAML into which previews what it will look like, and highlights any markdown errors or YAML errors Tags: vibe-coding , claude , tools , datasette
