# asgi-gzip 0.3
url: https://simonwillison.net/2026/Apr/9/asgi-gzip/#atom-everything
author: Simon Willison
published_at: 2026-04-09
persona_id: simon_willison

---

Release: asgi-gzip 0.3 I ran into trouble deploying a new feature using SSE to a production Datasette instance, and it turned out that instance was using datasette-gzip which uses asgi-gzip which was incorrectly compressing event/text-stream responses. asgi-gzip was extracted from Starlette, and has a GitHub Actions scheduled workflow to check Starlette for updates that need to be ported to the library... but that action had stopped running and hence had missed Starlette's own fix for this issue. I ran the workflow and integrated the new fix, and now datasette-gzip and asgi-gzip both correctly handle text/event-stream in SSE responses. Tags: gzip , asgi , python
