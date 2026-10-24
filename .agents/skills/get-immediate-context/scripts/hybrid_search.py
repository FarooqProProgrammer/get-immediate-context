#!/usr/bin/env python3
"""
hybrid_search.py - Smart Intent-Aware Hybrid Code & Documentation Retrieval

Combines:
  1. BM25 Lexical Term Scoring (Exact symbol, keyword, and token match)
  2. Dense Cosine Similarity (Conceptual & semantic match from code_embeddings.py)
  3. Intent-Aware Boosting:
     - "doc/definition/content" intent -> prioritizes Markdown (.md, .mdc)
     - "code/implementation/function" intent -> prioritizes source code (.py, .ts, etc.)
  4. Exact Verbatim Substring Matching Boost
  5. Reciprocal Rank Fusion (RRF): Rank = 1/(k + rank_bm25) + 1/(k + rank_dense)
Zero external dependencies.
"""

import sys
import re
import math
import json
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import helper functions from sibling scripts
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    import code_embeddings
except ImportError:
    code_embeddings = None

# ---------------------------------------------------------
# Intent Classification & File Type Prioritization
# ---------------------------------------------------------
DOC_INTENT_KEYWORDS = {
    "definition", "skill", "reference", "content", "written", "text",
    "described", "docs", "doc", "spec", "rule", "rules", "where is it mentioned",
    "markdown", "readme", "explain", "meaning", "guide", "on which file"
}

CODE_INTENT_KEYWORDS = {
    "code", "function", "class", "def", "implement", "implementation", "logic",
    "script", "run", "execute", "handler", "method", "variable", "syntax", "source"
}

def detect_query_intent(query: str) -> str:
    """Classifies user intent as 'doc', 'code', or 'neutral'."""
    q_words = set(re.findall(r"[a-z]+", query.lower()))
    doc_overlap = len(q_words & DOC_INTENT_KEYWORDS)
    code_overlap = len(q_words & CODE_INTENT_KEYWORDS)

    if doc_overlap > code_overlap:
        return "doc"
    elif code_overlap > doc_overlap:
        return "code"
    return "neutral"

# ---------------------------------------------------------
# BM25 Lexical Scoring Engine
# ---------------------------------------------------------
class BM25Okapi:
    def __init__(self, corpus_chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_chunks = corpus_chunks
        self.doc_len = []
        self.doc_freqs = []
        self.idf = {}
        self.avg_doc_len = 0.0

        total_len = 0
        df = {}
        for chunk in corpus_chunks:
            tokens = code_embeddings.tokenize_code(chunk["title"] + " " + chunk.get("snippet", "")) if code_embeddings else chunk["title"].lower().split()
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            freqs = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self.doc_freqs.append(freqs)
            for t in freqs.keys():
                df[t] = df.get(t, 0) + 1

        n_docs = max(1, len(corpus_chunks))
        self.avg_doc_len = total_len / n_docs if n_docs > 0 else 1.0

        for t, freq in df.items():
            self.idf[t] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = [0.0] * len(self.corpus_chunks)
        for i, freqs in enumerate(self.doc_freqs):
            doc_l = self.doc_len[i]
            score = 0.0
            for t in query_tokens:
                if t in freqs:
                    tf = freqs[t]
                    idf = self.idf.get(t, 0.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_l / self.avg_doc_len))
                    score += idf * (tf * (self.k1 + 1.0) / (denom if denom > 0 else 1.0))
            scores[i] = score
        return scores

# ---------------------------------------------------------
# Reciprocal Rank Fusion (RRF) with Intent Weighting
# ---------------------------------------------------------
def reciprocal_rank_fusion(ranked_lists: list[list[int]], k: int = 60) -> dict[int, float]:
    rrf_scores = {}
    for r_list in ranked_lists:
        for rank, doc_idx in enumerate(r_list, start=1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (k + rank))
    return rrf_scores

