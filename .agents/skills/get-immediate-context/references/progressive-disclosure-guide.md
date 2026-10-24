# Progressive Disclosure & Token Budgeting Guide

## 1. The Context Window Problem

LLMs have finite context windows. Injecting entire codebases or long documentation on session start leads to:
1. **Context Window Saturation**: Leaving insufficient token headroom for generation, reasoning, and test output.
2. **"Lost in the Middle" Effect**: Core domain invariants get buried under thousands of lines of boilerplate code.
3. **High Latency & Costs**: Re-sending 50,000+ tokens on every turn increases request latency and API costs.

---

## 2. The 3-Tier Progressive Disclosure Model

`get-immediate-context` organizes memory into three discrete tiers:

```
┌────────────────────────────────────────────────────────┐
│ Level 1: Index (~100 tokens)                          │
│ - Git SHA, Branch, Repo Type, Package List             │
└──────────────────────────┬─────────────────────────────┘
                           │ (Default Load)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Level 2: Standard OKF Brief (~700 - 1,200 tokens)      │
│ - Project Purpose, Entry Points, Run/Test Commands     │
│ - Confirmed Invariants [INV-xxx] with File Citations   │
│ - Live Code Location Table (Key classes & line ranges) │
└──────────────────────────┬─────────────────────────────┘
                           │ (On-Demand Fetch)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Level 3: Deep Dive (Variable, scoped to target task)   │
│ - Specific package implementation files                │
│ - Semantic search snippet retrieval via embeddings     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Token Cost Visibility Matrix

| Tier | Payload | Token Estimate | When to Use |
|---|---|---|---|
| **Level 1** | Frontmatter YAML | ~80 - 120 tokens | Fast heartbeat checks, CI scripts, quick git diff confirmation. |
| **Level 2** | Full `CONTEXT_BRIEF.md` | ~700 - 1,200 tokens | **Default**. Starts every interactive agent session with complete architecture and invariant context. |
| **Level 3** | Semantic search chunk | ~40 - 150 tokens per chunk | When working on a specific bug or feature; fetch only the matching function or class chunk. |

---

## 4. How to Calculate Token Cost

As a heuristic for English and source code:
$$\text{Tokens} \approx \frac{\text{Character Count}}{4}$$

- In Python:
  ```python
  def estimate_tokens(text: str) -> int:
      return max(1, len(text) // 4)
  ```

---

## 5. Decision Rules for Agents

1. **Never load Level 3 globally**: Only load Level 3 context for the specific module directly referenced by the user prompt.
2. **Verify Gate at Level 1**: Check `git_commit` at Level 1 before spending tokens reading Level 2.
3. **Cache Invariant Citations**: Rely on Level 2 invariant citations (`[INV-001]`) to avoid opening validator files until modification is required.
