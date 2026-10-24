# Get Immediate Context (`get-immediate-context`)

An autonomous agent skill that rapidly orients an AI coding agent to any unfamiliar codebase—whether a single-project repository or a complex multi-package monorepo—at the start of every session before any coding task begins.

It eliminates blind exploration, prevents token exhaustion, maintains **persistent cross-session memory**, supports **privacy-filtered context injection**, and outputs a structured **Context Brief** formatted according to Google Cloud's [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing).

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Persistent Memory** | Context, architecture decisions, and domain invariants survive across sessions using git-tracked Open Knowledge Format (OKF) briefs and history ledgers. |
| 📊 **Progressive Disclosure** | 3-tiered memory retrieval (Index → Brief → Deep Dive) with upfront token cost visibility so you never overload your model's context window. |
| 🔍 **Smart Search (`mem-search`)** | Query project history using a deterministic 3-step skill: (1) Index keyword scan → (2) Review candidate matches → (3) Fetch full context. |
| 🖥️ **Local My Work** | Live requests, task progress, human handoffs, and a saved review queue at the local worker status endpoint/viewer. |
| 👥 **TeamBrain** | Optional shared workspace alongside My Work with team work lists, member attribution, and linked findings. Personal notes stay local. |
| 💻 **Claude Desktop & IDE Skill** | Interoperable across Claude Desktop, Google Antigravity, VS Code, and terminal CLI agents. |
| 🔒 **Privacy Control** | Use `<private>...</private>` tags and automated secret filters to exclude sensitive credentials and proprietary notes from storage. |
| ⚙️ **Context Configuration** | Fine-grained control (`.contextrc`) over what context sections get injected into the prompt. |
| 🤖 **Automatic Operation** | Triggers automatically on session start and git branch/commit shifts without manual intervention. |
| 🔗 **Citations** | Reference past observations and domain rules using persistent IDs (`[INV-001]`, `[OBS-042]`) linked to exact files and line numbers. |

---

## 🔄 Session Lifecycle & How It Works

The skill runs sequentially through **five automated phases** on every session start:

```
                  ┌───────────────────────────────┐
                  │         Session Start         │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │      Phase 1: Discovery       │
                  │ - Read README & top-level docs│
                  │ - Locate manifests & configs  │
                  │ - Single project vs Monorepo? │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │       Phase 2: Changes        │
                  │ - Read existing OKF frontmatter│
                  │ - Run plain git commands:     │
                  │   git rev-parse HEAD / status │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │      Phase 3: Hard Gate       │
                  │ Brief current with git state? │
                  └──────┬─────────────────┬──────┘
                         │                 │
                   [No / Stale]         [Yes]
                         │                 │
                         ▼                 │
              ┌─────────────────────┐      │
              │  Regenerate Brief   │      │
              │   in OKF format     │      │
              └──────────┬──────────┘      │
                         │                 │
                         └────────┬────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Phase 4: Business Logic Rules │
                  │ - Extract confirmed invariants│
                  │ - Assign citation IDs [INV-x] │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ Phase 5: Persistence & My Work│
                  │ - Update OKF brief & ledger   │
                  │ - Initialize Local My Work    │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │   Proceed to Requested Task   │
                  └───────────────────────────────┘
```

### Phase 1: Discovery (Repository Topology)
- **Identify Core Purpose**: Reads repository README or top-level architecture documentation.
- **Determine Topology**:
  - Checks workspace manifests (`pnpm-workspace.yaml`, `go.work`, `Cargo.toml [workspace]`, `lerna.json`, `pom.xml`, etc.).
  - Distinguishes between a single-project repository and a monorepo.
  - If a monorepo, maps each package/service individually, noting its directory, primary language, and purpose.
- **Map High-Signal Anchors**: Locates entry points (`main.go`, `src/index.ts`, `app.py`, etc.) and surveys top-level directory layout at shallow depth (depth 2–3).

### Phase 2: Changes (Git State Check)
- Evaluates the working copy against the recorded brief using **plain git commands only**:
  ```bash
  git rev-parse --abbrev-ref HEAD
  git rev-parse HEAD
  git status --porcelain
  ```
- Compares commit SHA, branch name, and uncommitted manifest/config changes against the OKF frontmatter of `CONTEXT_BRIEF.md`.
- If state has not changed, the brief is reused immediately, incurring **0 token regeneration cost**.

### Phase 3: Hard Gate (Integrity Checkpoint)
- **Strict Enforcement**: The agent cannot begin any implementation or refactoring task until `CONTEXT_BRIEF.md` exists and is confirmed current with git state.
- If missing, stale, or unverified: Regenerates the brief immediately.
- If an environment detail cannot be confirmed, records the gap explicitly under **Explicit Boundaries** rather than guessing.

### Phase 4: Business Logic & Citations
- Surfaces confirmed domain rules, input validation rules, state machines, and calculations.
- Assigns persistent **Citation IDs** (e.g. `[INV-001]`, `[OBS-015]`) citing exact file and line references (e.g. `packages/billing/billing/discounts.py:42`).

