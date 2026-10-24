#!/usr/bin/env python3
"""
call_graph.py - Inter-Module Dependency & Blast Radius Analyzer

Maps import and dependency relationships across Python, TypeScript/JavaScript,
Go, and Rust. Calculates upstream dependencies, downstream dependents, and
computes the "blast radius" (ripple effect) before refactoring.
"""

import os
import sys
import re
import json
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

# Regex for imports across languages
IMPORT_PATTERNS = {
    "py": [
        re.compile(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import"),
        re.compile(r"^\s*import\s+([a-zA-Z0-9_\.]+)"),
    ],
    "ts_js": [
        re.compile(r"""(?:import|from)\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "go": [
        re.compile(r"""['"]([a-zA-Z0-9_\-\.\/]+)['"]"""),
    ],
    "rs": [
        re.compile(r"^\s*use\s+([a-zA-Z0-9_:]+)"),
        re.compile(r"^\s*mod\s+([a-zA-Z0-9_]+)"),
    ]
}

def extract_file_imports(filepath: Path) -> list[str]:
    ext = filepath.suffix.lower()
    imports = []
    lang_key = None
    if ext == ".py": lang_key = "py"
    elif ext in [".ts", ".tsx", ".js", ".jsx"]: lang_key = "ts_js"
    elif ext == ".go": lang_key = "go"
    elif ext == ".rs": lang_key = "rs"

    if not lang_key:
        return imports

    patterns = IMPORT_PATTERNS[lang_key]
    try:
        lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines[:100]:  # imports are at top
            line_str = line.strip()
            for pat in patterns:
                m = pat.search(line_str)
                if m:
                    imp = m.group(1).strip()
                    if imp and not imp.startswith("."):
                        imports.append(imp.split(".")[0])
                    elif imp:
                        imports.append(imp)
                    break
    except Exception:
        pass
    return list(set(imports))

def build_dependency_graph(repo_root: Path) -> dict:
    valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
    modules = {}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".agents")]
        for f in files:
            fp = Path(root) / f
            if fp.suffix.lower() in valid_exts:
                rel = fp.relative_to(repo_root).as_posix()
                raw_imports = extract_file_imports(fp)
                modules[rel] = {
                    "file": rel,
                    "imports": raw_imports,
                    "dependents": []  # who imports this
                }

    # Resolve reverse dependencies (dependents)
    all_files = list(modules.keys())
    for mod_path, data in modules.items():
        stem = Path(mod_path).stem
        for other_path, other_data in modules.items():
            if mod_path != other_path:
                for imp in other_data["imports"]:
                    if stem in imp or imp in mod_path:
                        data["dependents"].append(other_path)
                        break

    return modules

def analyze_blast_radius(modules: dict, target_query: str):
    """Calculates downstream dependents affected if target is modified."""
    matches = [m for m in modules.keys() if target_query.lower() in m.lower()]
    if not matches:
        print(f"[!] No module found matching '{target_query}'.")
        return

    print(f"\n=== 💥 Blast Radius & Dependency Impact: '{target_query}' ===")
    for target in matches:
        data = modules[target]
        print(f"\nTarget Module: {target}")
        print(f"  Outgoing Dependencies ({len(data['imports'])}):")
        for imp in data["imports"][:6]:
            print(f"    -> {imp}")

        print(f"  Downstream Dependents / Ripple Effect ({len(data['dependents'])}):")
        if data["dependents"]:
            for dep in data["dependents"]:
                print(f"    ⚠️  [AFFECTED] {dep}")
        else:
            print("    ✔ Leaf module: No downstream dependents directly affected.")

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]

    graph = build_dependency_graph(repo_root)

    # Save to .context/call_graph.json
    context_dir = repo_root / ".context"
    context_dir.mkdir(exist_ok=True)
    graph_file = context_dir / "call_graph.json"
    graph_file.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    if "--impact" in args:
        idx = args.index("--impact")
        if idx + 1 < len(args):
            analyze_blast_radius(graph, args[idx + 1])
        else:
            print("Usage: python call_graph.py --impact <filename_or_module>")
        return

    # Print summary
    print(f"=== 🕸️ Module Dependency Graph ({len(graph)} modules mapped) ===")
    print(f"Graph cached to {graph_file.name}")
    # Sort by number of dependents (God modules / most coupled)
    coupled = sorted(graph.values(), key=lambda x: len(x["dependents"]), reverse=True)
    print("\nTop Load-Bearing Modules (Highest Ripple Effect Risk):")
    for item in coupled[:5]:
        print(f"  - `{item['file']}`: Imported by {len(item['dependents'])} downstream files")

    print("\n💡 Tip: To calculate blast radius for a specific file before refactoring:")
    print("   python call_graph.py --impact <filename>")

if __name__ == "__main__":
    main()
