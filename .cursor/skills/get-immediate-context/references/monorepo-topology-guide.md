# Monorepo Topology & Workspace Manifests Reference

## 1. Overview

A monorepo holds multiple distinct packages, services, or applications in a single repository. Unlike single-project repositories where a root manifest defines everything, monorepos have distinct stacks, runtimes, and dependencies per subproject.

---

## 2. Workspace Manifest Matrix

| Ecosystem / Tool | Manifest File | Configuration Key | Example Syntax |
|---|---|---|---|
| **pnpm** | `pnpm-workspace.yaml` | `packages:` | `packages:\n  - 'apps/*'\n  - 'packages/*'` |
| **npm / Yarn** | `package.json` | `"workspaces": [...]` | `{"workspaces": ["packages/*", "client", "server"]}` |
| **Rust / Cargo** | `Cargo.toml` | `[workspace] members = [...]` | `[workspace]\nmembers = ["crates/*", "libs/*"]` |
| **Go** | `go.work` | `use (...)` | `go 1.22\n\nuse (\n  ./api\n  ./worker\n)` |
| **Lerna** | `lerna.json` | `"packages": [...]` | `{"packages": ["packages/*"]}` |
| **Gradle** | `settings.gradle(.kts)` | `include '...'` | `include 'core', 'web-api', 'shared'` |
| **Bazel** | `WORKSPACE` / `MODULE.bazel` | Sub-packages with `BUILD` | Multi-language BUILD rules |

---

## 3. Dynamic Discovery Algorithm (Zero-Assumption)

When no explicit workspace manifest exists (or in addition to it):
1. **Directory Traversal**: Walk subdirectories up to 3 levels deep.
2. **Directory Pruning**: Immediately prune vendor and artifact directories:
   - `.git`, `node_modules`, `.venv`, `venv`, `target`, `dist`, `build`, `vendor`, `__pycache__`.
3. **Manifest Inspection**: Check if the subdirectory contains any primary manifest:
   - `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `setup.py`, `composer.json`, `Gemfile`.
4. **Classification**:
   - If $\ge 2$ subdirectories contain independent manifests: classify as **Monorepo**.
   - If only root contains manifests: classify as **Single Project**.
