# datasette-apps 0.1a3
url: https://simonwillison.net/2026/Jun/15/datasette-apps-2/#atom-everything
author: Simon Willison
published_at: 2026-06-15
persona_id: simon_willison

---

Release: datasette-apps 0.1a3 Fixed a bug where users without the create-app permission could still create apps. #27 Fixed a bug where it was impossible to grant permission to edit an app to users who were not the app's owner. The rules for edit/delete are now the same as view: if the app is private only the owner can modify it, otherwise permission is controlled by Datasette's regular permission system. #29 Tags: datasette