def perform_hybrid_search(repo_root: Path, query: str, top_k: int = 5):
    """Executes BM25 and Vector search, applies intent & phrase boosts, fuses via RRF."""
    embeddings_file = repo_root / ".context" / "embeddings.json"
    if not embeddings_file.is_file():
        if code_embeddings:
            print("[*] Generating embeddings index first...")
            code_embeddings.generate_code_embeddings(repo_root)
        else:
            print("[ERROR] .context/embeddings.json not found.")
            return

    try:
        store = json.loads(embeddings_file.read_text(encoding="utf-8"))
        chunks = store.get("chunks", [])
    except Exception as e:
        print(f"[ERROR] Failed to load chunks: {e}")
        return

    if not chunks:
        print("[!] No code chunks available for search.")
        return

    # Detect user intent
    intent = detect_query_intent(query)
    clean_query = query.lower()
    query_tokens = code_embeddings.tokenize_code(query) if code_embeddings else clean_query.split()

    # 1. BM25 Lexical Ranking
    bm25 = BM25Okapi(chunks)
    bm25_scores = bm25.get_scores(query_tokens)
    bm25_ranked = sorted(range(len(chunks)), key=lambda idx: bm25_scores[idx], reverse=True)

    # 2. Dense Vector Ranking
    query_vec = code_embeddings.compute_lightweight_embedding(query, dim=store.get("dim", 256))
    vector_scores = [code_embeddings.cosine_similarity(query_vec, c["vector"]) for c in chunks]
    vector_ranked = sorted(range(len(chunks)), key=lambda idx: vector_scores[idx], reverse=True)

    # 3. Base RRF Fusion
    fused_scores = reciprocal_rank_fusion([bm25_ranked, vector_ranked], k=60)

    # 4. Intent & Exact Match Re-ranking
    # Extract significant phrases from query (>= 3 words)
    words = re.findall(r"[A-Za-z0-9_\-]+", clean_query)
    phrases = []
    if len(words) >= 3:
        phrases.append(" ".join(words[:3]))
        phrases.append(" ".join(words[:4]))
        phrases.append(" ".join(words))

    for idx, chunk in enumerate(chunks):
        file_path = chunk["file"].lower()
        snippet = chunk.get("snippet", "").lower()
        title = chunk.get("title", "").lower()

        # Intent boost
        is_doc = file_path.endswith((".md", ".mdc", ".txt", ".json"))
        if intent == "doc" and is_doc:
            fused_scores[idx] *= 1.35  # boost documentation when user asks for content/definition
        elif intent == "code" and not is_doc:
            fused_scores[idx] *= 1.35  # boost code when user asks for functions/implementation

        # Exact multi-word phrase bonus
        for phrase in phrases:
            if len(phrase) > 10 and (phrase in snippet or phrase in title):
                fused_scores[idx] += 0.020  # decisive boost for verbatim text match
                break

    final_ranked = sorted(fused_scores.keys(), key=lambda idx: fused_scores[idx], reverse=True)
    top_matches = final_ranked[:top_k]

    intent_label = f"Intent: {intent.upper()}" if intent != "neutral" else "Intent: GENERAL"
    print(f"\n=== ⚡ Smart Hybrid Search: '{query}' ({intent_label} | BM25 + Vector RRF) ===")
    print(f"{'RRF Score':<11} | {'BM25':<8} | {'Cosine':<8} | {'Location':<42} | {'Snippet'}")
    print("-" * 110)

    for idx in top_matches:
        chunk = chunks[idx]
        rrf = fused_scores[idx]
        b_score = bm25_scores[idx]
        v_score = vector_scores[idx]
        loc = f"{chunk['file']}:L{chunk['start_line']}-L{chunk['end_line']}"
        snippet = chunk.get("snippet", "")
        if len(snippet) > 38: snippet = snippet[:35] + "..."
        print(f"{rrf:.4f}     | {b_score:.2f}   | {v_score*100:.1f}%  | {loc[:42]:<42} | {snippet}")

    print("\n💡 Tip: Intent detection automatically prioritizes documentation (.md) for definitions and code (.py) for functions.")

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]
    if not args:
        print("Usage: python hybrid_search.py <query>")
        return
    query = " ".join(args)
    perform_hybrid_search(repo_root, query=query)

if __name__ == "__main__":
    main()
