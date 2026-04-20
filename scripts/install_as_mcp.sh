#!/usr/bin/env bash
# Run this script in any GitHub Codespace to install AAA as a local MCP server.
#
# Usage (from the target codespace terminal):
#   curl -fsSL https://raw.githubusercontent.com/BraPil/Agentic-AI-Architect/main/scripts/install_as_mcp.sh | bash
#
# What it does:
#   1. Clones Agentic-AI-Architect into /workspaces/Agentic-AI-Architect
#   2. Installs Python dependencies
#   3. Writes .vscode/mcp.json with the AAA server entry
#   4. Prints next steps

set -euo pipefail

AAA_DIR="/workspaces/Agentic-AI-Architect"
REPO_URL="https://github.com/BraPil/Agentic-AI-Architect.git"
TARGET_MCP_JSON="${PWD}/.vscode/mcp.json"

echo "=== AAA MCP installer ==="
echo "Target workspace: ${PWD}"
echo "AAA will be cloned to: ${AAA_DIR}"
echo ""

# ── 1. Clone AAA ─────────────────────────────────────────────────────────────
if [ -d "${AAA_DIR}/.git" ]; then
    echo "[1/3] AAA already cloned — pulling latest..."
    git -C "${AAA_DIR}" pull --ff-only
else
    echo "[1/3] Cloning Agentic-AI-Architect..."
    git clone "${REPO_URL}" "${AAA_DIR}"
fi

# ── 2. Install Python deps ────────────────────────────────────────────────────
echo ""
echo "[2/3] Installing AAA Python dependencies..."
pip install -q -r "${AAA_DIR}/requirements.txt"
echo "      Done."

# ── 3. Write / merge .vscode/mcp.json ────────────────────────────────────────
echo ""
echo "[3/3] Configuring .vscode/mcp.json..."
mkdir -p "${PWD}/.vscode"

AAA_ENTRY=$(cat <<'JSONBLOCK'
    "aaa": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "src.api.mcp_server"],
      "cwd": "/workspaces/Agentic-AI-Architect",
      "env": {
        "ANTHROPIC_API_KEY": "${input:aaa_anthropic_key}"
      }
    }
JSONBLOCK
)

AAA_INPUT=$(cat <<'JSONBLOCK'
    {
      "id": "aaa_anthropic_key",
      "type": "promptString",
      "description": "Anthropic API key for AAA synthesis tools",
      "password": true
    }
JSONBLOCK
)

if [ ! -f "${TARGET_MCP_JSON}" ]; then
    # Create fresh file
    cat > "${TARGET_MCP_JSON}" <<EOF
{
  "servers": {
${AAA_ENTRY}
  },
  "inputs": [
${AAA_INPUT}
  ]
}
EOF
    echo "      Created ${TARGET_MCP_JSON}"
else
    echo ""
    echo "      ⚠️  .vscode/mcp.json already exists — add the AAA entry manually."
    echo "      See the snippet printed below."
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  AAA MCP setup complete."
echo ""
echo "  Next steps:"
echo "  1. Reload VSCode window (Ctrl+Shift+P → 'Reload Window')"
echo "     OR restart Claude Code — the MCP server will appear."
echo ""
echo "  2. First tool call will take ~20 seconds (embedding model"
echo "     cold start). Subsequent calls: <50ms."
echo ""
echo "  3. 6 tools available:"
echo "     search_knowledge        get_architecture_recommendation"
echo "     get_trending_tools      ask_persona"
echo "     compare_personas        get_consensus"
echo ""
echo "  4. Set ANTHROPIC_API_KEY as a Codespace secret at:"
echo "     github.com/settings/codespaces"
echo "     (so Claude synthesis tools work without prompting)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Manual .vscode/mcp.json snippet (if you need to merge manually):"
echo ""
echo '  "aaa": {'
echo '    "type": "stdio",'
echo '    "command": "python",'
echo '    "args": ["-m", "src.api.mcp_server"],'
echo '    "cwd": "/workspaces/Agentic-AI-Architect",'
echo '    "env": { "ANTHROPIC_API_KEY": "${input:aaa_anthropic_key}" }'
echo '  }'
