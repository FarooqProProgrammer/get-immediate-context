#!/usr/bin/env bash
# ==============================================================================
# install-cursor.sh - Install & Configure get-immediate-context for Cursor IDE
# ==============================================================================
# Sets up:
#   1. Cursor Skills (.cursor/skills/get-immediate-context/)
#   2. Cursor Rules (.cursor/rules/immediate-context.mdc & .cursorrules)
#   3. Cursor Lifecycle Hooks (.cursor/hooks/ & .git/hooks/)
#   4. Initial Knowledge Brief (CONTEXT_BRIEF.md) & 256-dim Code Embeddings
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE_DIR="${SCRIPT_DIR}/.agents/skills/get-immediate-context"

echo "=========================================================="
echo "🚀 Installing get-immediate-context & Skills for Cursor IDE"
echo "=========================================================="

# 1. Universal Python 3 Detection (Cross-platform: Linux, macOS, Windows)
PYTHON_CMD=""
if command -v python3 &> /dev/null && python3 -c "import sys" &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v py &> /dev/null && py -3 -c "import sys" &> /dev/null; then
    PYTHON_CMD="py -3"
elif command -v python &> /dev/null && python -c "import sys" &> /dev/null; then
    PYTHON_CMD="python"
elif [ -f "/c/Python314/python.exe" ]; then
    PYTHON_CMD="/c/Python314/python.exe"
elif [ -f "/c/Python313/python.exe" ]; then
    PYTHON_CMD="/c/Python313/python.exe"
elif [ -f "/c/Python312/python.exe" ]; then
    PYTHON_CMD="/c/Python312/python.exe"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python 3 runtime could not be found. Please ensure Python 3 is installed."
    exit 1
fi

echo "✔ Detected Python runtime: $($PYTHON_CMD --version 2>&1)"

# 2. Setup Cursor Directories (.cursor/skills, .cursor/rules, .cursor/hooks)
echo "📁 Setting up .cursor directory structure..."
mkdir -p "${SCRIPT_DIR}/.cursor/skills"
mkdir -p "${SCRIPT_DIR}/.cursor/rules"
mkdir -p "${SCRIPT_DIR}/.cursor/hooks"

# 3. Install Skill into .cursor/skills/
echo "📦 Installing skill into .cursor/skills/get-immediate-context..."
CURSOR_SKILL_TARGET="${SCRIPT_DIR}/.cursor/skills/get-immediate-context"
rm -rf "$CURSOR_SKILL_TARGET"
mkdir -p "$CURSOR_SKILL_TARGET"

# Copy SKILL.md, scripts, and references into .cursor/skills/
cp -r "${SKILL_SOURCE_DIR}/SKILL.md" "$CURSOR_SKILL_TARGET/"
cp -r "${SKILL_SOURCE_DIR}/scripts" "$CURSOR_SKILL_TARGET/"
cp -r "${SKILL_SOURCE_DIR}/references" "$CURSOR_SKILL_TARGET/"
echo "   ✔ Installed SKILL.md, scripts/, and references/ to .cursor/skills/"

# 4. Create Modern Cursor MDC Rule (.cursor/rules/immediate-context.mdc)
echo "📝 Creating .cursor/rules/immediate-context.mdc..."
cat << 'EOF' > "${SCRIPT_DIR}/.cursor/rules/immediate-context.mdc"
---
description: Always-active immediate codebase context, OKF orientation brief, live module symbol lines, and agent skills.
globs: *
alwaysApply: true
---

# Immediate Codebase Context & Agent Skills

Before beginning any task, refactoring, or code generation:
1. **Read CONTEXT_BRIEF.md**: Check the Open Knowledge Format (OKF) brief at the repository root.
2. **Hard Gate**: Confirm that `git_commit` in the brief matches the current working copy HEAD. If stale, run `.cursor/skills/get-immediate-context/scripts/fetch_context.py`.
3. **Obey Invariants**: Respect all domain invariants listed under Section 6 (`[INV-xxx]`). Preserve cited constraints.
4. **Symbol Line Locations**: Check Section 9 ("Live Code Location & Symbol Index") for exact line numbers (`Lxx-Lyy`) rather than reading entire files blindly.
5. **Use Agent Skills & Search Tools**:
   - **Locate Functions/Classes**: `python .cursor/skills/get-immediate-context/scripts/symbol_indexer.py --locate <symbol>`
   - **Semantic Concept Search**: `python .cursor/skills/get-immediate-context/scripts/code_embeddings.py --search "<intent>"`
   - **Memory / History Search**: `python .cursor/skills/get-immediate-context/scripts/mem_search.py "<query>"`
   - **Progressive Token Levels**: `python .cursor/skills/get-immediate-context/scripts/progressive_disclosure.py <1|2|3>`
