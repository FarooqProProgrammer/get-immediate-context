# Open Knowledge Format (OKF) Specification Reference

Based on the [Google Cloud Open Knowledge Format Specification](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing).

## 1. Overview & Philosophy

The **Open Knowledge Format (OKF)** is a lightweight, vendor-neutral specification designed to standardize how context, metadata, and curated domain knowledge are shared between humans, data systems, and autonomous AI agents.

### Core Principles
- **Format, Not a Platform**: No proprietary SDKs, databases, or runtime lock-in. A compliant OKF bundle is plain text that can be committed to Git, edited in any markdown viewer, or interpreted by any LLM.
- **Just Markdown**: Human-readable, GitHub-renderable, searchable.
- **Just Files**: Directory-based hierarchy that integrates seamlessly with Git version control.
- **Just YAML Frontmatter**: Structured metadata headers at the top of every document provide machine-parseable fields for agent indexing and query filtering.

---

## 2. Specification Conformance (v0.2)

### Required Frontmatter Fields for a Concept/Brief
Every non-reserved `.md` file must begin with valid YAML frontmatter containing:

| Field | Type | Required | Description |
|---|---|---|---|
| `okf_version` | String | Yes | Version of the OKF spec (e.g. `"0.2"`) |
| `type` | String | Yes | Classification of the document (e.g. `ContextBrief`, `Metric`, `Policy`, `Runbook`) |
| `title` | String | Yes | Human-readable title of the document |
| `description` | String | Yes | High-signal summary for semantic routing and indexing |
| `timestamp` | String (ISO-8601) | Yes | Generation or update timestamp |
| `tags` | Array of Strings | Optional | Categorization tags for keyword search |

### Git State Metadata (for Context Briefs)
For codebase orientation briefs, the frontmatter includes git state to enable zero-token freshness checks:
- `git_commit`: Full or abbreviated commit SHA at generation time.
- `git_branch`: Active working branch.
- `repo_type`: `single-project` or `monorepo`.

---

## 3. Directory & Bundle Layout

In multi-concept knowledge repositories, OKF organizes context into concepts:

```text
knowledge-bundle/
├── index.md             # Bundle root index (declares okf_version & bundle metadata)
├── log.md               # Chronological append-only ledger of updates
└── concepts/            # Domain concepts and definitions
    ├── index.md         # Category index
    ├── architecture/
    │   └── backend.md
    └── invariants/
        └── discounts.md
```

In a code repository implementing `get-immediate-context`, the brief is consolidated into `CONTEXT_BRIEF.md` at the repository root, with historical session ledgers optionally appended to `.context/`.

---

## 4. Example OKF Document

```markdown
---
okf_version: "0.2"
type: ContextBrief
title: "Shop Engine Context Brief"
description: "Repository architecture, package structure, and domain invariants for agent orientation."
git_commit: "7f2a1b9"
git_branch: "main"
repo_type: "monorepo"
timestamp: "2026-10-24T10:00:00Z"
tags:
  - context-brief
  - architecture
  - monorepo
---

# Shop Engine Context Brief

## 1. Purpose
E-commerce engine managing product catalog queries and customer checkout billing.

## 2. Stack & Dependencies
- **`packages/api`**: TypeScript (Node.js 20), Express 4, Prisma ORM.
- **`packages/billing`**: Python 3.11, FastAPI, Pydantic v2, Stripe SDK.
```

---

## 5. Agent Ingestion Rules

1. **Header Inspection First**: Agents inspect the YAML frontmatter before reading the body. If `git_commit` matches current `HEAD` and `git status` is clean, the brief is cached and reused with zero token penalty.
2. **Citation Tracking**: Concepts cite exact files and line numbers (e.g., `src/billing/tier.py:42`) so agents can verify claims before making code changes.
