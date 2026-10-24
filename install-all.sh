#!/usr/bin/env bash
# ==============================================================================
# install-all.sh - Universal One-Click Installer (Cursor, Claude, VS Code, Cline)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "🌐 Universal IDE Installer: get-immediate-context"
echo "=========================================================="

bash "${SCRIPT_DIR}/install-cursor.sh"
bash "${SCRIPT_DIR}/install-claude.sh"
bash "${SCRIPT_DIR}/install-vscode.sh"

echo ""
echo "=========================================================="
echo "🚀 All IDE environments configured successfully!"
echo "   - Cursor IDE (.cursor/ & .cursorrules)"
echo "   - Claude Code & Desktop (CLAUDE.md & .claude/)"
echo "   - VS Code, Cline & Roo Code (.vscode/ & .clinerules)"
echo "=========================================================="
