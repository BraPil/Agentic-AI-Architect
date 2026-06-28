# datasette PR #2689: Replace token-based CSRF with Sec-Fetch-Site header protection
url: https://simonwillison.net/2026/Apr/14/replace-token-based-csrf/#atom-everything
author: Simon Willison
published_at: 2026-04-14
persona_id: simon_willison

---

datasette PR #2689: Replace token-based CSRF with Sec-Fetch-Site header protection Datasette has long protected against CSRF attacks using CSRF tokens, implemented using my asgi-csrf Python library. These are something of a pain to work with - you need to scatter forms in templates with <input type="hidden" name="csrftoken" value="{{ csrftoken() }}"> lines and then selectively disable CSRF protection for APIs that are intended to be called from outside the browser. I've been following Filippo Valsorda's research here with interest, described in this detailed essay from August 2025 and shipped as part of Go 1.25 that same month. I've now landed the same change in Datasette. Here's the PR description - Claude Code did much of the work (across 10 commits, closely guided by me and cross-reviewed by GPT-5.4) but I've decided to start writing these PR descriptions by hand, partly to make them more concise and also as an exercise in keeping myself honest. New CSRF protection middleware inspired by Go 1.25 and this research by Filippo Valsorda. This replaces the old CSRF token based protection. Removes all instances of <input type="hidden" name="csrftoken" value="{{ csrftoken() }}"> in the templates - they are no longer needed. Removes the def skip_csrf(datasette, scope): plugin hook defined in datasette/hookspecs.py and its documentation and tests. Updated CSRF protection documentation to describe the new approach. Upgrade guide now describes the CSRF change . Tags: csrf , security , datasette , ai-assisted-programming
