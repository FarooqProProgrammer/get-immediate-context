---
okf_version: "0.2"
type: ContextBrief
title: "get-immediate-context Context Brief"
description: "High-signal repository orientation, architecture, and domain invariants."
git_commit: "da10499795e1ea5b31c0188649c974190943f472"
git_branch: "master"
repo_type: single-project
timestamp: "2026-10-24T17:29:33Z"
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
| `.agents/skills/get-immediate-context/scripts/call_graph.py` | `def extract_file_imports()` | `L49-L77` |
| `.agents/skills/get-immediate-context/scripts/call_graph.py` | `def build_dependency_graph()` | `L79-L107` |
| `.agents/skills/get-immediate-context/scripts/call_graph.py` | `def analyze_blast_radius()` | `L109-L129` |
| `.agents/skills/get-immediate-context/scripts/call_graph.py` | `def main()` | `L131-L161` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def tokenize_code()` | `L41-L52` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def compute_lightweight_embedding()` | `L54-L78` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def cosine_similarity()` | `L80-L84` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def get_neural_embeddings()` | `L91-L101` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def chunk_code_file()` | `L106-L156` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def generate_code_embeddings()` | `L161-L209` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def search_code_embeddings()` | `L214-L256` |
| `.agents/skills/get-immediate-context/scripts/code_embeddings.py` | `def main()` | `L258-L285` |
| `.agents/skills/get-immediate-context/scripts/diff_impact.py` | `def extract_invariants_from_brief()` | `L22-L39` |
| `.agents/skills/get-immediate-context/scripts/diff_impact.py` | `def parse_git_diff()` | `L41-L68` |
| `.agents/skills/get-immediate-context/scripts/diff_impact.py` | `def check_diff_impact()` | `L70-L115` |
