# AAA Operational Runbooks

**Last Updated**: 2026-06-28

Quick reference guides for deploying, monitoring, and maintaining the Agentic AI Architect system in production.

---

## Table of Contents

1. [System Startup](#system-startup)
2. [Daily Operations](#daily-operations)
3. [Troubleshooting](#troubleshooting)
4. [Debugging](#debugging)
5. [Scaling](#scaling)
6. [Incident Recovery](#incident-recovery)
7. [Performance Tuning](#performance-tuning)

---

## System Startup

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export ANTHROPIC_API_KEY="sk-..."  # From Codespace secrets or .env
export HF_TOKEN="hf_..."            # For sentence-transformers (optional)

# 3. Start the MCP server (stdio for Claude Desktop)
python -m src.api.mcp_server

# Or HTTP/SSE transport for remote access
./scripts/run_mcp_server_sse.sh 8765
```

### MCP Server Registration (Claude Desktop)

**File**: `~/.config/Claude/claude_desktop_config.json` (macOS/Linux) or equivalent

```json
{
  "mcpServers": {
    "aaa": {
      "command": "python",
      "args": ["-m", "src.api.mcp_server"],
      "cwd": "/path/to/Agentic-AI-Architect"
    }
  }
}
```

Then reload Claude Desktop.

### REST API Startup

```bash
python3 -c "
from src.api.rest_v1 import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"

# Or:
uvicorn src.api.rest_v1:app --reload --port 8000
```

Health check: `curl http://localhost:8000/v1/health`

---

## Daily Operations

### Health Check

```bash
# 1. MCP server responsiveness
python3 -c "
from src.api.mcp_server import _get_store
store = _get_store()
print(f'ChromaDB items: {store._collection.count()}')
personas = store.get_personas()
print(f'Personas indexed: {len(personas)}')
"

# 2. REST API status
curl -s http://localhost:8000/v1/health | jq .

# 3. Check recent logs
tail -20 data/mcp_usage.jsonl
```

### Corpus Refresh

```bash
# Manual refresh (polls sources, ingests new content)
python3 scripts/refresh_corpus.py

# Daemon mode (runs every 6 hours)
python3 scripts/refresh_corpus.py --daemon

# With email notifications on trend alerts
python3 scripts/refresh_corpus.py --notify-webhooks
```

### Evaluation Run

```bash
# Run full eval suite (20 ground-truth questions)
python3 scripts/run_eval.py

# Single question
python3 scripts/run_eval.py --question eval-001

# With synthesis eval (requires API key)
python3 scripts/run_eval.py --synthesis

# Check persona coverage
python3 scripts/run_eval.py --coverage

# Save results to custom file
python3 scripts/run_eval.py --output data/eval_results_2026-06-28.json
```

### Wiki Maintenance

```bash
# Lint wiki for consistency
python3 scripts/lint_wiki.py

# Rebuild schema extracts
python3 scripts/build_wiki_schema.py

# Check for stale pages (>90 days)
python3 scripts/lint_wiki.py --stale-days 90
```

### Commit and Push

```bash
# After any manual work, commit changes
git status
git add data/wiki/ docs/ src/
git commit -m "chore(ops): daily maintenance — eval results, wiki lint"
git push origin main
```

---

## Troubleshooting

### "ChromaDB connection failed"

**Symptom**: `Error: No such file or directory: data/linkedin_store`

**Fix**:
```bash
# Restore from snapshot
python3 scripts/restore_chromadb_snapshot.py
```

**If no snapshot exists**:
```bash
# Re-ingest from sources
python3 scripts/refresh_corpus.py --full-reingest
```

---

### "ANTHROPIC_API_KEY not set"

**Symptom**: LLM synthesis fails; falls back to evidence-only

**Fix**:
```bash
# Set in Codespace secrets or .env
export ANTHROPIC_API_KEY="sk-..."

# Verify
echo $ANTHROPIC_API_KEY | head -10
```

---

### "Search returns no results"

**Symptom**: `search_knowledge` returns `{"results": [], "total_results": 0}`

**Possible causes**:

1. **Query too specific**: Try broader terms
2. **Embedding mismatch**: ChromaDB corrupted
3. **Persona not indexed**: Check `store.get_personas()` for persona_id

**Fix**:

```python
# Check what's indexed for a persona
from src.pipeline.linkedin_persona_store import LinkedInPersonaStore
store = LinkedInPersonaStore(store_path='data/linkedin_store')
store.initialize()

# Count items for persona
result = store._collection.get(
    where={"persona_id": "andrej-karpathy"},
    include=["metadatas"]
)
print(f"Found {len(result['ids'])} items for andrej-karpathy")

# Try a broad search
hits = store.search(query="AI", n_results=5)
print(f"Broad search returned {len(hits)} results")
```

---

### "MCP server crashes on startup"

**Fix**:

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check dependencies
pip list | grep -E "mcp|fastmcp|anthropic"

# Reinstall MCP dependencies
pip install --upgrade mcp fastmcp anthropic

# Try with verbose logging
python -m src.api.mcp_server --verbose
```

---

### "Webhook delivery failed"

**Symptom**: Alert events not reaching external system

**Check**:

```bash
# Review webhook log
tail -50 data/webhook_delivery.jsonl

# Check registered subscribers
curl -s http://localhost:8000/v1/webhooks/subscribers | jq .

# Test webhook manually
curl -X POST http://localhost:8000/v1/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"event": "tool_deprecated", "tool": "test"}'
```

---

## Debugging

### Enable Verbose Logging

```bash
export DEBUG=true
python -m src.api.mcp_server
```

### Inspect MCP Usage Log

```bash
# Recent 50 calls
tail -50 data/mcp_usage.jsonl | jq .

# Filter by tool
cat data/mcp_usage.jsonl | jq 'select(.tool == "search_knowledge")'

# Count calls per tool
cat data/mcp_usage.jsonl | jq -r '.tool' | sort | uniq -c
```

### Test LLM Synthesis Directly

```python
from src.api.mcp_server import _get_anthropic
from src.personas.synthesis import ask_persona_synthesis

client = _get_anthropic()
question = "What is agentic architecture?"

# Mock search results
hits = [
    {
        "document": "Agentic systems use autonomous loops for reasoning and action.",
        "metadata": {
            "post_type": "blog",
            "timestamp": "2026-06-01",
            "author": "Jane Researcher"
        }
    }
]

viewpoint = ask_persona_synthesis(
    persona_id="jane-researcher",
    display_name="Jane Researcher",
    question=question,
    hits=hits,
    client=client
)

print(viewpoint.to_dict())
```

### Check Database Integrity

```bash
# Validate ChromaDB
python3 -c "
import sqlite3
conn = sqlite3.connect('data/linkedin_store/chroma.sqlite3')
cursor = conn.cursor()

# Check table counts
for table in ['documents', 'embeddings', 'metadata']:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} rows')

conn.close()
"
```

---

## Performance Tuning

### MCP Query Latency

**Goal**: < 200 ms for cached queries

**Measurement**:

```bash
python3 scripts/benchmark_mcp.py
```

**Output**:
```
search_knowledge (warm): 45ms
search_knowledge (cold): 180ms
get_architecture_recommendation (warm): 120ms
get_trending_tools: 65ms
```

**If latency > 200ms**:

1. **Increase ChromaDB cache**: Allocate more memory to the host
2. **Use fewer_n_results**: Default is 8; reduce if not needed
3. **Profile with cProfile**:
   ```python
   import cProfile
   cProfile.run('store.search("query", n_results=8)', sort='cumtime')
   ```

### Vector Search Performance

**Optimize embedding model**:

```python
# Currently: all-MiniLM-L6-v2 (384-dim)
# For faster inference, switch to:
# - all-MiniLM-L6-v1 (faster, slightly lower accuracy)
# - Or offload to GPU if available
```

**Check embedding stats**:

```python
from src.pipeline.linkedin_persona_store import LinkedInPersonaStore
store = LinkedInPersonaStore()
store.initialize()

# Count embeddings
emb_count = store._collection.count()
print(f"Total embeddings: {emb_count}")

# Estimate memory usage (384-dim float32 = 1.5 KB per vector)
memory_kb = emb_count * 1.5
print(f"Approximate memory: {memory_kb / 1024 / 1024:.1f} MB")
```

---

## Incident Recovery

### MCP Server Hangs

**Symptom**: Queries timeout; no response

**Recovery**:

```bash
# 1. Kill the process
pkill -f "python -m src.api.mcp_server"

# 2. Check ChromaDB for corruption
python3 scripts/restore_chromadb_snapshot.py

# 3. Restart
python -m src.api.mcp_server
```

### Data Loss (ChromaDB corrupted)

**Recovery**:

```bash
# 1. Restore from git-committed snapshot
python3 scripts/restore_chromadb_snapshot.py

# 2. Or, re-ingest from raw sources
python3 scripts/refresh_corpus.py --full-reingest

# 3. Verify integrity
python3 scripts/run_eval.py  # Should pass 20/20
```

### Webhook Queue Overload

**Symptom**: Trend alerts backing up; memory growing

**Fix**:

```bash
# 1. Check queue depth
python3 -c "
import json
with open('data/webhook_queue.jsonl') as f:
    events = [json.loads(line) for line in f]
print(f'Queued events: {len(events)}')
"

# 2. Force delivery
python3 scripts/webhook_worker.py --drain

# 3. Archive old logs
mv data/webhook_delivery.jsonl data/webhook_delivery.archive_2026-06-28.jsonl
```

---

## Scaling Guidance

### From 1x to 10x

**At current state** (260 items, 56 personas):
- MCP latency: ~50ms (warm), ~180ms (cold)
- Memory: ~300 MB (ChromaDB + model)
- API throughput: ~100 req/sec on single instance

**For 10x corpus** (2,600 items, 560 personas):
- Switch to Postgres + pgvector: Better scaling than SQLite
- Offload embeddings to GPU or separate service
- Add caching layer (Redis or memcached)
- Use LLM routing to fast model (Haiku) for filtering

```bash
# Postgres setup
docker run -d --name pg-vector \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  pgvector/pgvector:latest

# Update config
export KNOWLEDGE_DB_URL="postgresql://user:password@localhost:5432/aaa"
```

### From 10x to 100x

- Distribute ChromaDB/Postgres across multiple nodes
- Use async ingestion (queue-based)
- Separate read and write instances
- Implement sharding by persona_id or topic
- Cache at CDN level for REST API

---

## Emergency Contacts & Escalation

| Issue | First Step | Escalate If |
|-------|-----------|------------|
| MCP server unresponsive | Kill & restart | Happens > 2x/hour |
| API latency spike | Check logs; profile | Sustained > 500ms |
| Data corruption | Restore from snapshot | Snapshot also corrupted |
| Webhook failures | Check subscriber endpoint | Network unreachable |

---

## Testing & Validation

### Pre-Deployment Checklist

```bash
# 1. Run full test suite
pytest tests/ -v

# 2. Run eval (must pass 20/20)
python3 scripts/run_eval.py
# Expected: 20/20 passing, avg relevance 0.46+

# 3. Check system health
python3 -c "
from src.api.mcp_server import _get_store
store = _get_store()
assert store._collection.count() > 250, 'Corpus too small'
personas = store.get_personas()
assert len(personas) > 50, 'Not enough personas'
print('✓ Health check passed')
"

# 4. Lint wiki
python3 scripts/lint_wiki.py
# Expected: no contradictions, <5 orphan warnings

# 5. Manual MCP test
python3 -c "
from src.api.mcp_server import mcp
# Smoke test: can server initialize?
print('✓ MCP server ready')
"

# 6. Git status clean
git status
# Expected: nothing to commit, working tree clean
```

---

*Runbooks maintained by: Agentic AI Architect devops*  
*Last tested: 2026-06-28*
