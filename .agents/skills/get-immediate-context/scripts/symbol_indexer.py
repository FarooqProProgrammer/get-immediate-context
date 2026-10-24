#!/usr/bin/env python3
"""
symbol_indexer.py - Live Code Location & Module Symbol Indexer

Maps every module's functions, classes, and handlers to exact files and line numbers.
Supports Python (native AST), TypeScript/JavaScript, Go, Rust, C#, and Java.
Can run incrementally after edits/prompts in <50ms.
"""

import os
import sys
import re
import ast
import json
import subprocess
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IGNORED_DIRS = {
    ".git", ".github", ".vscode", ".idea", ".gemini",
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", "target", "out", ".next", ".turbo",
    "coverage", ".pytest_cache", ".mypy_cache", "tmp", "temp", "vendor"
}

# Regex patterns for non-Python languages
REGEX_PATTERNS = {
    "ts_js": [
        re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)"),
        re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\("),
        re.compile(r"^\s*(?:export\s+)?interface\s+([a-zA-Z0-9_$]+)"),
    ],
    "go": [
        re.compile(r"^func\s+(?:\([^\)]+\)\s+)?([a-zA-Z0-9_]+)\s*\("),
        re.compile(r"^type\s+([a-zA-Z0-9_]+)\s+(?:struct|interface)"),
    ],
    "rs": [
        re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)"),
        re.compile(r"^\s*(?:pub\s+)?struct\s+([a-zA-Z0-9_]+)"),
        re.compile(r"^\s*(?:pub\s+)?enum\s+([a-zA-Z0-9_]+)"),
        re.compile(r"^\s*impl(?:\s+[a-zA-Z0-9_]+)?\s+for\s+([a-zA-Z0-9_]+)"),
    ],
    "csharp_java": [
        re.compile(r"^\s*(?:public|private|protected|internal|static|\s)+class\s+([a-zA-Z0-9_]+)"),
        re.compile(r"^\s*(?:public|private|protected|internal|static|\s)+(?:async\s+)?(?:[\w<>\[\],\s]+)\s+([a-zA-Z0-9_]+)\s*\("),
    ]
}

def extract_python_symbols(filepath: Path):
    """Uses Python AST for exact 100% precision line numbers."""
    symbols = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(filepath))
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                symbols.append({
                    "symbol": f"def {node.name}()",
                    "kind": "function",
                    "line": node.lineno,
                    "end_line": end_line,
                    "loc": f"L{node.lineno}-L{end_line}"
                })
            elif isinstance(node, ast.ClassDef):
                end_line = getattr(node, "end_lineno", node.lineno)
                symbols.append({
                    "symbol": f"class {node.name}",
                    "kind": "class",
                    "line": node.lineno,
                    "end_line": end_line,
                    "loc": f"L{node.lineno}-L{end_line}"
                })
                # Methods inside class
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sub_end = getattr(sub, "end_lineno", sub.lineno)
                        symbols.append({
                            "symbol": f"  -> {node.name}.{sub.name}()",
                            "kind": "method",
                            "line": sub.lineno,
                            "end_line": sub_end,
                            "loc": f"L{sub.lineno}-L{sub_end}"
                        })
    except Exception:
        pass
    return symbols

def extract_regex_symbols(filepath: Path, lang_key: str):
    """Extracts symbols from TS, JS, Go, Rust, Java, C# via line regex."""
    symbols = []
    patterns = REGEX_PATTERNS.get(lang_key, [])
    try:
        lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
        for lineno, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                continue
            for pat in patterns:
                m = pat.search(line)
                if m:
                    sym_name = m.group(1)
                    symbols.append({
                        "symbol": sym_name,
                        "kind": "symbol",
                        "line": lineno,
                        "end_line": lineno,
                        "loc": f"L{lineno}"
                    })
                    break
    except Exception:
        pass
    return symbols

def index_file(filepath: Path):
    ext = filepath.suffix.lower()
    if ext == ".py":
        return extract_python_symbols(filepath)
    elif ext in [".ts", ".tsx", ".js", ".jsx"]:
        return extract_regex_symbols(filepath, "ts_js")
    elif ext == ".go":
        return extract_regex_symbols(filepath, "go")
    elif ext == ".rs":
        return extract_regex_symbols(filepath, "rs")
    elif ext in [".cs", ".java"]:
        return extract_regex_symbols(filepath, "csharp_java")
    return []

