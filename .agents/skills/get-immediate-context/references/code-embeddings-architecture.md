# Lightweight Code Embeddings Architecture Reference

## 1. Design Goals

- **Zero-Dependency Fallback**: Must work on a fresh machine with only Python 3 standard library installed (no `torch`, `transformers`, or C++ compilers required).
- **Fast Execution**: Must index a 1,000-file repository in under 2 seconds.
- **Semantic Code Awareness**: Tokenization must understand code semantics (e.g. splitting `calculateDiscount` into `calculate` and `discount`).
- **Dense Vector Search**: Standard vector search via Cosine Similarity.

---

## 2. Feature Hashing & Subword Vectorization

### Architecture Diagram
```
Raw Source Code 
       │
       ▼
Code-Aware Tokenizer (Split camelCase, snake_case, keywords)
       │
       ▼
MD5 Feature Hashing with Sublinear TF Scaling: w = 1.0 + ln(count)
       │
       ▼
256-Dimensional Vector Assignment with Alternate Sign Bit Hashing
       │
       ▼
L2 Normalization: v_norm = v / sqrt(sum(v_i^2))
       │
       ▼
Dense 256-dim Vector Saved to .context/embeddings.json
```

---

## 3. Cosine Similarity Formula

Because both the query vector $\mathbf{q}$ and code chunk vector $\mathbf{d}$ are $L_2$-normalized ($||\mathbf{q}||_2 = 1, ||\mathbf{d}||_2 = 1$):

$$\text{Similarity}(\mathbf{q}, \mathbf{d}) = \mathbf{q} \cdot \mathbf{d} = \sum_{i=1}^{256} q_i \cdot d_i$$

- **Range**: $[-1.0, 1.0]$ (practically $[0.0, 1.0]$ for code queries).
- **Threshold**: Similarity scores $> 0.15$ indicate strong lexical and semantic overlap.

---

## 4. Code Chunking Strategy

Instead of arbitrary character chunking (which breaks function signatures):
- Files $\le 80$ lines are treated as a single cohesive chunk.
- Files $> 80$ lines are split in sliding 40-line windows with a 10-line overlap.
- Chunk titles automatically capture enclosing signatures (e.g., `def sanitize_text()`, `class InvariantEngine`).

---

## 5. Neural FastEmbed Fallback (Optional)

When the `--neural` flag is supplied and `fastembed` is installed:
- Model: `BAAI/bge-small-en-v1.5` running on `onnxruntime`.
- Embedding Dimension: 384 dimensions.
- Use case: Deep conceptual questions where code syntax differs completely from query vocabulary.
