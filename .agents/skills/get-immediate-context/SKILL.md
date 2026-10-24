---
name: get-immediate-context
description: Rapidly orients an AI agent to an unfamiliar single-project repository or monorepo at session start before any task begins. Inspects manifests, git status, layout, and domain rules to create or verify an under-1500-word context brief formatted according to the Open Knowledge Format (OKF) at the repo root. USE FOR: session start, unfamiliar codebases, repository orientation, repo onboarding, mapping monorepos, extracting domain business logic, checking stale context briefs. DO NOT USE FOR: task-specific code generation, refactoring, or broad codebase-wide file reading.
---

# Get Immediate Context

Orient rapidly to an unfamiliar codebase at the start of any session before beginning task work. This skill inspects repository structures, manifests, git status, and core business rules across any language or stack, establishing a factual context brief saved as `CONTEXT_BRIEF.md` at the repository root formatted according to the **Open Knowledge Format (OKF)**.

## When to Use

- Starting a new agent session in any repository before any task begins
- Onboarding to an unfamiliar codebase or monorepo without blind exploration
- Verifying whether existing codebase documentation matches current git state
- Identifying distinct packages, dependencies, and entry points in a monorepo
- Extracting confirmed domain invariants and business rules prior to implementing features or fixes
- Publishing or standardizing repository knowledge in an open, vendor-neutral format consumable by humans and any AI agent

## When Not to Use

- Executing specific refactoring, bug fixes, or code edits once context is established (use task-specific implementation workflows)
- Deep full-codebase code reviews or lint audits
- Arbitrary full-text reads of every source file in the repository

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `repo_root` | Yes | Path to the repository root directory (where `.git` resides or workspace root) |
| `task_description` | Optional | The user's intended task to help guide selective-depth reads after orientation |
| `brief_filename` | Optional | Filename for the markdown brief (defaults to `CONTEXT_BRIEF.md` at repository root) |

## Trigger Conditions and Session Lifecycle

This skill triggers at **every session start** in a repository prior to executing any user prompt or modification task. The agent must complete the four phases in order and confirm the hard gate before proceeding to task execution.

```
Session Start ──> Phase 1: Discovery
                       │
                  Phase 2: Changes (Git State Check)
                       │
                  Phase 3: Hard Gate ──[Stale/Missing]──> Regenerate Brief (OKF Format)
                       │                                         │
                  [Valid & Current] <────────────────────────────┘
                       │
                  Phase 4: Business Logic Extraction
                       │
                  Context Gathered ──> Proceed to Task
```

---

## Session Workflow

Execute these four phases sequentially:

### Phase 1: Discovery (Repository Topology)

Determine repository type and map high-signal anchors without reading entire directories:

1. **Locate Workspace Root and Docs**: Read `README.md`, `README.*`, or architecture docs in root. Extract the stated purpose of the project.
2. **Determine Architecture (Single Project vs Monorepo)**:
   - Check for workspace configuration files: `pnpm-workspace.yaml`, `lerna.json`, `rush.json`, `package.json` with `workspaces`, `Cargo.toml` with `[workspace]`, `go.work`, `settings.gradle` / `pom.xml` modules, or directories like `packages/`, `services/`, `apps/`, `libs/`.
   - If monorepo: list each distinct service/package, identify its directory, primary language, and purpose.
   - If single project: identify the central manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, etc.).
3. **Map Entry Points and Structure**:
   - Locate main entry points (e.g., `main.go`, `src/index.ts`, `app.py`, `Program.cs`, `cmd/`).
   - Run a shallow top-level tree/listing (max depth 2-3) to establish key modules and directory boundaries.

### Phase 2: Changes (Git State Verification)

Compare current working copy state against the recorded brief using **plain git commands only**:

1. **Read Existing Brief Header**: Check if `CONTEXT_BRIEF.md` exists at repository root. Extract its OKF YAML frontmatter (`git_commit`, `git_branch`, `timestamp`).
2. **Execute Git Commands**:
   ```bash
   git rev-parse --abbrev-ref HEAD
   git rev-parse HEAD
   git status --porcelain
   ```
