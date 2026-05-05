# Using BERT (all‑miniLM‑L6‑v2) for Retrieval and Re‑ranking

This document explains how to use sentence‑transformer embeddings (e.g., `all‑miniLM‑L6‑v2`) in retrieval pipelines: encoding, indexing, ANN retrieval, semantic re‑ranking, and hybrid scoring. Includes code sketches and practical tips.

## 1. Embedding generation
- Load model (sentence‑transformers) and `encode()` texts (documents/items or queries).
- Recommended: L2 normalize embeddings and store as float32 arrays.

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(docs, convert_to_numpy=True, show_progress_bar=True)
# L2 normalize
import numpy as np
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
```

## 2. Indexing (ANN)
- For large corpora, use ANN indexes: Faiss, hnswlib, Annoy; choose based on latency/memory.
- Example (hnswlib):

```python
import hnswlib
dim = embeddings.shape[1]
index = hnswlib.Index(space='cosine', dim=dim)
index.init_index(max_elements=n_docs, ef_construction=200, M=16)
index.add_items(embeddings, ids=np.arange(n_docs))
index.set_ef(50)
```

- Store mapping id → document metadata separately.

## 3. Two‑stage pipeline (recommended)
1. Candidate selection: use TF‑IDF or filters to get top‑N candidates (cheap). Or use ANN on embeddings to get candidates directly.
2. Re‑rank: compute query embedding and re‑score candidates by cosine similarity.

Re‑rank formula (plain semantic):

$$\text{score}_{semantic}(q,d) = e_q^T e_d$$

If combining with CF or lexical scores, normalize each source to [0,1] and combine:

$$\text{score}(q,d)=\alpha\,\text{score}_{lex}(q,d) + \beta\,\text{score}_{semantic}(q,d) + \gamma\,\text{score}_{cf}(u,d)$$

where \(\alpha+\beta+\gamma=1\).

## 4. Efficiency tips
- Precompute item embeddings so ranking is a single dot product per candidate.
- Batch encode queries when handling high throughput.
- Use quantization (Faiss IVFPQ) or HNSW quantized indexes to reduce memory.
- Normalize embeddings at index time so cosine similarity reduces to dot product.

## 5. Example: TF‑IDF candidate + BERT re‑rank (Python sketch)

```python
# Precompute TF‑IDF index (sparse) and item embeddings
# Step at query time:
q_tf = tfidf_vectorizer.transform([query])
candidates = topk_by_tfidf(q_tf, topk=200)  # returns doc ids
q_emb = model.encode([query], convert_to_numpy=True)
q_emb = q_emb / np.linalg.norm(q_emb)
# Load candidate embeddings
cand_embs = item_embeddings[candidates]
scores = cand_embs.dot(q_emb.T).ravel()
# Combine scores (optional) and sort
```

## 6. Practical considerations
- Dimensionality: `all‑miniLM‑L6‑v2` returns 384‑dim embeddings (moderate size).
- Relevance thresholds: tune on dev set; semantic similarity scales differ from lexical scores.
- Interpretability: provide highlighted lexical matches for UI along with semantic result.

## 7. Libraries & resources
- `sentence-transformers` for embedding models
- `faiss` / `hnswlib` / `annoy` for ANN
- `scikit-learn` for TF‑IDF and evaluation


---

If you want, I can implement a runnable example in `model-test/` that demonstrates a small dataset, TF‑IDF candidate retrieval, and BERT re‑ranking using `sentence-transformers` and `scikit-learn`. Would you like that?