#!/usr/bin/env python3
"""
mem_search.py - 3-Step Smart Project Knowledge & Memory Search

Implements progressive search across repository memory and context briefs:
  Step 1: Scan query against memory index
  Step 2: Preview candidate matches with token cost estimates
  Step 3: Fetch targeted observation details on demand
"""

import sys
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def search_memory(repo_root: Path, query: str, fetch_id: str = None):
    brief_file = repo_root / "CONTEXT_BRIEF.md"
    if not brief_file.is_file():
        print(f"[ERROR] CONTEXT_BRIEF.md not found in {repo_root}. Run fetch_context.py first.")
        return

    content = brief_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Step 3: Direct fetch mode
    if fetch_id:
        print(f"=== Fetching Record: {fetch_id} ===")
        found = False
        for line in lines:
            if fetch_id.lower() in line.lower():
                print(f"  {line}")
                found = True
        if not found:
            print(f"  No record found matching ID '{fetch_id}'.")
        return

    # Step 1 & 2: Progressive search and candidate review
    print(f"=== Smart Search: '{query}' in {brief_file.name} ===")
    matches = []
    current_section = "General"

    for idx, line in enumerate(lines, start=1):
        if line.startswith("#"):
            current_section = line.strip("# ").strip()
        if query.lower() in line.lower() and not line.startswith("tags:"):
            # Estimate token cost (~1 token = 4 characters)
            token_estimate = max(1, len(line) // 4)
            matches.append((idx, current_section, line.strip(), token_estimate))

    if not matches:
        print("  No direct matches found. Try broadening your query terms.")
        return

    print(f"Found {len(matches)} candidate matches:\n")
    print(f"{'Line':<6} | {'Section':<25} | {'Tokens':<7} | {'Snippet'}")
    print("-" * 75)
    for line_no, sec, snippet, tokens in matches:
        display_snippet = snippet if len(snippet) <= 45 else snippet[:42] + "..."
        print(f"{line_no:<6} | {sec[:25]:<25} | {tokens:<7} | {display_snippet}")

    print("\nTip: To fetch full context for a specific item, run:")
    print(f"   python mem_search.py --fetch <ID_OR_KEYWORD>")

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python mem_search.py <query>")
        print("  python mem_search.py --fetch <ID>")
        return

    if "--fetch" in args:
        idx = args.index("--fetch")
        if idx + 1 < len(args):
            fetch_id = args[idx + 1]
            search_memory(repo_root, query="", fetch_id=fetch_id)
        else:
            print("[ERROR] Please provide an ID or keyword to fetch.")
    else:
        query = " ".join(args)
        search_memory(repo_root, query=query)

if __name__ == "__main__":
    main()
