---
wiki_id: repo_second_brain_starter
type: repo_page
persona: cole_medin
repo: coleam00/second-brain-starter
foundational: true
raw_source: data/wiki/raw/cole_medin/github_coleam00_second-brain-starter_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - P6.4 — knowledge distillation and memory persistence pattern
  - Persona Analog System — memory architecture for simulating influential voices
  - Claude Code skills — .claude/skills/ pattern applicable to AAA tooling
---

# coleam00/second-brain-starter

## What It Is

A Claude Code skill that generates a personalized PRD (Product Requirements Document) for building an AI second brain. You fill out a requirements template; Claude Code generates a phased build plan for a persistent, proactive AI assistant.

The generated second brain:
- **Remembers** across sessions in markdown files
- **Connects** to Gmail, Slack, Calendar, Asana, Linear, GitHub, etc.
- **Proactively monitors** email/calendar/tasks every 30 minutes
- **Searches** months of memory with hybrid keyword + semantic search
- **Drafts** in the user's voice using RAG on past messages

## Architecture Patterns

### SOUL.md / USER.md / MEMORY.md persistence
The repo follows the pattern of markdown-file memory. Key files:
- `SOUL.md` — persistent values, personality, communication style
- `USER.md` — facts about the user (role, tools, preferences)
- `MEMORY.md` — episodic memory index (decisions, events, context)

This is the same memory pattern now implemented in AAA's `/home/codespace/.claude/projects/` memory system.

### Proactive heartbeat
The agent monitors external systems on a 30-minute cron, synthesizes signals, and surfaces them proactively. This is the Phase 4.2 APScheduler pattern applied to personal AI.

### .claude/skills/ pattern
The skill is distributed as a `.claude/skills/create-second-brain-prd/` directory. This is how Claude Code skills compose — they're just structured markdown instruction files in a known location. This pattern is directly applicable to AAA's P5 MCP tool delivery.

## Why It Matters for AAA

1. **Persona Analog Memory**: The SOUL.md/USER.md/MEMORY.md triplet is the right architecture for persona analog memory in AAA. Each persona (Karpathy, Cole Medin, etc.) could have a SOUL.md capturing their communication style and values, a USER.md capturing their background, and a MEMORY.md indexing their key positions.

2. **Phase 6 knowledge distillation**: The hybrid keyword + semantic search over markdown memory files is exactly what P6.4 requires — a structured, queryable memory surface that doesn't require FAISS at personal scale.

3. **Proactive monitoring → Phase 4.2**: The 30-minute heartbeat pattern validates the APScheduler-based recurring cycle design.
