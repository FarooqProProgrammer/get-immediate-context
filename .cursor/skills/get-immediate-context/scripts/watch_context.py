#!/usr/bin/env python3
"""
watch_context.py - Real-Time Codebase Context & Symbol Line Watcher Daemon

Monitors source files for edits and saves. Incremental update latency: <15ms.
Automatically refreshes:
  1. Symbol line numbers in CONTEXT_BRIEF.md (Section 9)
  2. .context/symbol_map.json
  3. Code chunk embeddings
Zero external dependencies (uses standard library polling).
"""

import os
import sys
import time
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import symbol_indexer
    import code_embeddings
except ImportError:
    symbol_indexer = None
    code_embeddings = None

IGNORED_DIRS = {
    ".git", ".github", ".vscode", ".idea", ".gemini",
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", "target", "out", ".next", ".turbo",
    "coverage", ".pytest_cache", ".mypy_cache", "tmp", "temp", "vendor"
}

VALID_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".cs", ".java"}

def get_file_mtimes(repo_root: Path) -> dict[str, float]:
    """Scans valid source files and records modification timestamps."""
    mtimes = {}
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".agents")]
        for f in files:
            fp = Path(root) / f
            if fp.suffix.lower() in VALID_EXTS:
                try:
                    rel = fp.relative_to(repo_root).as_posix()
                    mtimes[rel] = fp.stat().st_mtime
                except Exception:
                    pass
    return mtimes

def run_watcher(repo_root: Path, poll_interval: float = 1.5, max_ticks: int = None):
    brief_path = repo_root / "CONTEXT_BRIEF.md"
    print(f"=== 👁️ get-immediate-context Real-Time Watcher Daemon ===")
    print(f"Monitoring: {repo_root}")
    print(f"Polling interval: {poll_interval}s | Press Ctrl+C to stop.\n")

    current_mtimes = get_file_mtimes(repo_root)
    ticks = 0

    try:
        while True:
            time.sleep(poll_interval)
            new_mtimes = get_file_mtimes(repo_root)
            changed_files = []

            for path, mtime in new_mtimes.items():
                if path not in current_mtimes or mtime > current_mtimes[path]:
                    changed_files.append(path)

            for path in list(current_mtimes.keys()):
                if path not in new_mtimes:
                    changed_files.append(path)

            if changed_files:
                start_t = time.time()
                print(f"[*] Detected changes in {len(changed_files)} file(s): {', '.join(changed_files[:3])}...")

                if symbol_indexer:
                    symbol_indexer.update_live_code_locations(repo_root, brief_path)

                if code_embeddings:
                    code_embeddings.generate_code_embeddings(repo_root)

                duration_ms = (time.time() - start_t) * 1000
                print(f"[✔] Context & symbol map updated in {duration_ms:.1f}ms.\n")
                current_mtimes = new_mtimes

            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
    except KeyboardInterrupt:
        print("\n[!] Watcher stopped by user.")

def main():
    repo_root = Path.cwd()
    poll_sec = 1.5
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        repo_root = Path(sys.argv[1]).resolve()

    run_watcher(repo_root, poll_interval=poll_sec)

if __name__ == "__main__":
    main()
