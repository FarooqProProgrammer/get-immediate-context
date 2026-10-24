#!/usr/bin/env bash
# ==============================================================================
# install-claude.sh - Configure get-immediate-context for Claude Code & Desktop
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE_DIR="${SCRIPT_DIR}/.agents/skills/get-immediate-context"

echo "=========================================================="
echo "🚀 Installing get-immediate-context for Claude Code"
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

# 1. Create root CLAUDE.md
echo "📝 Creating root CLAUDE.md for Claude Code CLI..."
cat << 'EOF' > "${SCRIPT_DIR}/CLAUDE.md"
# Claude Code Project Guidelines: get-immediate-context

## Immediate Codebase Orientation
- Always inspect `CONTEXT_BRIEF.md` at the repository root before answering or implementing tasks.
- Verify `git_commit` in the header matches current HEAD. If stale, run:
  `python .agents/skills/get-immediate-context/scripts/fetch_context.py`
- Check Section 6 for confirmed domain invariants (`[INV-xxx]`). Never violate them without explicit user consent.
- Check Section 9 for exact symbol locations (`Lxx-Lyy`) rather than reading large files in full.

## Helper Tools & Skills
- **Locate symbols/functions**: `python .agents/skills/get-immediate-context/scripts/symbol_indexer.py --locate <name>`
- **Semantic code search**: `python .agents/skills/get-immediate-context/scripts/code_embeddings.py --search "<intent>"`
- **Hybrid search (BM25 + Vector)**: `python .agents/skills/get-immediate-context/scripts/hybrid_search.py "<query>"`
- **Blast radius impact analysis**: `python .agents/skills/get-immediate-context/scripts/call_graph.py --impact <filename>`
- **Check invariant impact before commit**: `python .agents/skills/get-immediate-context/scripts/diff_impact.py`

## Privacy & Safety
- Never store or display secrets. Wrap proprietary blocks in `<private>...</private>` markers.
EOF

# 2. Setup .claude config
mkdir -p "${SCRIPT_DIR}/.claude"
cat << EOF > "${SCRIPT_DIR}/.claude/config.json"
{
  "skillPath": ".agents/skills/get-immediate-context",
  "autoInjectBrief": true,
  "contextFile": "CONTEXT_BRIEF.md"
}
EOF

# 3. Generate initial brief & embeddings
echo "⚡ Generating initial orientation brief & code embeddings..."
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/fetch_context.py" --force
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/symbol_indexer.py"
$PYTHON_CMD "${SKILL_SOURCE_DIR}/scripts/code_embeddings.py" --generate

echo ""
echo "=========================================================="
echo "🎉 Claude Code Setup Complete!"
echo "=========================================================="
echo "Configured:"
echo "  1. CLAUDE.md (Project memory & agent orientation guidelines)"
echo "  2. .claude/config.json (Claude CLI settings)"
echo "  3. CONTEXT_BRIEF.md (Open Knowledge Format brief)"
echo "=========================================================="
