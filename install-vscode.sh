#!/usr/bin/env bash
# ==============================================================================
# install-vscode.sh - Configure get-immediate-context for VS Code, Cline & Roo
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE_DIR="${SCRIPT_DIR}/.agents/skills/get-immediate-context"

echo "=========================================================="
echo "🚀 Installing get-immediate-context for VS Code, Cline & Roo Code"
echo "=========================================================="

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v py &> /dev/null; then
        PYTHON_CMD="py -3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    elif [ -f "/c/Python314/python.exe" ]; then
        PYTHON_CMD="/c/Python314/python.exe"
    fi
fi

# 1. Create .clinerules (for Cline and Roo Code agents)
echo "📝 Creating .clinerules..."
cat << 'EOF' > "${SCRIPT_DIR}/.clinerules"
# get-immediate-context Cline & Roo Code Agent Rules

Before editing or generating code:
1. Always read CONTEXT_BRIEF.md at the workspace root.
2. Confirm the brief is fresh against git HEAD. If not, run:
   python .agents/skills/get-immediate-context/scripts/fetch_context.py
3. Respect all domain invariants listed under Section 6 ([INV-xxx]).
4. Find exact file line ranges using Section 9 or run:
   python .agents/skills/get-immediate-context/scripts/symbol_indexer.py --locate <symbol>
5. Check ripple effect and blast radius before refactoring:
   python .agents/skills/get-immediate-context/scripts/call_graph.py --impact <filename>
6. Never expose secrets. Wrap private notes in <private>...</private> tags.
EOF

# 2. Setup .vscode settings & tasks
mkdir -p "${SCRIPT_DIR}/.vscode"

cat << 'EOF' > "${SCRIPT_DIR}/.vscode/tasks.json"
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Refresh Immediate Context",
      "type": "shell",
      "command": "python .agents/skills/get-immediate-context/scripts/fetch_context.py --force && python .agents/skills/get-immediate-context/scripts/symbol_indexer.py",
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent"
      }
    },
    {
      "label": "Check Invariant Impact",
      "type": "shell",
      "command": "python .agents/skills/get-immediate-context/scripts/diff_impact.py",
      "problemMatcher": []
    }
  ]
}
EOF

# 3. Generate initial brief & embeddings
echo "⚡ Generating initial orientation brief & code embeddings..."
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/fetch_context.py" --force
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/symbol_indexer.py"
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/code_embeddings.py" --generate

echo ""
echo "=========================================================="
echo "🎉 VS Code / Cline / Roo Code Setup Complete!"
echo "=========================================================="
echo "Configured:"
echo "  1. .clinerules (Agent system instructions)"
echo "  2. .vscode/tasks.json (Context refresh & Invariant Guardian tasks)"
echo "  3. CONTEXT_BRIEF.md (Verified OKF brief)"
echo "=========================================================="