6. **Privacy Enforcement**: Strip sensitive credentials. Never persist blocks wrapped in `<private>...</private>` tags.
EOF

# 5. Create Root .cursorrules (Backward compatibility for Cursor Chat & Composer)
echo "📝 Creating root .cursorrules..."
cat << 'EOF' > "${SCRIPT_DIR}/.cursorrules"
# get-immediate-context Cursor Rules & Skills Integration
# Read automatically by Cursor Composer and Chat on every interaction.

- Always refer to CONTEXT_BRIEF.md at the repository root for architecture, stack, and domain rules.
- Check Section 6 for confirmed invariants ([INV-xxx]) before altering calculation or business logic.
- Check Section 9 for exact symbol line numbers (Lxx-Lyy) rather than guessing file contents.
- Available Cursor skills & helper scripts in .cursor/skills/get-immediate-context/scripts/:
  * fetch_context.py: Refreshes OKF brief and checks git freshness
  * symbol_indexer.py --locate <name>: Locates exact line numbers of any function or class
  * code_embeddings.py --search "<concept>": Semantic similarity search across code chunks
  * mem_search.py "<term>": 3-step structured project history query
  * progressive_disclosure.py <level>: Exports Level 1 (~100 tokens), Level 2 (~800 tokens), or Level 3
EOF

# 6. Create Cursor Lifecycle Hook Script (.cursor/hooks/update-context.sh)
echo "⚓ Creating Cursor hook: .cursor/hooks/update-context.sh..."
cat << EOF > "${SCRIPT_DIR}/.cursor/hooks/update-context.sh"
#!/usr/bin/env bash
# Cursor lifecycle hook: auto-refreshes brief, symbol line numbers, and embeddings
REPO_ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_CMD}"

echo "[Cursor Hook] Refreshing immediate codebase context and symbol line map..."
"\$PYTHON_BIN" "\${REPO_ROOT}/.cursor/skills/get-immediate-context/scripts/fetch_context.py"
"\$PYTHON_BIN" "\${REPO_ROOT}/.cursor/skills/get-immediate-context/scripts/symbol_indexer.py"
echo "[Cursor Hook] Codebase context is fresh and verified."
EOF
chmod +x "${SCRIPT_DIR}/.cursor/hooks/update-context.sh"

# 7. Install Git Lifecycle Hooks (.git/hooks/)
if [ -d "${SCRIPT_DIR}/.git" ]; then
    echo "🔗 Installing git hooks into .git/hooks/..."
    HOOKS_DIR="${SCRIPT_DIR}/.git/hooks"
    mkdir -p "${HOOKS_DIR}"

    for HOOK_NAME in post-checkout post-commit post-merge; do
        HOOK_FILE="${HOOKS_DIR}/${HOOK_NAME}"
        cat << EOF > "${HOOK_FILE}"
#!/usr/bin/env bash
# get-immediate-context Cursor git hook
if [ -f "${SCRIPT_DIR}/.cursor/hooks/update-context.sh" ]; then
    "${SCRIPT_DIR}/.cursor/hooks/update-context.sh" > /dev/null 2>&1 &
fi
EOF
        chmod +x "${HOOK_FILE}"
        echo "   ✔ Installed ${HOOK_NAME} hook"
    done
else
    echo "ℹ Note: .git directory not found. Skipping git hooks installation."
fi

# 8. Run Initial Context & Embeddings Generation
echo "⚡ Generating initial Open Knowledge Format brief & code embeddings..."
$PYTHON_CMD "${CURSOR_SKILL_TARGET}/scripts/fetch_context.py" --force
$PYTHON_CMD "${CURSOR_SKILL_TARGET}/scripts/symbol_indexer.py"
$PYTHON_CMD "${CURSOR_SKILL_TARGET}/scripts/code_embeddings.py" --generate

echo ""
echo "=========================================================="
echo "🎉 Cursor IDE Skills & Hooks Installation Complete!"
echo "=========================================================="
echo "Configured Components:"
echo "  1. .cursor/skills/get-immediate-context/ (Cursor Skills Package)"
echo "  2. .cursor/rules/immediate-context.mdc (Modern Cursor MDC Rule)"
echo "  3. .cursorrules (Cursor Composer & Chat Prompt Guidelines)"
echo "  4. .cursor/hooks/update-context.sh (Automatic Lifecycle Hook)"
echo "  5. .git/hooks/ (post-checkout, post-commit, post-merge auto-refresh)"
echo "  6. CONTEXT_BRIEF.md (Verified OKF brief at repository root)"
echo "  7. .context/embeddings.json (Lightweight 256-dim Semantic Search)"
echo "=========================================================="
