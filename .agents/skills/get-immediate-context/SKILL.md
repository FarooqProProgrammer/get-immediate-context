---
name: get-immediate-context
description: Rapidly orients an AI agent at session start with persistent cross-session memory, progressive disclosure, smart search, and privacy controls. Generates and verifies an Open Knowledge Format (OKF) context brief under 1500 words at repo root. USE FOR: session start, unfamiliar codebases, repository orientation, persistent memory, team context sharing, privacy-filtered context injection. DO NOT USE FOR: task-specific code generation, refactoring, or broad codebase-wide file reading.
---

# Get Immediate Context

An autonomous orientation and memory skill that establishes factual, persistent codebase context across sessions. It surveys repository topology, verifies git state, enforces privacy controls, extracts domain business rules with citation IDs, and maintains an Open Knowledge Format (OKF) context brief (`CONTEXT_BRIEF.md`) at the repository root.

## Key Capabilities

- 🧠 **Persistent Memory**: Context and domain insights survive across sessions via OKF logs and local briefs.
- 📊 **Progressive Disclosure**: 3-tiered memory retrieval (Index → Brief → Deep Dive) with token cost visibility.
- 🔍 **Smart Search (`mem-search`)**: 3-step structured retrieval over project history (Index → Match → Fetch).
- 🖥️ **Local My Work**: Tracks live requests, active progress, human handoffs, and review queues.
- 👥 **TeamBrain**: Collaborative workspace sharing verified findings and package maps with member attribution while keeping personal notes isolated.
- 💻 **Desktop & CLI Interoperability**: Seamlessly accessible from IDE agents, Claude Desktop, and CLI tooling.
- 🔒 **Privacy Control**: Strips content bounded by private markers (`<private>...</private>`) and secrets from storage.
- ⚙️ **Context Configuration**: Fine-grained controls (`.contextrc`) defining what sections get injected into prompts.
- 📍 **Live Module & Line Location Map**: AST & regex indexer tracking where every class/function lives (`file:line-range`), updating automatically after every prompt/edit.
- ⚡ **Lightweight Code Embeddings**: 256-dim vectorizer & cosine similarity search across functions, classes, and code chunks.
- 🤖 **Automatic Operation**: Executes automatically on session start without manual invocation.
- 🔗 **Citations**: Attaches persistent observation IDs (e.g., `OBS-001`, `INV-012`) linking facts to files, lines, and commits.

## When to Use

- Session start in any single-project or monorepo to establish instant orientation
- Maintaining long-lived project memory, architecture decisions, and domain invariants across sessions
- Querying past project decisions, bug investigations, and review queues via smart search
- Sharing curated team knowledge without leaking personal or sensitive credentials

## When Not to Use

- Writing task-specific feature code or refactoring after orientation is complete
- Whole-codebase bulk file dumping into active context

## Inputs & Configuration

The skill reads configuration from `.contextrc` (JSON/YAML) or uses sensible defaults:

| Input / Setting | Type | Default | Description |
|-----------------|------|---------|-------------|
| `repo_root` | Path | Working directory | Root directory containing `.git` or workspace manifests |
| `privacy_filter` | Boolean | `true` | Automatically strip `<private>` tags, API keys, and `.env` data |
| `max_brief_words` | Integer | `1500` | Word ceiling for generated brief (<500 for single projects) |
| `team_sync` | Boolean | `false` | Enable TeamBrain synchronization for shared findings |
| `injection_level` | Integer (1-3) | `2` | Progressive disclosure level (1=Index, 2=Brief, 3=Deep Dive) |

## Bundled Helper Scripts

Executable Python 3 scripts (standard library only) are bundled under `scripts/`:
- `scripts/fetch_context.py`: Immediately inspects the codebase, enforces privacy, and writes/refreshes `CONTEXT_BRIEF.md`.
- `scripts/symbol_indexer.py`: Live module & symbol location mapper (Python AST + polyglot regex) indexing exact line numbers (`L42-L80`), updated after every edit/prompt.
- `scripts/mem_search.py`: 3-step progressive memory search across observations and brief records.
- `scripts/progressive_disclosure.py`: Exports layered context (Level 1, 2, or 3) with token count estimations.
- `scripts/code_embeddings.py`: Ultra-lightweight 256-dim code embedding generator and semantic search engine (offline & fast).

---

## Session Workflow

On every session start, the skill runs five automated phases:

```
Session Start ──> 1. Discovery ──> 2. Changes (Git Check) ──> 3. Hard Gate
                                                                    │
      Proceed to Task <── 5. Persistence <── 4. Business Logic <────┘
                          & My Work
```

