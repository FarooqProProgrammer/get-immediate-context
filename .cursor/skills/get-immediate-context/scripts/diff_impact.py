#!/usr/bin/env python3
"""
diff_impact.py - Git Diff Invariant Guardian & Impact Analyzer

Analyzes git diffs (staged, unstaged, or commit ranges) and cross-references
changed lines against confirmed domain invariants ([INV-xxx]) in CONTEXT_BRIEF.md.
Alerts developers and agents before regressions or broken business rules occur.
"""

import sys
import re
import subprocess
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def extract_invariants_from_brief(brief_path: Path) -> list[dict]:
    """Parses Section 6 of CONTEXT_BRIEF.md to extract invariant IDs, rules, and file:line citations."""
    invariants = []
    if not brief_path.is_file():
        return invariants

    content = brief_path.read_text(encoding="utf-8")
    # Match: - **[INV-001]**: `rule text` (Source: `file:line`)
    pattern = re.compile(r"-\s+\*\*\[(INV-\d+)\]\*\*:\s+`([^`]+)`\s+\(Source:\s+`([^`:]+):?(\d+)?`\)")
    for match in pattern.finditer(content):
        inv_id, rule, file_path, line_no = match.groups()
        invariants.append({
            "id": inv_id,
            "rule": rule,
            "file": file_path.strip().replace("\\", "/"),
            "line": int(line_no) if line_no else None
        })
    return invariants

def parse_git_diff(repo_root: Path, diff_args: list[str]) -> dict[str, list[int]]:
    """Runs git diff and extracts touched line numbers per file."""
    cmd = ["git", "diff"] + (diff_args if diff_args else ["HEAD"])
    try:
        output = subprocess.check_output(cmd, cwd=repo_root, stderr=subprocess.DEVNULL, text=True)
    except Exception:
        # Fallback to unstaged diff
        try:
            output = subprocess.check_output(["git", "diff"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True)
        except Exception:
            return {}

    touched_files = {}
    current_file = None

    for line in output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip().replace("\\", "/")
            touched_files[current_file] = []
        elif line.startswith("@@ ") and current_file:
            # Parse @@ -old,old_len +new_start,new_len @@
            m = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) else 1
                touched_files[current_file].extend(range(start, start + count))

    return touched_files

def check_diff_impact(repo_root: Path, diff_args: list[str] = None, strict: bool = False):
    brief_path = repo_root / "CONTEXT_BRIEF.md"
    invariants = extract_invariants_from_brief(brief_path)
    touched_files = parse_git_diff(repo_root, diff_args)

    print(f"=== 🛡️ Invariant Guardian & Diff Impact Analysis ===")
    if not touched_files:
        print("  No modified files detected in current git diff.")
        return 0

    impacted_invariants = []

    for inv in invariants:
        inv_file = inv["file"]
        # Check if modified
        for touched_f, line_nums in touched_files.items():
            if touched_f.endswith(inv_file) or inv_file.endswith(touched_f):
                # If specific line number was recorded, check proximity (within 15 lines)
                if inv["line"] is not None:
                    is_near = any(abs(l - inv["line"]) <= 15 for l in line_nums)
                    if is_near or not line_nums:
                        impacted_invariants.append((inv, touched_f, inv["line"]))
                else:
                    impacted_invariants.append((inv, touched_f, "File level"))

    if impacted_invariants:
        print("\n🚨 WARNING: The current diff touches code linked to confirmed domain invariants!\n")
        print(f"{'Invariant ID':<15} | {'Source Location':<30} | {'Domain Constraint Rule'}")
        print("-" * 90)
        for inv, fpath, line_info in impacted_invariants:
            loc = f"{fpath}:{line_info}"
            print(f"{inv['id']:<15} | {loc:<30} | {inv['rule']}")

        print("\n⚠️ Mandatory Verification Checkpoints:")
        print("  1. Verify this change intentionally modifies the domain rule.")
        print("  2. Ensure corresponding regression tests were updated to lock in new behavior.")
        print("  3. Run the test suite before committing.")

        if strict:
            print("\n[STRICT GATE FAILED] Diff impacts invariants without explicit confirmation.")
            return 1
        return 0
    else:
        print(f"✔ Safe: Scanned {len(touched_files)} changed files across {len(invariants)} registered invariants.")
        print("  No critical business logic constraints were impacted.")
        return 0

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]
    strict = "--strict" in args
    diff_args = [a for a in args if a != "--strict"]

    exit_code = check_diff_impact(repo_root, diff_args=diff_args, strict=strict)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