def get_git_modified_files(repo_root: Path):
    """Gets files changed in working tree or recent commits for instant incremental indexing."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        )
        changed = []
        for line in out.splitlines():
            if len(line) > 3:
                changed.append(line[3:].strip())
        return changed
    except Exception:
        return []

def build_symbol_index(repo_root: Path, target_files=None):
    """Walks files and extracts symbol index mapping modules to exact line numbers."""
    index = {}
    valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".cs", ".java"}

    if target_files:
        files_to_scan = [repo_root / f for f in target_files if (repo_root / f).is_file() and (repo_root / f).suffix in valid_exts]
    else:
        files_to_scan = []
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".agents")]
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in valid_exts:
                    files_to_scan.append(Path(root) / f)

    for fp in files_to_scan:
        rel = fp.relative_to(repo_root).as_posix()
        symbols = index_file(fp)
        if symbols:
            index[rel] = symbols

    return index

def save_symbol_index(repo_root: Path, index: dict):
    context_dir = repo_root / ".context"
    context_dir.mkdir(exist_ok=True)
    json_path = context_dir / "symbol_map.json"
    json_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return json_path

def locate_symbol(repo_root: Path, query: str):
    """Locates where a function/class is located, in which file and line."""
    json_path = repo_root / ".context" / "symbol_map.json"
    if not json_path.is_file():
        index = build_symbol_index(repo_root)
        save_symbol_index(repo_root, index)
    else:
        index = json.loads(json_path.read_text(encoding="utf-8"))

    results = []
    q = query.lower()
    for file_path, sym_list in index.items():
        for s in sym_list:
            if q in s["symbol"].lower():
                results.append((s["symbol"], file_path, s["loc"], s["line"]))

    print(f"=== Code Location Search: '{query}' ===")
    if not results:
        print(f"  No symbol found matching '{query}'.")
        return

    print(f"{'Symbol':<35} | {'File Path':<45} | {'Line'}")
    print("-" * 90)
    for sym, fpath, loc, line in results:
        print(f"{sym[:35]:<35} | {fpath[:45]:<45} | {loc}")

def generate_symbol_markdown_summary(index: dict, max_entries: int = 15) -> str:
    """Generates a concise markdown table of key modules, code locations, and lines."""
    lines = [
        "## 9. Live Code Location & Symbol Index (Module -> File : Line)",
        "| Module / File | Key Symbol | Line Location |",
        "|---|---|---|"
    ]
    count = 0
    for fpath, syms in index.items():
        for s in syms:
            if s["kind"] in ["class", "function", "symbol"]:
                lines.append(f"| `{fpath}` | `{s['symbol']}` | `{s['loc']}` |")
                count += 1
                if count >= max_entries:
                    break
        if count >= max_entries:
            break

    if count == 0:
        lines.append("| (No major class/function declarations indexed yet) | - | - |")
    return "\n".join(lines)

def update_live_code_locations(repo_root: Path, brief_path: Path):
    """Updates symbol index and injects updated location map into CONTEXT_BRIEF.md."""
    index = build_symbol_index(repo_root)
    save_symbol_index(repo_root, index)

    if brief_path.is_file():
        content = brief_path.read_text(encoding="utf-8")
        symbol_md = generate_symbol_markdown_summary(index)

        # Replace existing section 9 or append
        if "## 9. Live Code Location & Symbol Index" in content:
            parts = content.split("## 9. Live Code Location & Symbol Index")
            new_content = parts[0].rstrip() + "\n\n" + symbol_md + "\n"
        else:
            new_content = content.rstrip() + "\n\n" + symbol_md + "\n"

        brief_path.write_text(new_content, encoding="utf-8")
        print(f"[SUCCESS] Live code locations updated in {brief_path.name} & .context/symbol_map.json")

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]

    if "--locate" in args:
        idx = args.index("--locate")
        if idx + 1 < len(args):
            locate_symbol(repo_root, args[idx + 1])
        else:
            print("Usage: python symbol_indexer.py --locate <symbol_name>")
        return

    brief_path = repo_root / "CONTEXT_BRIEF.md"
    update_live_code_locations(repo_root, brief_path)

if __name__ == "__main__":
    main()