3. **Evaluate Freshness**:
   - If `HEAD` matches recorded SHA, branch matches, and manifests/configuration files have no uncommitted changes in `git status`: **Brief is current**. Skip full regeneration.
   - If `HEAD` differs, branch differs, or any build/manifest/source configuration has changed: **Brief is stale**. Trigger Phase 3 regeneration.
   - If git is not installed or directory is not a git repository: Record this limitation explicitly in the brief and proceed with discovery data.

### Phase 3: Hard Gate (Enforcement Checkpoint)

Before starting any task work:
- Confirm that `CONTEXT_BRIEF.md` exists at the repository root, conforms to Open Knowledge Format (YAML frontmatter + Markdown body), and matches current git state.
- If missing, stale, or unverified: **Regenerate the brief immediately**.
- Do not make assumptions or start writing code with an unverified or absent brief.
- Where a detail cannot be confirmed from files, record the uncertainty explicitly in the brief under "Explicit Boundaries" rather than guessing.

### Phase 4: Business Logic Extraction

Surface the actual domain rules and behaviors enforced by the codebase:

1. **Locate Core Domain Areas**: Focus on domain models, entity validators, state machines, policy engines, pricing/calculation routines, or permission matrices.
2. **Identify Invariants**:
   - Input validation limits and requirements
   - Allowable state transitions (e.g., `PENDING` -> `APPROVED` -> `FULFILLED`)
   - Calculation rules, fees, permissions, or access gates
3. **Cite Exact Files**: For every business rule documented, cite the defining file and line/symbol reference (e.g., `src/billing/tier.py:calculate_discount`).
4. **Flag Ambiguities**: If a rule cannot be determined conclusively without runtime inspection or missing schemas, note it as an open question.

---

## Context Gathering Strategy

To remain fast, lightweight, and prevent context bloat, sequence information retrieval using these principles:

### 1. Triage Order
Start strictly with the highest-signal sources in this order:
1. `README.md` and repository-level docs
2. Primary manifests and package definitions (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `*.csproj`)
3. Workspace definitions for monorepos (`pnpm-workspace.yaml`, `go.work`, `Cargo.toml [workspace]`)
4. Build, test, and container scripts (`Makefile`, `Dockerfile`, `.github/workflows/`, task runners)
5. Top-level directory layout (shallow depth)
6. Recent commit history (`git log -n 5 --oneline`) to reveal active areas

### 2. Breadth Before Depth
- Scan symbols, module exports, file listings, and class/function signatures before opening file bodies.
- Never read all files in a folder. List files first, identify load-bearing files, and read only targeted declarations.

### 3. Selective Depth Matrix

| Context Need | Depth Level | Technique |
|--------------|-------------|-----------|
| Architecture overview | Breadth | Top-level directory listing and workspace manifests |
| Module interfaces | Signatures only | Class/function headers, exported interfaces, types |
| Entry points & task files | Full contents | Complete file reads of `main.*`, central routers, or files directly modified |
| Inter-module relations | Dependency graph | `import` / `require` / `use` statements at top of files |
| Active development | Git commits | `git log -n 5 --oneline -- <path>` |
| Domain intent | Comments & docstrings | Targeted docstrings and assertions inside domain models |

### 4. Task-Driven Scoping
When a specific task is provided:
- Treat files outside the task's import path as signature-only.
- Read full file contents **only** for files directly involved in the change or tests validating that behavior.
- Constrain exploration to the relevant service or package in a monorepo.

### 5. Stopping Criteria
**Stop reading immediately** when you can answer these five points with confidence:
1. What does this project or service do?
2. What stack and test runners are used?
3. Where are the entry points and key modules?
4. What are the build/run/test commands?
5. What are the key domain invariants governing the task?
Do not continue scanning for general completeness.

### 6. Verification Over Inference
- Do not infer a framework or tool from a folder name alone (e.g., a `tests/` folder does not prove pytest is used; confirm via `pyproject.toml` or `pytest.ini`).
- Confirm commands by inspecting scripts, package manifests, or CI workflows.

---

## Output Specification: Open Knowledge Format (OKF) Brief

