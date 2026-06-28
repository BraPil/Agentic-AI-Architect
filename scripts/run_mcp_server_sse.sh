#!/usr/bin/env bash
# Launch the AAA MCP server with SSE (HTTP) transport for remote access.
#
# Usage:
#   ./scripts/run_mcp_server_sse.sh [PORT]
#
# Default port: 8765
# Binds to 0.0.0.0 — forward this port in your Codespace to expose it.

set -euo pipefail

PORT="${1:-8765}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Starting AAA MCP SSE server on 0.0.0.0:${PORT}" >&2
echo "SSE endpoint: http://0.0.0.0:${PORT}/sse" >&2

exec python3 -c "
import sys
sys.path.insert(0, '${REPO_ROOT}')
from src.api.mcp_server import mcp
mcp.settings.host = '0.0.0.0'
mcp.settings.port = ${PORT}
mcp.run(transport='sse')
"
