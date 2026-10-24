# Claude Code Project Guidelines: get-immediate-context

## Immediate Codebase Orientation
- Always inspect `CONTEXT_BRIEF.md` at the repository root before answering or implementing tasks.
- Verify `git_commit` in the header matches current HEAD. If stale, run:
  `python .agents/skills/get-immediate-context/scripts/fetch_context.py`
- Check Section 6 for confirmed domain invariants (`[INV-xxx]`). Never violate them without explicit user consent.
- Check Section 9 for exact symbol locations (`Lxx-Lyy`) rather than reading large files in full.

## Helper Tools & Skills
- **Locate symbols/functions**: `python .agents/skills/get-immediate-context/scripts/symbol_indexer.py --locate <name>`
- **Semantic code search**: `python .agents/skills/get-immediate-context/scripts/code_embeddings.py --search "<intent>"`
- **Hybrid search (BM25 + Vector)**: `python .agents/skills/get-immediate-context/scripts/hybrid_search.py "<query>"`
- **Blast radius impact analysis**: `python .agents/skills/get-immediate-context/scripts/call_graph.py --impact <filename>`
- **Check invariant impact before commit**: `python .agents/skills/get-immediate-context/scripts/diff_impact.py`

## Privacy & Safety
- Never store or display secrets. Wrap proprietary blocks in `<private>...</private>` markers.
