#!/usr/bin/env python3
"""
hybrid_search.py - Hybrid Code Retrieval (BM25 Lexical + Dense Vector RRF Fusion)

Combines:
  1. BM25 Lexical Term Scoring (Exact symbol, keyword, and token match)
  2. Dense Cosine Similarity (Conceptual & semantic match from code_embeddings.py)
  3. Reciprocal Rank Fusion (RRF): Rank = 1/(k + rank_bm25) + 1/(k + rank_dense)
Zero external dependencies.
"""

import sys
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
            # Standard Lucene/BM25 IDF formula
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
# Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------
def reciprocal_rank_fusion(ranked_lists: list[list[int]], k: int = 60) -> dict[int, float]:
    """Blends multiple ranked lists using Reciprocal Rank Fusion."""
    rrf_scores = {}
    for r_list in ranked_lists:
        for rank, doc_idx in enumerate(r_list, start=1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (k + rank))
    return rrf_scores

def perform_hybrid_search(repo_root: Path, query: str, top_k: int = 5):
    """Executes BM25 and Vector search, fuses with RRF, and outputs top ranked results."""
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

    query_tokens = code_embeddings.tokenize_code(query) if code_embeddings else query.lower().split()

    # 1. BM25 Lexical Ranking
    bm25 = BM25Okapi(chunks)
    bm25_scores = bm25.get_scores(query_tokens)
    bm25_ranked = sorted(range(len(chunks)), key=lambda idx: bm25_scores[idx], reverse=True)

    # 2. Dense Vector Ranking
    query_vec = code_embeddings.compute_lightweight_embedding(query, dim=store.get("dim", 256))
    vector_scores = [code_embeddings.cosine_similarity(query_vec, c["vector"]) for c in chunks]
    vector_ranked = sorted(range(len(chunks)), key=lambda idx: vector_scores[idx], reverse=True)

    # 3. Fuse via RRF
    fused_scores = reciprocal_rank_fusion([bm25_ranked, vector_ranked], k=60)
    final_ranked = sorted(fused_scores.keys(), key=lambda idx: fused_scores[idx], reverse=True)

    top_matches = final_ranked[:top_k]

    print(f"\n=== ⚡ Hybrid Search: '{query}' (BM25 + Dense Vector RRF) ===")
    print(f"{'RRF Score':<11} | {'BM25':<8} | {'Cosine':<8} | {'Location':<40} | {'Snippet'}")
    print("-" * 105)

    for idx in top_matches:
        chunk = chunks[idx]
        rrf = fused_scores[idx]
        b_score = bm25_scores[idx]
        v_score = vector_scores[idx]
        loc = f"{chunk['file']}:L{chunk['start_line']}-L{chunk['end_line']}"
        snippet = chunk.get("snippet", "")
        if len(snippet) > 35: snippet = snippet[:32] + "..."
        print(f"{rrf:.4f}     | {b_score:.2f}   | {v_score*100:.1f}%  | {loc[:40]:<40} | {snippet}")

    print("\n💡 Tip: Hybrid search eliminates vocabulary mismatch by uniting lexical accuracy with semantic intent.")

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
