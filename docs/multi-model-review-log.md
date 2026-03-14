# Multi-Model Review Log
## Tracking Independent AI Architecture Reviews

> **Purpose**: Keep a dated record of every independent AI architecture review session so decisions can be traced back to the review that informed them.

---

## How to Conduct a Review Session

1. Open `docs/ai-review-context-prompt.md`
2. Copy everything between `---BEGIN PROMPT---` and `---END PROMPT---`
3. Paste it as the opening message to your chosen model
4. Let the model respond fully before asking follow-up questions
5. Save the conversation locally (e.g. `<model>_<date>_review.md`)
6. Add a row to the table below
7. Reconcile any architectural decisions with `CLAUDE.md §12` (Key Decisions Log)

---

## Review Session Log

| Date | Model | Session File | Key Takeaways | Decisions Made |
|------|-------|-------------|---------------|----------------|
| 2026-03 | ChatGPT 4.5 | `Agentics_Ideation_Sesh_ChatGPT45.md` (local) | See user's local notes | TBD — see `docs/chatgpt45-ideation-review.md` for GitHub Copilot's response |
| 2026-03 | GitHub Copilot | `docs/chatgpt45-ideation-review.md` | LangGraph migration is biggest risk; move API contract earlier; pgvector over Pinecone; v0.1 = crawl 5 sources + GET /query | Pending |
| 2026-03 | GitHub Copilot (synthesis) | `docs/exmorbus-v3-integration.md` | ExMorbus V3 is MoltBook-for-medicine; Agentic-AI-Architect serves as on-demand architectural oracle; MCP server must support load/unload under 200ms; add `get_architecture_recommendation` tool; Phase 5 ExMorbus adapter is a new deliverable | See Decision Record below |

---

## Pending Decisions (from current review round)

These questions were raised in the 2026-03 review round and have not yet been resolved:

- [ ] **Agent framework**: Stay custom `BaseAgent` → LangGraph migration at Phase 4, OR start LangGraph now, OR stay custom forever?
- [ ] **Vector store production target**: PostgreSQL + pgvector, or PostgreSQL + Pinecone?
- [ ] **API timing**: Move minimal `GET /query` endpoint to Phase 2, or keep at Phase 5? (Note: ExMorbus integration needs lean toward moving earlier)
- [ ] **Config layer**: Migrate from `@dataclass` to `pydantic-settings`?
- [ ] **MCP contract**: Define stub interface in Phase 1 alongside `BaseAgent`? (Note: ExMorbus integration strongly favors defining the stub now — see `docs/exmorbus-v3-integration.md §4.1`)
- [ ] **ExMorbus MCP stub timing**: Create `src/api/mcp_server.py` type stubs now (Phase 1) or defer to Phase 5?

---

## Decision Record

| Decision | Chosen Option | Rationale | Date | Review Round |
|----------|--------------|-----------|------|-------------|
| Repository structure | Keep `Agentic-AI-Architect` as its own product repo; defer ecosystem-level repo split until at least a second real system exists | Preserves focus for Phase 1 while still designing explicit seams for later multi-repo interoperability | 2026-03 | 2026-03 |
| ExMorbus integration model | Oracle model (read-only, on-demand, advisory) — not embedded, not resident | ExMorbus must continue operating if Agentic-AI-Architect is unavailable; advisory-only prevents coupling | 2026-03 | 2026-03 |
| MCP tool latency target | < 200ms for cached queries | ExMorbus uses on-demand load/unload; slow responses defeat the token-efficiency purpose | 2026-03 | 2026-03 |
| API schema versioning | All responses include `schema_version`; breaking changes require new major version + 90-day deprecation | ExMorbus cannot afford mid-project API breaks from its architectural advisor | 2026-03 | 2026-03 |
| Additional MCP tool | Add `get_architecture_recommendation` to P5.3 MCP server | ExMorbus's primary use case is targeted architectural guidance, not just knowledge retrieval | 2026-03 | 2026-03 |
| Webhook delivery | Add outbound webhook support to P5.4 for proactive architecture alerts | ExMorbus should not poll; architecture shifts in medical AI may have compliance implications | 2026-03 | 2026-03 |

---

*Last updated: March 2026*
