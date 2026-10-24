#!/usr/bin/env python3
"""
progressive_disclosure.py - Layered Context Exporter with Token Cost Visibility

Outputs context at 3 discrete levels:
  Level 1 (Index, ~100 tokens): Git SHA, branch, project name, topology
  Level 2 (Brief, ~800 tokens): Standard OKF Brief (purpose, stack, run commands, invariants)
  Level 3 (Deep Dive): Full concept and architecture drill-down
"""

import sys
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_token_count(text: str) -> int:
    return max(1, len(text) // 4)

def export_progressive_context(repo_root: Path, level: int = 2):
    brief_file = repo_root / "CONTEXT_BRIEF.md"
    if not brief_file.is_file():
        print(f"[ERROR] CONTEXT_BRIEF.md not found in {repo_root}. Please run fetch_context.py first.")
        return

    content = brief_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    if level == 1:
        # Index level: extract frontmatter and title
        frontmatter = []
        in_fm = False
        for line in lines:
            if line.strip() == "---":
                if not in_fm:
                    in_fm = True
                    frontmatter.append(line)
                    continue
                else:
                    frontmatter.append(line)
                    break
            if in_fm:
                frontmatter.append(line)
        output = "\n".join(frontmatter)
        tokens = get_token_count(output)
        print(f"=== Level 1: Index Context [Estimated Tokens: ~{tokens}] ===")
        print(output)

    elif level == 2:
        # Standard OKF Brief level (exclude unneeded deep sections if any)
        tokens = get_token_count(content)
        print(f"=== Level 2: Standard OKF Brief [Estimated Tokens: ~{tokens}] ===")
        print(content)

    elif level == 3:
        # Deep Dive level: prints brief + file structure of core entry points
        tokens = get_token_count(content) + 200
        print(f"=== Level 3: Deep Dive Context [Estimated Tokens: ~{tokens}] ===")
        print(content)
        print("\n--- Additional Directory Topology ---")
        for item in sorted(repo_root.iterdir()):
            if not item.name.startswith("."):
                print(f" - {item.name}/" if item.is_dir() else f" - {item.name}")

def main():
    repo_root = Path.cwd()
    level = 2
    if len(sys.argv) > 1:
        try:
            level = int(sys.argv[1])
        except ValueError:
            pass

    export_progressive_context(repo_root, level=level)

if __name__ == "__main__":
    main()