The brief is saved as a plain markdown file named `CONTEXT_BRIEF.md` directly at the repository root.

### Conformance to Open Knowledge Format (OKF)
In accordance with the [Open Knowledge Format specification](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing), the document treats context as a portable, vendor-neutral, version-controlled asset:
- **Format, Not a Platform**: No proprietary SDK or database required; just Markdown and YAML frontmatter.
- **YAML Frontmatter**: Standard headers housing structured machine-readable metadata (`okf_version`, `type`, `title`, `description`, `git_commit`, `git_branch`, `repo_type`, `timestamp`, `tags`).
- **Markdown Body**: Clean, readable headings and links that both human engineers and AI models can traverse.

### Word Budget Rules
- **Simple Single-Project Repositories**: Aim for under **500 words**.
- **Complex or Multi-Service Monorepos**: Scale up as necessary, but strictly capped at **1,500 words**.
- Prioritize factual completeness across all required sections over aggressive brevity, but avoid filler text, boilerplate explanations, and long code copies.

### OKF Context Brief Template

```markdown
---
okf_version: "0.2"
type: ContextBrief
title: "<Repository Name> Context Brief"
description: "High-signal repository orientation, architecture, and domain invariants."
git_commit: "<commit-sha>"
git_branch: "<branch-name>"
repo_type: single-project | monorepo
timestamp: "YYYY-MM-DDTHH:MM:SSZ"
tags:
  - context-brief
  - orientation
  - architecture
---

# <Repository Name> Context Brief

## 1. Purpose
[1-2 sentences summarizing what problem this software solves and its primary end-users.]

## 2. Stack & Dependencies
[For Single Project: Primary language, runtime, key frameworks, and core libraries.]
[For Monorepo: Table or list broken down per package/service.]
- **<Service/Package A>**: <Language/Version>, <Framework>, <Core Dependencies>
- **<Service/Package B>**: <Language/Version>, <Framework>, <Core Dependencies>

## 3. Layout & Architecture
- **Entry Points**: `<path>` (Role)
- **Key Modules**:
  - `<path>`: Summary of responsibility
- **Inter-Package / Module Relationships**: How components communicate (e.g. gRPC, HTTP, shared lib).

## 4. How to Run, Build, and Test
- **Install**: `<command>`
- **Build**: `<command>`
- **Test**: `<command>`
- **Run / Dev**: `<command>`

## 5. Configuration & Conventions
- **Configuration Files**: `<file-paths>` and environment variable sources
- **Code Conventions**: Noteworthy style, typing conventions, or architectural patterns confirmed by code

## 6. Business Logic & Invariants
- **[Rule 1]**: Explanation of domain rule (Source: `<file>:<symbol_or_line>`)
- **[Rule 2]**: Validation rule or state transition constraint (Source: `<file>:<symbol_or_line>`)

## 7. Explicit Boundaries (Uninspected Areas)
- [List specific directories, legacy packages, or third-party integrations not inspected during this pass]
```

---

## Usage Example

### Walkthrough: Monorepo Orientation and Targeted Task

#### 1. Repository State & Discovery
The agent is launched in an unfamiliar monorepo `shop-engine`.
- Agent inspects root: finds `pnpm-workspace.yaml`, `README.md`, and directories `packages/api` and `packages/billing`.
- Agent checks `git rev-parse HEAD` -> `7f2a1b9` on `main`. No previous `CONTEXT_BRIEF.md` exists.
- Agent gathers high-signal context and generates `CONTEXT_BRIEF.md` at root in OKF format:

