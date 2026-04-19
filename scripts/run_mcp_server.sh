#!/usr/bin/env bash
# Launch the AAA MCP server (stdio transport — for Claude Desktop / MCP clients).
#
# Usage:
#   ./scripts/run_mcp_server.sh
#   ANTHROPIC_API_KEY=sk-ant-... ./scripts/run_mcp_server.sh
#
# Without ANTHROPIC_API_KEY: search_knowledge and get_trending_tools work fully;
# get_architecture_recommendation returns raw retrieval results without LLM synthesis.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

exec python3 -m src.api.mcp_server "$@"