### Phase 1: Discovery (Repository Topology)
1. Read `README.md`, manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`), and workspace configs (`pnpm-workspace.yaml`, `go.work`).
2. Classify as **Single Project** or **Monorepo**; map every package, its stack, entry points, and purpose.

### Phase 2: Changes (Git State Check)
1. Read OKF YAML frontmatter in `CONTEXT_BRIEF.md` (`git_commit`, `git_branch`, `timestamp`).
2. Run plain git checks: `git rev-parse HEAD`, `git rev-parse --abbrev-ref HEAD`, `git status --porcelain`.
3. If commit SHA and branch match and configs are clean: reuse existing memory (0 token regeneration cost). If changed: flag as stale.

### Phase 3: Hard Gate (Verification Checkpoint)
- Confirm valid, current brief exists before executing any task.
- If missing or stale: regenerate immediately.
- If directory is unversioned or details cannot be confirmed: log gaps under **Explicit Boundaries** rather than guessing.

### Phase 4: Business Logic Extraction & Citations
1. Locate core domain validators, state machines, and calculations.
2. Assign **Observation IDs** (e.g., `[INV-001]`, `[OBS-023]`) citing exact file and line references (e.g., `packages/billing/billing/discounts.py:42`).
3. State only what code confirms; flag ambiguous logic.

### Phase 5: Persistence & Local My Work
1. Update `CONTEXT_BRIEF.md` and append any new observations to the session ledger.
2. Initialize or refresh **Local My Work** tracking current active request, next steps, and review queue items.

---

## Progressive Disclosure & Smart Search

### 3-Tier Progressive Disclosure

| Level | Scope | Approx Tokens | What is Injected |
|-------|-------|---------------|------------------|
| **1: Index** | Metadata only | ~100 tokens | Project name, repo type, git SHA, package list |
| **2: Brief (Default)** | OKF Context Brief | ~700-1,200 tokens | Architecture, run/test commands, conventions, confirmed invariants |
| **3: Deep Dive** | Concept Files | On-demand | Specific package implementation details, full history logs |

### Smart Search (`mem-search`) Workflow
When querying past project history or architectural decisions:
1. **Index Scan**: Search index for target keywords, observation tags, or commit messages.
2. **Review Candidates**: Inspect matched observation headers and citation IDs with token costs displayed.
3. **Selective Fetch**: Retrieve only the specific observation blocks needed for the active task.

---

## Privacy Control & TeamBrain

### Privacy Isolation
- Any block wrapped in `<private>...</private>` markers is **strictly redacted** before saving to `CONTEXT_BRIEF.md` or memory ledgers.
- Automatically ignores `.env*`, `*.pem`, `id_rsa`, credentials, and bearer tokens.
- Personal handoff notes and scratchpads remain in local session storage.

### TeamBrain Collaboration
- Curated domain invariants (`INV-*`) and package maps can be exported to a shared team ledger.
- Each contribution includes member/agent attribution (`author: agent-session-id`, `verified_at: timestamp`).
- Personal work queues and private notes stay local.

---

## Output Specification: OKF Context Brief

The brief is saved at the repository root as `CONTEXT_BRIEF.md`.

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

## 9. Live Code Location & Symbol Index (Module -> File : Line)
| Module / File | Key Symbol | Line Location |
|---|---|---|
| `<module_path>` | `class ...` / `def ...()` | `L<start>-L<end>` |
```

---

## Usage Example

### Walkthrough: Monorepo with Privacy & Invariant Citations

1. **Session Start**: Agent starts in `shop-engine` monorepo.
2. **Discovery & Git Check**: Verifies `pnpm-workspace.yaml`, git SHA `7f2a1b9`.
3. **Privacy Filter**: Identifies `<private>AWS_SECRET_KEY=...</private>` in local notes and redacts it completely.
4. **Brief Generation**: Outputs `CONTEXT_BRIEF.md` with OKF frontmatter and citation `[INV-001]`:
   > `[INV-001]`: Orders > 10 items receive tiered discounts, total discount capped at 30% (`packages/billing/billing/discounts.py:42`).
5. **Targeted Task**:
   - User prompt: *"Add a 15% discount tier for orders > 10 items in `discounts.py` without violating the discount cap."*
   - Agent inspects only `discounts.py`, applies tier, preserves invariant `[INV-001]`, and records progress in Local My Work.

---

## Validation Checklist

- [ ] `CONTEXT_BRIEF.md` exists at repo root with valid OKF YAML frontmatter
- [ ] Git SHA, branch, and timestamp match current working copy
- [ ] All sensitive sections marked with private tags are completely excluded
- [ ] Business logic statements include observation citation IDs with exact file paths
- [ ] Word count is under 1,500 words (<500 words for simple projects)
- [ ] Uninspected paths are explicitly recorded under Boundaries

---

## References

### External Specifications & Guides
- [Google Cloud Blog: How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [Claude-Mem Architecture & My Work Guide](https://docs.claude-mem.ai/usage/my-work)
- [Agent Skills Specification](https://agentskills.io/specification)

### Bundled Reference Documentation
- [Open Knowledge Format Specification](references/open-knowledge-format-spec.md)
- [Progressive Disclosure & Token Budgeting Guide](references/progressive-disclosure-guide.md)
- [Lightweight Code Embeddings Architecture](references/code-embeddings-architecture.md)
- [Monorepo Topology & Workspace Manifests](references/monorepo-topology-guide.md)
- [Privacy, Secrets Redaction, and Compliance](references/privacy-and-compliance.md)