```markdown
---
okf_version: "0.2"
type: ContextBrief
title: "Shop Engine Context Brief"
description: "Monorepo orientation brief covering API and Billing services."
git_commit: "7f2a1b9"
git_branch: "main"
repo_type: monorepo
timestamp: "2026-10-24T10:00:00Z"
tags:
  - context-brief
  - orientation
  - monorepo
---

# Shop Engine Context Brief

## 1. Purpose
E-commerce engine managing product catalog queries and customer checkout billing.

## 2. Stack & Dependencies
- **`packages/api`**: TypeScript (Node.js 20), Express 4, Prisma ORM.
- **`packages/billing`**: Python 3.11, FastAPI, Pydantic v2, Stripe SDK.

## 3. Layout & Architecture
- `packages/api/src/server.ts`: HTTP API entry point for store client.
- `packages/billing/billing/main.py`: Internal billing microservice called via HTTP from API service.
- `packages/billing/billing/discounts.py`: Domain logic for customer discounts and voucher validation.

## 4. How to Run, Build, and Test
- **Install**: `pnpm install` (root)
- **Build**: `pnpm build` (runs turbo build across all packages)
- **Test (API)**: `pnpm --filter api test` (Jest)
- **Test (Billing)**: `cd packages/billing && pytest`

## 5. Configuration & Conventions
- `.env.example` defines required `STRIPE_KEY` and `DATABASE_URL`.
- Pydantic models enforce strict camelCase aliasing for public responses.

## 6. Business Logic & Invariants
- Orders exceeding 10 items receive tiered discounts, but total discount cannot exceed 30% (`packages/billing/billing/discounts.py:apply_order_discount`).
- Billing accounts must be in `ACTIVE` state before applying vouchers (`packages/billing/billing/models.py:AccountState`).

## 7. Explicit Boundaries (Uninspected Areas)
- `packages/api/src/legacy/` was not inspected.
- Cloud deployment scripts in `.github/workflows/deploy.yml` were not examined.
```

#### 2. Applying Context to a Coding Task
**User Prompt**:
> "In `packages/billing/billing/discounts.py`, add a volume discount tier of 15% for orders over 10 items, but ensure the aggregate discount never exceeds the 30% cap."

**Agent Execution**:
1. **Hard Gate Passed**: Agent inspects `CONTEXT_BRIEF.md`; parses the OKF frontmatter (`git_commit: "7f2a1b9"`), confirms it matches current HEAD, and validates integrity.
2. **Task-Driven Scoping**: Agent targets only `packages/billing/billing/discounts.py` and `packages/billing/tests/test_discounts.py`. No other packages or files are read.
3. **Change Implementation**:
   - Opens `packages/billing/billing/discounts.py`.
   - Modifies `apply_order_discount` to incorporate the 15% tier when item count > 10.
   - Preserves the confirmed invariant: `assert total_discount <= 0.30` or `min(calculated_discount, 0.30)` as cited in Section 6.
4. **Verification**:
   - Runs `cd packages/billing && pytest tests/test_discounts.py`. All tests pass.

---

## Validation Checklist

Before concluding the skill run and proceeding with a task, verify:

- [ ] `CONTEXT_BRIEF.md` is present at the repository root
- [ ] Brief conforms to Open Knowledge Format (starts with valid YAML frontmatter containing `okf_version`, `type`, `title`, `description`, `git_commit`, `git_branch`, `timestamp`)
- [ ] Monorepos list each package/service individually with its respective stack
- [ ] Build, run, and test commands are confirmed by configuration/scripts, not guessed
- [ ] Every business rule lists the exact file path where it is enforced
- [ ] Explicit Boundaries section lists all uninspected areas
- [ ] Word count is strictly under 1,500 words (and under 500 words for simple repos)
- [ ] No speculative or unverified claims are present

---

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Missing YAML frontmatter | Follow OKF standard: prefix the markdown brief with parseable YAML frontmatter containing `type: ContextBrief` and version. |
| Reading all files recursively | Restrict file reads to top-level manifests, entry points, and task-specific paths. |
| Guessing test or build tools | Check package manifests (`scripts`), `Makefile`, or CI workflows for explicit commands. |
| Treating a monorepo as a single stack | Identify each package directory and map its individual runtime, language, and dependencies. |
| Stale brief after git checkout or pull | Re-run git checks on session start; parse frontmatter `git_commit` and regenerate if HEAD changed. |
| Inventing business logic from names | Only cite domain invariants directly confirmed in code, validators, or docstrings with file citations. |
| Leaving out uninspected areas | Always include Section 7 ("Explicit Boundaries") so the agent knows where knowledge ceases. |

---

## References

- [Google Cloud Blog: How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [Agent Skills Specification](https://agentskills.io/specification)
