---
okf_version: "0.2"
type: ContextBrief
title: "get-immediate-context Context Brief"
description: "High-signal repository orientation, architecture, and domain invariants."
git_commit: "fc0479af2fc4e74378440cf6578cbca64f44bf15"
git_branch: "master"
repo_type: single-project
timestamp: "2026-10-24T17:04:54Z"
tags: [context-brief, orientation, architecture]
---

# get-immediate-context Context Brief

## 1. Purpose
Software project codebase.

## 2. Stack & Dependencies
- **`get-immediate-context`** (`.`): Unknown Stack

## 3. Layout & Architecture
- **Repository Type**: Single Project
- **Entry Points**:
  - Standard package entry points

## 4. Run, Build & Test Commands
- **Install**: `N/A`
- **Build**: `N/A`
- **Test**: `N/A`
- **Run / Dev**: `N/A`

## 5. Configuration & Conventions
- Configuration sources identified dynamically from workspace manifests.
- Package boundaries and dependency structures isolated.

## 6. Business Logic & Invariants (Citations)
- No strict invariant assertions extracted in preliminary scan.

## 7. Explicit Boundaries (Uninspected Areas)
- External network resources and deployment workflows were not executed.
- Vendor directories (node_modules, target, .venv, etc.) excluded from analysis.

## 8. Local My Work & Review Queue
- **Active Task**: Repository orientation completed.
- **Status**: Verified and ready for prompt execution.

## 9. Live Code Location & Symbol Index (Module -> File : Line)
| Module / File | Key Symbol | Line Location |
|---|---|---|
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def sanitize_text()` | `L36-L41` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def get_git_info()` | `L46-L70` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def get_directory_stack()` | `L97-L113` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def parse_workspace_patterns()` | `L115-L207` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def discover_project_structure()` | `L209-L290` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def find_entry_points()` | `L292-L311` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def find_test_commands()` | `L313-L358` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def extract_invariants()` | `L365-L399` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def generate_okf_brief()` | `L404-L530` |
| `.agents/skills/get-immediate-context/scripts/fetch_context.py` | `def main()` | `L532-L539` |
| `.agents/skills/get-immediate-context/scripts/mem_search.py` | `def search_memory()` | `L21-L67` |
| `.agents/skills/get-immediate-context/scripts/mem_search.py` | `def main()` | `L69-L88` |
| `.agents/skills/get-immediate-context/scripts/progressive_disclosure.py` | `def get_token_count()` | `L21-L22` |
| `.agents/skills/get-immediate-context/scripts/progressive_disclosure.py` | `def export_progressive_context()` | `L24-L67` |
| `.agents/skills/get-immediate-context/scripts/progressive_disclosure.py` | `def main()` | `L69-L78` |