### Phase 5: Persistence & Local My Work
- Persists knowledge into `CONTEXT_BRIEF.md` and appends updates to history ledgers.
- Updates **Local My Work** tracking the active request, handoff checkpoints, and pending items in the review queue.

---

## 📊 Progressive Disclosure & Smart Search

### 3-Tier Progressive Disclosure

| Level | Scope | Approx Tokens | Injected Content |
|-------|-------|---------------|------------------|
| **Level 1: Index** | Metadata only | ~100 tokens | Repo name, git SHA, branch, package list |
| **Level 2: Brief (Default)** | OKF Context Brief | ~700–1,200 tokens | Purpose, architecture, run/test commands, confirmed invariants with citation IDs |
| **Level 3: Deep Dive** | Concept Files | On-demand | Specific package implementation details and historical session logs |

### Smart Search (`mem-search`) Workflow
When searching historical decisions, past bug resolutions, or architecture records:
1. **Index Scan**: Search the index using semantic or keyword search.
2. **Review Candidates**: Inspect matched observation headers and citation IDs with visible token estimates.
3. **Selective Fetch**: Retrieve only the specific observation blocks needed for the active task.

---

## 🔒 Privacy Controls & TeamBrain

### Privacy Shielding
- Anything surrounded by `<private>...</private>` tags is **completely redacted** before saving to the brief or memory store.
- Sensitive environment files (`.env*`, `*.pem`, `id_rsa`, API keys, tokens) are automatically skipped.

### TeamBrain (Collaborative Sharing)
- Enables multi-agent and human team coordination.
- Share verified invariants (`INV-*`) and package maps across team repositories.
- Includes author/agent attribution (`author: agent-session-id`, `timestamp: ISO-8601`).
- Personal work logs and private review notes remain strictly local.

---

## ⚙️ Context Configuration (`.contextrc`)

Configure the skill using a `.contextrc` file at the repository root:

```json
{
  "privacy_filter": true,
  "max_brief_words": 1500,
  "injection_level": 2,
  "team_sync": false,
  "exclude_patterns": ["legacy/**", "tmp/**"]
}
```

---

## 📄 Output: The OKF Context Brief

