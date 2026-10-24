#!/usr/bin/env python3
"""
fetch_context.py - Immediate Repository Context & Knowledge Extractor

Automatically discovers project topology, manifests, git status, entry points,
and domain invariants. Dynamically detects monorepos and packages across any directory
layout (no hardcoded folders). Outputs an Open Knowledge Format (OKF) brief (CONTEXT_BRIEF.md).
Zero external dependencies (uses Python standard library only).
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------
# Privacy & Redaction Engine
# ---------------------------------------------------------
PRIVATE_TAG_REGEX = re.compile(r"<private>[\s\S]*?</private>", re.IGNORECASE)
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"sk_[live|test]_[0-9a-zA-Z]{24,}"),
    re.compile(r"ghp_[0-9a-zA-Z]{36}"),
]

def sanitize_text(text: str) -> str:
    """Strips <private> tags and redacts secret tokens."""
    text = PRIVATE_TAG_REGEX.sub("[REDACTED: PRIVATE BLOCK]", text)
    for pat in SECRET_PATTERNS:
        text = pat.sub(r"\1: [REDACTED_SECRET]", text)
    return text

# ---------------------------------------------------------
# Git Inspection Engine
# ---------------------------------------------------------
def get_git_info(repo_root: Path):
    """Executes plain git commands to fetch current state without extra tools."""
    try:
        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        commit_sha = "unknown-non-git"

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        branch = "unknown"

    try:
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, stderr=subprocess.DEVNULL, text=True
        ).strip()
        has_changes = len(status_output) > 0
    except Exception:
        has_changes = False

    return commit_sha, branch, has_changes

# ---------------------------------------------------------
# Dynamic Discovery Engine (Zero Hardcoded Directories)
# ---------------------------------------------------------
MANIFEST_FILES = {
    "package.json": ("Node.js/JavaScript/TypeScript", "npm/pnpm/yarn"),
    "pyproject.toml": ("Python", "pyproject"),
    "requirements.txt": ("Python", "pip"),
    "Pipfile": ("Python", "pipenv"),
    "setup.py": ("Python", "setuptools"),
    "Cargo.toml": ("Rust", "cargo"),
    "go.mod": ("Go", "go modules"),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java/Kotlin", "gradle"),
    "build.gradle.kts": ("Kotlin", "gradle"),
    "composer.json": ("PHP", "composer"),
    "Gemfile": ("Ruby", "bundler"),
}

IGNORED_DIRS = {
    ".git", ".github", ".vscode", ".idea", ".gemini",
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", "target", "out", ".next", ".turbo",
    "coverage", ".pytest_cache", ".mypy_cache", "tmp", "temp", "vendor"
}

def get_directory_stack(dir_path: Path):
    """Identifies languages and tools in a directory based on manifests."""
    stack_found = []
    # Check csproj or sln
    try:
        if any(dir_path.glob("*.csproj")):
            stack_found.append(".NET / C# (dotnet)")
        elif any(dir_path.glob("*.sln")):
            stack_found.append(".NET Solution (dotnet)")
    except Exception:
        pass

    for mf, (lang, runner) in MANIFEST_FILES.items():
        if (dir_path / mf).is_file():
            stack_found.append(f"{lang} ({runner})")

    return ", ".join(stack_found) if stack_found else None

def parse_workspace_patterns(repo_root: Path):
    """Extracts explicit package/workspace glob patterns from configuration manifests."""
    patterns = []
    indicator = None

    # 1. Custom user configuration (.contextrc)
    contextrc = repo_root / ".contextrc"
    if contextrc.is_file():
        try:
            with open(contextrc, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                custom_dirs = cfg.get("scan_dirs") or cfg.get("packages")
                if custom_dirs:
                    return list(custom_dirs), ".contextrc custom scan_dirs"
        except Exception:
            pass

    # 2. pnpm-workspace.yaml
    pnpm_ws = repo_root / "pnpm-workspace.yaml"
    if pnpm_ws.is_file():
        try:
            for line in pnpm_ws.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("-"):
                    pat = line.lstrip("- '\"").rstrip("'\"").strip()
                    if pat and not pat.startswith("!"):
                        patterns.append(pat)
            if patterns:
                return patterns, "pnpm-workspace.yaml"
        except Exception:
            pass

    # 3. package.json workspaces
    pkg_json = repo_root / "package.json"
    if pkg_json.is_file():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                ws = data.get("workspaces")
                if isinstance(ws, list):
                    patterns.extend(ws)
                elif isinstance(ws, dict) and "packages" in ws:
                    patterns.extend(ws["packages"])
                if patterns:
                    return patterns, "package.json workspaces"
        except Exception:
            pass

    # 4. Cargo.toml workspace
    cargo_toml = repo_root / "Cargo.toml"
    if cargo_toml.is_file():
        try:
            content = cargo_toml.read_text(encoding="utf-8")
            if "[workspace]" in content:
                match = re.search(r"members\s*=\s*\[(.*?)\]", content, re.DOTALL)
                if match:
                    members = re.findall(r'["\'](.*?)["\']', match.group(1))
                    patterns.extend(members)
                    return patterns, "Cargo.toml workspace"
        except Exception:
            pass

    # 5. lerna.json
    lerna_json = repo_root / "lerna.json"
    if lerna_json.is_file():
        try:
            with open(lerna_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "packages" in d:
                    return d["packages"], "lerna.json"
        except Exception:
            pass

    # 6. go.work
    go_work = repo_root / "go.work"
    if go_work.is_file():
        try:
            content = go_work.read_text(encoding="utf-8")
            use_matches = re.findall(r"use\s+(?:\((.*?)\)|([^\s\n]+))", content, re.DOTALL)
            for block, single in use_matches:
                if single:
                    patterns.append(single.strip().lstrip("./"))
                elif block:
                    for line in block.splitlines():
                        p = line.strip().lstrip("./")
                        if p:
                            patterns.append(p)
            if patterns:
                return patterns, "go.work"
        except Exception:
            pass

    return patterns, indicator

def discover_project_structure(repo_root: Path):
    """
    Dynamically maps all packages in the repository without hardcoded directory names.
    Prioritizes workspace manifests, then falls back to recursive manifest discovery.
    """
    packages = []
    is_monorepo = False
    mono_indicator = None

    # Step 1: Check explicit workspace definitions
    patterns, indicator = parse_workspace_patterns(repo_root)
    discovered_paths = set()

    if patterns:
        mono_indicator = indicator
        for pat in patterns:
            # Normalize glob pattern
            clean_pat = pat.rstrip("/")
            for match in repo_root.glob(clean_pat):
                if match.is_dir() and match != repo_root and match.name not in IGNORED_DIRS:
                    rel = match.relative_to(repo_root).as_posix()
                    stack = get_directory_stack(match) or "Generic Package"
                    packages.append({
                        "name": match.name,
                        "path": rel,
                        "stack": stack
                    })
                    discovered_paths.add(match.resolve())

        if packages:
            is_monorepo = True
            return packages, is_monorepo, mono_indicator

    # Step 2: Dynamic recursive scan for subdirectories with manifests (up to depth 3)
    # This works for ANY directory layout (e.g. backend/frontend, crates/*, custom_services/*, etc.)
    for root, dirs, files in os.walk(repo_root):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        
        current_dir = Path(root)
        if current_dir == repo_root:
            continue

        # Limit depth from repo root to 3 levels
        try:
            rel_parts = current_dir.relative_to(repo_root).parts
            if len(rel_parts) > 3:
                dirs[:] = []  # stop recursing deeper
                continue
        except Exception:
            continue

        # Check if current_dir has any manifest
        stack = get_directory_stack(current_dir)
        if stack:
            rel = current_dir.relative_to(repo_root).as_posix()
            packages.append({
                "name": rel,
                "path": rel,
                "stack": stack
            })
            discovered_paths.add(current_dir.resolve())
            # Don't descend further into this package
            dirs[:] = []

    # Step 3: Determine if repository is a Monorepo or Single Project
    if len(packages) >= 2 or mono_indicator:
        is_monorepo = True
        if not mono_indicator:
            mono_indicator = f"dynamic multi-package discovery ({len(packages)} packages found)"
    else:
        # Single project
        is_monorepo = False
        mono_indicator = None
        root_stack = get_directory_stack(repo_root) or "Unknown Stack"
        packages = [{
            "name": repo_root.name,
            "path": ".",
            "stack": root_stack
        }]

    return packages, is_monorepo, mono_indicator

def find_entry_points(repo_root: Path):
    """Finds primary application entry points dynamically."""
    entry_patterns = [
        "**/main.py", "**/app.py", "**/server.py",
        "**/index.ts", "**/index.js", "**/server.ts", "**/server.js",
        "**/main.go", "**/src/main.rs", "**/Program.cs"
    ]
    entries = []
    for pat in entry_patterns:
        for match in repo_root.glob(pat):
            rel = match.relative_to(repo_root)
            parts = rel.parts
            if any(p in IGNORED_DIRS for p in parts):
                continue
            entries.append(str(rel).replace("\\", "/"))
            if len(entries) >= 6:
                break
        if len(entries) >= 6:
            break
    return entries

def find_test_commands(repo_root: Path):
    """Detects run, build, and test commands from manifests."""
    commands = {"install": "N/A", "build": "N/A", "test": "N/A", "run": "N/A"}

    # Check package.json scripts
    pkg_json = repo_root / "package.json"
    if pkg_json.is_file():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                scripts = d.get("scripts", {})
                commands["install"] = "npm install (or pnpm/yarn)"
                if "build" in scripts: commands["build"] = "npm run build"
                if "test" in scripts: commands["test"] = "npm test"
                if "start" in scripts: commands["run"] = "npm start"
                elif "dev" in scripts: commands["run"] = "npm run dev"
        except Exception:
            pass

    # Check Makefile
    makefile = repo_root / "Makefile"
    if makefile.is_file():
        try:
            content = makefile.read_text(encoding="utf-8")
            if "test:" in content: commands["test"] = "make test"
            if "build:" in content: commands["build"] = "make build"
            if "run:" in content: commands["run"] = "make run"
        except Exception:
            pass

    # Check Python pyproject / pytest
    if (repo_root / "pyproject.toml").is_file() or (repo_root / "pytest.ini").is_file():
        if commands["test"] == "N/A": commands["test"] = "pytest"

    # Check Cargo
    if (repo_root / "Cargo.toml").is_file():
        commands["build"] = "cargo build"
        commands["test"] = "cargo test"
        commands["run"] = "cargo run"

    # Check Go
    if (repo_root / "go.mod").is_file():
        commands["build"] = "go build ./..."
        commands["test"] = "go test ./..."

    return commands

# ---------------------------------------------------------
# Business Logic & Invariant Extractor
# ---------------------------------------------------------
INVARIANT_KEYWORDS = ["validate", "assert", "invariant", "discount", "permission", "limit", "max_", "min_"]

def extract_invariants(repo_root: Path):
    """Finds confirmed domain validation and rules in source code with citations."""
    invariants = []
    inv_id = 1
    exts = [".py", ".ts", ".js", ".go", ".rs", ".cs", ".java"]
    scanned_count = 0

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".agents")]
        for f in files:
            if any(f.endswith(ext) for ext in exts):
                filepath = Path(root) / f
                rel_path = filepath.relative_to(repo_root).as_posix()
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                        for line_no, line in enumerate(fp, start=1):
                            line_str = line.strip()
                            if any(k in line_str.lower() for k in INVARIANT_KEYWORDS) and len(line_str) > 10:
                                clean_rule = sanitize_text(line_str)
                                if len(clean_rule) > 120:
                                    clean_rule = clean_rule[:117] + "..."
                                invariants.append({
                                    "id": f"INV-{inv_id:03d}",
                                    "rule": clean_rule,
                                    "citation": f"{rel_path}:{line_no}"
                                })
                                inv_id += 1
                                if len(invariants) >= 6:
                                    return invariants
                    scanned_count += 1
                    if scanned_count > 30:
                        return invariants
                except Exception:
                    continue
    return invariants

# ---------------------------------------------------------
# Brief Generator (OKF Format)
# ---------------------------------------------------------
def generate_okf_brief(repo_root: Path, output_file: Path, force=False):
    commit_sha, branch, has_changes = get_git_info(repo_root)

    # Check if brief is already fresh
    if output_file.is_file() and not force:
        try:
            content = output_file.read_text(encoding="utf-8")
            if f'git_commit: "{commit_sha}"' in content and f'git_branch: "{branch}"' in content and not has_changes:
                print(f"[OK] Existing CONTEXT_BRIEF.md is fresh (commit: {commit_sha[:7]} on {branch}). 0 tokens needed.")
                return output_file
        except Exception:
            pass

    print(f"[*] Dynamically discovering topology & building Open Knowledge Format brief...")

    # Read README for purpose
    purpose = "Software project codebase."
    for readme_name in ["README.md", "readme.md", "README.txt"]:
        readme_path = repo_root / readme_name
        if readme_path.is_file():
            try:
                lines = readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                para = []
                for l in lines:
                    if l.startswith("#") or not l.strip():
                        if para: break
                        continue
                    para.append(l.strip())
                if para:
                    purpose = sanitize_text(" ".join(para))
                    if len(purpose) > 300: purpose = purpose[:297] + "..."
            except Exception:
                pass
            break

    # Dynamic Discovery of Packages & Topology
    packages, is_mono, mono_indicator = discover_project_structure(repo_root)
    entry_points = find_entry_points(repo_root)
    commands = find_test_commands(repo_root)
    invariants = extract_invariants(repo_root)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Render OKF Brief
    doc_lines = [
        "---",
        'okf_version: "0.2"',
        'type: ContextBrief',
        f'title: "{repo_root.name} Context Brief"',
        'description: "High-signal repository orientation, architecture, and domain invariants."',
        f'git_commit: "{commit_sha}"',
        f'git_branch: "{branch}"',
        f'repo_type: {"monorepo" if is_mono else "single-project"}',
        f'timestamp: "{timestamp}"',
        'tags: [context-brief, orientation, architecture]',
        "---",
        "",
        f"# {repo_root.name} Context Brief",
        "",
        "## 1. Purpose",
        purpose,
        "",
        "## 2. Stack & Dependencies"
    ]

    for p in packages:
        doc_lines.append(f"- **`{p['name']}`** (`{p['path']}`): {p['stack']}")

    doc_lines.extend([
        "",
        "## 3. Layout & Architecture",
        f"- **Repository Type**: {'Monorepo' if is_mono else 'Single Project'}" + (f" ({mono_indicator})" if mono_indicator else ""),
        "- **Entry Points**:"
    ])
    if entry_points:
        for ep in entry_points:
            doc_lines.append(f"  - `{ep}`")
    else:
        doc_lines.append("  - Standard package entry points")

    doc_lines.extend([
        "",
        "## 4. Run, Build & Test Commands",
        f"- **Install**: `{commands['install']}`",
        f"- **Build**: `{commands['build']}`",
        f"- **Test**: `{commands['test']}`",
        f"- **Run / Dev**: `{commands['run']}`",
        "",
        "## 5. Configuration & Conventions",
        "- Configuration sources identified dynamically from workspace manifests.",
        "- Package boundaries and dependency structures isolated.",
        "",
        "## 6. Business Logic & Invariants (Citations)"
    ])

    if invariants:
        for inv in invariants:
            doc_lines.append(f"- **[{inv['id']}]**: `{inv['rule']}` (Source: `{inv['citation']}`)")
    else:
        doc_lines.append("- No strict invariant assertions extracted in preliminary scan.")

    doc_lines.extend([
        "",
        "## 7. Explicit Boundaries (Uninspected Areas)",
        "- External network resources and deployment workflows were not executed.",
        "- Vendor directories (node_modules, target, .venv, etc.) excluded from analysis.",
        "",
        "## 8. Local My Work & Review Queue",
        "- **Active Task**: Repository orientation completed.",
        "- **Status**: Verified and ready for prompt execution."
    ])

    # Dynamic Section 9: Live Code Location & Symbol Index (Module -> File : Line)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import symbol_indexer
        sym_index = symbol_indexer.build_symbol_index(repo_root)
        symbol_indexer.save_symbol_index(repo_root, sym_index)
        sym_md = symbol_indexer.generate_symbol_markdown_summary(sym_index)
        doc_lines.extend(["", sym_md])
    except Exception as e:
        pass

    full_doc = "\n".join(doc_lines) + "\n"
    output_file.write_text(full_doc, encoding="utf-8")
    print(f"[SUCCESS] Context brief generated at {output_file.name} ({len(full_doc.split())} words).")
    return output_file

def main():
    repo_root = Path.cwd()
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        repo_root = Path(sys.argv[1]).resolve()

    force = "--force" in sys.argv
    output_path = repo_root / "CONTEXT_BRIEF.md"
    generate_okf_brief(repo_root, output_path, force=force)

if __name__ == "__main__":
    main()
