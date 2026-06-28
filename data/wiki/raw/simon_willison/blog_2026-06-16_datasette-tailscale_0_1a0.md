# datasette-tailscale 0.1a0
url: https://simonwillison.net/2026/Jun/16/datasette-tailscale/#atom-everything
author: Simon Willison
published_at: 2026-06-16
persona_id: simon_willison

---

Release: datasette-tailscale 0.1a0 A very experimental alpha plugin which lets you do this: datasette tailscale mydata.db \ --ts-authkey tskey-auth-xxxx --ts-hostname datasette-preview This starts a localhost Datasette server with a Tailscale sidecar that connects it to your Tailnet, such that http://datasette-preview/ serves Datasette. It's using the Python bindings for the experimental tailscale-rs library. I filed an issue asking if there's a cleaner way of setting up the proxy mechanism. Tags: datasette , tailscale
