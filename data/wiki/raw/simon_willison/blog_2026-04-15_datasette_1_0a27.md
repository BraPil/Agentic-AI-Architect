# datasette 1.0a27
url: https://simonwillison.net/2026/Apr/15/datasette/#atom-everything
author: Simon Willison
published_at: 2026-04-15
persona_id: simon_willison

---

Release: datasette 1.0a27 Two major changes in this new Datasette alpha. I covered the first of those in detail yesterday - Datasette no longer uses Django-style CSRF form tokens, instead using modern browser headers as described by Filippo Valsorda . The second big change is that Datasette now fires a new RenameTableEvent any time a table is renamed during a SQLite transaction. This is useful because some plugins (like datasette-comments ) attach additional data to table records by name, so a renamed table requires them to react in appropriate ways. Here are the rest of the changes in the alpha: New actor= parameter for datasette.client methods, allowing internal requests to be made as a specific actor. This is particularly useful for writing automated tests. ( #2688 ) New Database(is_temp_disk=True) option, used internally for the internal database. This helps resolve intermittent database locked errors caused by the internal database being in-memory as opposed to on-disk. ( #2683 ) ( #2684 ) The /<database>/<table>/-/upsert API ( docs ) now rejects rows with null primary key values. ( #1936 ) Improved example in the API explorer for the /-/upsert endpoint ( docs ). ( #1936 ) The /<database>.json endpoint now includes an "ok": true key, for consistency with other JSON API responses. call_with_supported_arguments() is now documented as a supported public API. ( #2678 ) Tags: annotated-release-notes , datasette , python
