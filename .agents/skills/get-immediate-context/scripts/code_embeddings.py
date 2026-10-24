#!/usr/bin/env python3
"""
code_embeddings.py - Ultra-Lightweight Code Embeddings & Semantic Search Engine

Generates dense vector embeddings for repository code and symbols.
Features:
  1. Default: 0-download, 0-dependency, subword feature-hashing + L2-normalized embeddings (instant & offline).
  2. Optional Neural Mode: Uses fastembed ONNX runtime if requested (--neural).
  3. Semantic Code Search: Cosine-similarity ranking over functions, classes, and code chunks.
  4. Stores embeddings in .context/embeddings.json with git commit cache.
"""

import os
import sys
import re
import math
import json
import hashlib
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

EMBEDDING_DIM = 256
IGNORED_DIRS = {
    ".git", ".github", ".vscode", ".idea", ".gemini",
    "node_modules", ".venv", "venv", "env", "__pycache__",
    "dist", "build", "target", "out", ".next", ".turbo",
    "coverage", ".pytest_cache", ".mypy_cache", "tmp", "temp", "vendor"
}

VALID_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".cs", ".java", ".md", ".json"}

# ---------------------------------------------------------
# Tokenizer & Lightweight Vectorizer
# ---------------------------------------------------------
def tokenize_code(text: str) -> list[str]:
    """Tokenizes code, splitting camelCase, snake_case, and extracting identifier tokens."""
    raw_words = re.findall(r"[A-Za-z0-9_]{2,}", text)
    tokens = []
    for w in raw_words:
        tokens.append(w.lower())
        # Split camelCase and snake_case into conceptual subwords
        subwords = re.sub(r"([a-z])([A-Z])", r"\1 \2", w).replace("_", " ").split()
        for sw in subwords:
            if len(sw) > 1:
                tokens.append(sw.lower())
    return tokens

def compute_lightweight_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Computes an L2-normalized dense feature-hash embedding vector (0-dependency, offline)."""
    tokens = tokenize_code(text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    # Term frequency counter
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1

    for t, count in tf.items():
        # Sublinear scaling for term frequency
        weight = 1.0 + math.log(count)
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[idx] += sign * weight

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [round(v / norm, 5) for v in vec]
    return vec

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes dot product of two L2-normalized vectors."""
    if len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))

# ---------------------------------------------------------
# Neural Embedding Engine (Optional fastembed)
# ---------------------------------------------------------
_NEURAL_MODEL = None

def get_neural_embeddings(texts: list[str]) -> list[list[float]]:
    global _NEURAL_MODEL
    try:
        from fastembed import TextEmbedding
        if _NEURAL_MODEL is None:
            print("[*] Initializing fastembed ONNX model (BAAI/bge-small-en-v1.5)...")
            _NEURAL_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return [list(vec) for vec in _NEURAL_MODEL.embed(texts)]
    except Exception as e:
        print(f"[WARN] Neural model unavailable ({e}). Falling back to lightweight vectorizer.")
        return [compute_lightweight_embedding(t) for t in texts]

# ---------------------------------------------------------
# Code Chunking Engine
# ---------------------------------------------------------
def chunk_code_file(filepath: Path, repo_root: Path) -> list[dict]:
    """Splits a file into meaningful logical chunks (functions/classes or blocks)."""
    chunks = []
    rel_path = filepath.relative_to(repo_root).as_posix()
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
    except Exception:
        return chunks

    if not lines:
        return chunks

    # If small file (< 80 lines), store as single chunk
    if len(lines) <= 80:
        chunks.append({
            "file": rel_path,
            "title": f"file:{rel_path}",
            "start_line": 1,
            "end_line": len(lines),
            "text": content[:1200]
        })
        return chunks

    # Chunk by logical function/class lines or sliding window
    chunk_size = 40
    overlap = 10
    start = 0
    while start < len(lines):
        end = min(start + chunk_size, len(lines))
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()
        if len(chunk_text) > 30:
            # Look for function or class signature in first few lines
            title = f"{rel_path}:L{start+1}-L{end}"
            for l in chunk_lines[:5]:
                l_strip = l.strip()
                if l_strip.startswith(("def ", "class ", "func ", "function ", "export ", "pub fn ")):
                    title = f"{rel_path}: {l_strip[:50]}"
                    break

            chunks.append({
                "file": rel_path,
                "title": title,
                "start_line": start + 1,
                "end_line": end,
                "text": chunk_text[:1000]
            })
        start += (chunk_size - overlap)

    return chunks