The brief is saved as [`CONTEXT_BRIEF.md`](file:///c:/Users/Farooq/Documents/AI Agent/get-immediate-context/CONTEXT_BRIEF.md) at the repository root in accordance with the **Open Knowledge Format (OKF)**:

```markdown
---
okf_version: "0.2"
type: ContextBrief
title: "<Repo Name> Context Brief"
description: "Repository orientation, architecture, and domain invariants."
git_commit: "<commit-sha>"
git_branch: "<branch-name>"
repo_type: single-project | monorepo
timestamp: "YYYY-MM-DDTHH:MM:SSZ"
tags: [context-brief, orientation, memory]
---

# <Repo Name> Context Brief

## 1. Purpose
[Summary of project purpose and problem domain.]

## 2. Stack & Dependencies
[Single project or per-package table for monorepos.]

## 3. Layout & Architecture
- **Entry Points**: `<path>`
- **Key Modules**: `<path>` - Responsibility

## 4. Run, Build & Test Commands
- **Install**: `<command>` | **Build**: `<command>` | **Test**: `<command>`

## 5. Configuration & Conventions
- Config sources, environment variables, code conventions.

## 6. Business Logic & Invariants (Citations)
- **[INV-001]**: Invariant description (`<file>:<line_or_symbol>`)

## 7. Explicit Boundaries (Uninspected Areas)
- List of uninspected files, legacy directories, or external integrations.

## 8. Local My Work & Review Queue
- **Active Task**: Current task objective
- **Handoff / Next**: Pending actions or items in review queue
```

---

## 💡 Example Usage

### 1. Orientation & Invariant Citation
The agent starts in `shop-engine` monorepo:
1. **Phases 1–3**: Verifies git SHA `7f2a1b9`, identifies `packages/api` and `packages/billing`.
2. **Phase 4**: Redacts `<private>` notes, cites invariant `[INV-001]`:
   > `[INV-001]`: Orders > 10 items receive tiered discounts, capped at 30% aggregate discount (`packages/billing/billing/discounts.py:42`).
3. **Phase 5**: Generates `CONTEXT_BRIEF.md` with OKF metadata and registers the active task in Local My Work.

### 2. Task Execution Against the Brief
**User Request**:
> *"In `packages/billing/billing/discounts.py`, add a volume discount tier of 15% for orders over 10 items without violating the discount cap."*

**Agent Action**:
1. Checks that `CONTEXT_BRIEF.md` matches `HEAD` (Hard Gate passed).
2. Targets only `discounts.py` and its test file.
3. Implements the 15% tier while upholding invariant `[INV-001]`.
4. Runs tests, verifies success, and marks the task complete in Local My Work.

---

## 🛠️ Python Scripts (Immediate Knowledge Fetching)

All standalone, dependency-free Python scripts live directly inside the skill folder under `.agents/skills/get-immediate-context/scripts/`:

### 1. `fetch_context.py` - Immediate Knowledge Extractor
Scans the repository, detects monorepo packages, checks git state, extracts confirmed domain invariants, strips sensitive `<private>` tags, and generates `CONTEXT_BRIEF.md`:
```bash
python .agents/skills/get-immediate-context/scripts/fetch_context.py

# Force regeneration even if git state has not changed:
python .agents/skills/get-immediate-context/scripts/fetch_context.py --force
```

### 2. `symbol_indexer.py` - Live Module & Symbol Line Locator
Extracts every module's functions and classes with exact line ranges (`L14-L85`) using native AST (Python) and regex (TypeScript, JS, Go, Rust, C#, Java). Updates live after every prompt in <50ms:
```bash
# Update Section 9 in CONTEXT_BRIEF.md with current line numbers:
python .agents/skills/get-immediate-context/scripts/symbol_indexer.py

# Instant locate: find where any function/class lives and on which line:
python .agents/skills/get-immediate-context/scripts/symbol_indexer.py --locate sanitize
```

### 3. `mem_search.py` - 3-Step Smart Project Memory Search
Query past decisions, invariants, or configuration keywords with token estimates before loading:
```bash
# Step 1 & 2: Preview matched candidates with token cost estimates
python .agents/skills/get-immediate-context/scripts/mem_search.py "discount"

# Step 3: Fetch full details for a chosen citation ID
python .agents/skills/get-immediate-context/scripts/mem_search.py --fetch INV-001
```

### 4. `progressive_disclosure.py` - Layered Context Exporter
Extracts context at 3 discrete levels with token metrics for prompt injection:
```bash
# Level 1: Index (~100 tokens)
python .agents/skills/get-immediate-context/scripts/progressive_disclosure.py 1

# Level 2: Standard OKF Brief (~800 tokens)
python .agents/skills/get-immediate-context/scripts/progressive_disclosure.py 2

# Level 3: Deep Dive with topology
python .agents/skills/get-immediate-context/scripts/progressive_disclosure.py 3
```

### 5. `code_embeddings.py` - Ultra-Lightweight Code Embeddings & Semantic Search
Generates 256-dimensional dense vector embeddings for code chunks (0-download, runs offline in <1s) or neural embeddings via fastembed ONNX:
```bash
# Generate/refresh embeddings for all code chunks in the repository:
python .agents/skills/get-immediate-context/scripts/code_embeddings.py --generate

# Semantic Code Search: Find relevant functions/classes by concept or intent:
python .agents/skills/get-immediate-context/scripts/code_embeddings.py --search "sanitize user input and tokens"

# Check index dimensions, total chunks, and storage stats:
python .agents/skills/get-immediate-context/scripts/code_embeddings.py --info
```

---

## 📂 Installation & Setup

Drop the skill into your project's `.agents/skills` directory:

```text
your-repository/
├── .agents/
│   └── skills/
│       └── get-immediate-context/
│           ├── SKILL.md
│           ├── scripts/
│           │   ├── fetch_context.py
│           │   ├── symbol_indexer.py
│           │   ├── code_embeddings.py
│           │   ├── mem_search.py
│           │   └── progressive_disclosure.py
│           └── references/
│               ├── open-knowledge-format-spec.md
│               ├── progressive-disclosure-guide.md
│               ├── code-embeddings-architecture.md
│               ├── monorepo-topology-guide.md
│               └── privacy-and-compliance.md
```

Compatible with:
- **Google Antigravity**
- **Claude Desktop & Claude Code**
- **dotnet/skills** runtimes
- Any agent runtime adhering to the [Agent Skills Specification](https://agentskills.io/specification)

---

## 📚 References

### External Specifications & Guides
- [Google Cloud Blog: How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [Claude-Mem Architecture & My Work Guide](https://docs.claude-mem.ai/usage/my-work)
- [Agent Skills Specification](https://agentskills.io/specification)

### Bundled Reference Documentation
- [`references/open-knowledge-format-spec.md`](.agents/skills/get-immediate-context/references/open-knowledge-format-spec.md): Complete specification of OKF v0.2.
- [`references/progressive-disclosure-guide.md`](.agents/skills/get-immediate-context/references/progressive-disclosure-guide.md): 3-tier token budgeting & context injection model.
- [`references/code-embeddings-architecture.md`](.agents/skills/get-immediate-context/references/code-embeddings-architecture.md): Subword feature hashing & cosine vector search.
- [`references/monorepo-topology-guide.md`](.agents/skills/get-immediate-context/references/monorepo-topology-guide.md): Matrix of monorepo manifests across languages.
- [`references/privacy-and-compliance.md`](.agents/skills/get-immediate-context/references/privacy-and-compliance.md): Secret detection regexes and `<private>` filtering.