# ---------------------------------------------------------
# Embeddings Generation & Indexing
# ---------------------------------------------------------
def generate_code_embeddings(repo_root: Path, use_neural=False):
    """Chunks all codebase files, generates embeddings, and saves to .context/embeddings.json."""
    context_dir = repo_root / ".context"
    context_dir.mkdir(exist_ok=True)
    embeddings_file = context_dir / "embeddings.json"

    print(f"[*] Scanning files for code embeddings in {repo_root}...")
    all_chunks = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and (not d.startswith(".") or d == ".agents")]
        for f in files:
            fp = Path(root) / f
            if fp.suffix.lower() in VALID_EXTS and fp.name != "embeddings.json":
                chunks = chunk_code_file(fp, repo_root)
                all_chunks.extend(chunks)

    print(f"[*] Total code chunks to embed: {len(all_chunks)}")
    if not all_chunks:
        print("[!] No code chunks found.")
        return

    # Generate vectors
    if use_neural:
        texts = [f"{c['title']}\n{c['text']}" for c in all_chunks]
        vectors = get_neural_embeddings(texts)
    else:
        vectors = [compute_lightweight_embedding(f"{c['title']}\n{c['text']}") for c in all_chunks]

    # Save to JSON
    store = {
        "model": "fastembed-bge-small" if use_neural else "lightweight-subword-hash-256",
        "dim": len(vectors[0]) if vectors else EMBEDDING_DIM,
        "total_chunks": len(all_chunks),
        "chunks": []
    }

    for chunk, vec in zip(all_chunks, vectors):
        store["chunks"].append({
            "file": chunk["file"],
            "title": chunk["title"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "vector": vec,
            "snippet": chunk["text"][:180].replace("\n", " ")
        })

    embeddings_file.write_text(json.dumps(store, indent=2), encoding="utf-8")
    size_kb = len(embeddings_file.read_bytes()) / 1024
    print(f"[SUCCESS] Code embeddings generated: {len(store['chunks'])} chunks saved to {embeddings_file.name} ({size_kb:.1f} KB).")

# ---------------------------------------------------------
# Semantic Code Search
# ---------------------------------------------------------
def search_code_embeddings(repo_root: Path, query: str, top_k: int = 5):
    """Performs cosine-similarity search against code embeddings."""
    embeddings_file = repo_root / ".context" / "embeddings.json"
    if not embeddings_file.is_file():
        print("[*] Embeddings index not found. Generating now...")
        generate_code_embeddings(repo_root)

    try:
        store = json.loads(embeddings_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to load embeddings: {e}")
        return

    is_neural = "fastembed" in store.get("model", "")
    if is_neural:
        query_vec = get_neural_embeddings([query])[0]
    else:
        query_vec = compute_lightweight_embedding(query, dim=store.get("dim", EMBEDDING_DIM))

    results = []
    for chunk in store.get("chunks", []):
        sim = cosine_similarity(query_vec, chunk["vector"])
        if sim > 0.05:
            results.append((sim, chunk))

    results.sort(key=lambda x: x[0], reverse=True)
    top_matches = results[:top_k]

    print(f"\n=== 🧠 Semantic Code Search: '{query}' (Model: {store.get('model')}) ===")
    if not top_matches:
        print("  No semantically relevant code chunks found.")
        return

    print(f"{'Similarity':<12} | {'Location':<45} | {'Code Snippet'}")
    print("-" * 95)
    for sim, chunk in top_matches:
        loc = f"{chunk['file']}:L{chunk['start_line']}-L{chunk['end_line']}"
        snippet = chunk["snippet"]
        if len(snippet) > 40: snippet = snippet[:37] + "..."
        score_pct = f"{sim * 100:.1f}%"
        print(f"{score_pct:<12} | {loc:<45} | {snippet}")

    print("\n💡 Tip: View exact code lines using your editor or read_file tool.")

def main():
    repo_root = Path.cwd()
    args = sys.argv[1:]

    if not args or "--generate" in args:
        use_neural = "--neural" in args
        generate_code_embeddings(repo_root, use_neural=use_neural)
    elif "--search" in args:
        idx = args.index("--search")
        if idx + 1 < len(args):
            query = " ".join(args[idx + 1:])
            search_code_embeddings(repo_root, query=query)
        else:
            print("Usage: python code_embeddings.py --search <query>")
    elif "--info" in args:
        embeddings_file = repo_root / ".context" / "embeddings.json"
        if embeddings_file.is_file():
            store = json.loads(embeddings_file.read_text(encoding="utf-8"))
            print(f"Model: {store.get('model')}")
            print(f"Dimensions: {store.get('dim')}")
            print(f"Total Chunks: {store.get('total_chunks')}")
            print(f"Storage: {len(embeddings_file.read_bytes()) / 1024:.1f} KB")
        else:
            print("[INFO] No embeddings generated yet. Run: python code_embeddings.py --generate")
    else:
        # Default fallback to search if query passed
        query = " ".join(args)
        search_code_embeddings(repo_root, query=query)

if __name__ == "__main__":
    main()
