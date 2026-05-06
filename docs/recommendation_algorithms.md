# Recommendation Algorithms — CF, TF‑IDF, BERT (all‑miniLM‑L6)

This document summarizes core recommendation/retrieval approaches commonly used together in production: Collaborative Filtering (CF), TF‑IDF (sparse lexical retrieval), and semantic embeddings using BERT-like models (here: `all‑miniLM‑L6-v2`). It includes key formulas, algorithmic logic, strengths/weaknesses, and short pseudocode for implementation and hybrid combinations.

---

## 1. Collaborative Filtering (CF)

Overview
- CF uses past user–item interactions (ratings, clicks, bookings, etc.) to recommend items. Two main flavors:
  - User‑based CF: find users similar to the target user and recommend items they liked.
  - Item‑based CF: find items similar to items the user liked and recommend similar ones.
- Works well when you have explicit feedback (ratings) or dense implicit feedback.

Data model
- Let $R$ be the user–item matrix where $r_{u,i}$ is the rating or interaction value (0 if missing). Many algorithms operate on $R$.

Similarity metrics
- Cosine similarity between two vectors $x,y$:
  $\displaystyle \text{cos}(x,y)=\frac{x\cdot y}{\|x\|\,\|y\|}$. 
- Pearson correlation (centers by user/item mean) to handle shift in user rating scale.

Item‑based prediction (neighborhood method)
- Predict rating for user $u$ and item $i$ using top‑k similar items:

$$\hat r_{u,i} = \frac{\sum_{j\in N(i)} s_{i,j}\,r_{u,j}}{\sum_{j\in N(i)} |s_{i,j}|}$$

where $s_{i,j}$ is similarity between items $i$ and $j$, and $N(i)$ are items rated by user $u$.

Matrix factorization (latent factors)
- Learn low‑rank factors $P \in \mathbb{R}^{|U|\times f}$ and $Q \in \mathbb{R}^{|I|\times f}$ such that

$$R \approx P Q^T$$

- Typical loss (for observed entries):

$$\min_{P,Q} \sum_{(u,i)\in \Omega} (r_{u,i} - p_u^T q_i)^2 + \lambda(\|p_u\|^2 + \|q_i\|^2)$$

- Optimization: SGD or ALS (alternating least squares) for implicit feedback.

Cold start & sparsity
- New users/items are challenging. Use content features (profile, item metadata) and hybrid methods.
- For sparse data, prefer item‑based CF or content/hybrid retrieval.

Pseudocode: item‑based CF
- Build item vectors from user ratings (columns of $R$)
- Compute similarity matrix S (item×item)
- For a user u and target item i, use top-k neighbors to compute $\hat r_{u,i}$ (formula above)

Strengths
- Captures collaborative signals and taste patterns.

Weaknesses
- Cold start, data sparsity, scalability (large matrices) — mitigated with factorization and ANN indices.

---

## 2. TF‑IDF (term frequency–inverse document frequency)

Overview
- TF‑IDF is a sparse lexical representation for documents (or item descriptions). Commonly used for initial retrieval or where exact term match matters.

Formulas
- Term frequency (raw or normalized). One common normalization:
  $\displaystyle \text{tf}_{t,d} = \frac{f_{t,d}}{\max_{t'} f_{t',d}}$ where $f_{t,d}$ is raw count of term $t$ in document $d$.
- Inverse document frequency:
  $\displaystyle \text{idf}_t = \log\frac{N}{1 + \text{df}_t}$ where $N$ is number of documents and $\text{df}_t$ is document frequency.
- TF‑IDF weight:
  $\displaystyle w_{t,d} = \text{tf}_{t,d} \cdot \text{idf}_t$.

Similarity
- Represent query and documents as TF‑IDF vectors and compute cosine similarity:

$$\text{score}(q,d) = \frac{v_q \cdot v_d}{\|v_q\|\,\|v_d\|}$$

Where $v_q$ is TF‑IDF vector for the query.

Use in pipelines
- Fast to compute and index using inverted index (Lucene, Elastic, Whoosh).
- Use TF‑IDF to produce candidate set (top‑N lexical matches), then re‑rank with semantic model (BERT embeddings) or CF scores.

Strengths
- Fast, interpretable, handles exact keyword matches, small memory for inverted index.

Weaknesses
- Cannot capture semantic similarity beyond lexical overlap; synonyms and paraphrases are missed.

Pseudocode: TF‑IDF retrieval
- Precompute TF‑IDF vectors for documents and build inverted index
- Convert query to TF‑IDF vector
- Compute top‑N cosine similarities via sparse dot products (use index)

---

## 3. BERT (all‑miniLM‑L6‑v2) — sentence embeddings

Overview
- `all‑miniLM‑L6‑v2` is a small, fast sentence‑transformer model that maps text (sentences, short docs) to dense embeddings (e.g., 384 dimensions).
- Use for semantic similarity, paraphrase detection, and re‑ranking lexical candidates.

How embeddings are produced
- Input text is tokenized and passed through a transformer encoder. A pooling layer (mean, weighted mean, or CLS) aggregates token embeddings into a fixed‑length vector.
- Typical usage (with `sentence-transformers`): `embedding = model.encode(text)`.

Similarity and retrieval
- Use cosine similarity on normalized embeddings:

$$\text{sim}(a,b)=\frac{a\cdot b}{\|a\|\,\|b\|}$$

- For large collections, use Approximate Nearest Neighbors (ANN) libraries (Faiss, Annoy, HNSW) for sublinear retrieval.

Example pipeline
1. Candidate retrieval: use TF‑IDF or metadata filters to get top‑K candidates.
2. Encode query and candidates with `all‑miniLM‑L6‑v2`.
3. Re‑rank candidates by embedding cosine similarity.

Advantages
- Captures semantic relationships (synonyms, paraphrases).
- Works well with short queries and noisy text.

Considerations
- Embedding dimension and index size — use PCA or quantization if memory constrained.
- Normalizing embeddings (L2) helps: store normalized vectors so cosine similarity reduces to dot product.
- Latency: encoding many candidates can be costly; precompute and index item embeddings.

Pseudocode: semantic re‑rank
- Precompute and index item embeddings (index = ANN(index_vectors))
- For query q: e_q = encode(q)
- Find top‑M ANN neighbors by e_q
- Return items sorted by cosine(e_q, e_item)

---

## 4. Hybrid patterns (practical recommended approaches)

1. Lexical candidate + semantic re‑rank
   - Use TF‑IDF to get top‑N (e.g., 100) candidates quickly.
   - Re‑rank with BERT embeddings to capture semantics.

2. CF + content hybrid
   - Use collaborative scores (CF or MF) when users have interaction history.
   - Fall back to content (TF‑IDF/BERT) for cold start.
   - Combine by weighted sum or learning‑to‑rank model:

$$\text{score} = \alpha\,\text{CF}_\text{score} + (1-\alpha)\,\text{semantic}_\text{score}$$

3. Two‑stage retrieval (filter → rank) for scale
   - Stage 1: cheap filters (category, TF‑IDF, popularity)
   - Stage 2: expensive re‑ranking (BERT embeddings, learning‑to‑rank)

Implementation notes
- Precompute where possible: item embeddings, item popularity, and TF‑IDF index.
- Use ANN for fast semantic lookup. Tune index (ef, nprobe, etc.) for recall/latency tradeoffs.
- Normalize scores when combining different sources (CF, cosine, popularity) to comparable ranges.

---

## 5. Practical tips & thresholds

- Cosine similarity thresholds are task dependent; start with 0.6–0.8 for strong semantic match.
- For TF‑IDF, tune `idf` smoothing and query expansion to improve recall.
- For MF, use $f=32$–$128$ latent dims for moderate datasets; regularize ($\lambda$) to avoid overfitting.
- Measure recommenders by offline metrics (precision@k, recall@k, NDCG) and online A/B tests.

---

## 6. References & libraries

- `scikit-learn` — TF‑IDF vectorizer, cosine similarity
- `sentence-transformers` — `all-miniLM-L6-v2` encoder
- `Faiss`, `Annoy`, `hnswlib` — ANN indexes for embeddings
- Recommender libraries: `implicit` (ALS), `Surprise` (matrix factorization examples)

---

## 7. Quick implementation sketches

TF‑IDF (Python/sklearn):

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
vectorizer = TfidfVectorizer(max_features=50_000)
X = vectorizer.fit_transform(documents)
qv = vectorizer.transform([query])
scores = cosine_similarity(qv, X).ravel()
```

BERT embeddings (sentence-transformers):

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
# L2-normalize then use Faiss/Annoy to index
```

Matrix factorization (SGD sketch):

```python
# minimize over observed (u,i)
# p_u, q_i randomly initialized
for epoch in range(E):
    for (u,i,r) in observed:
        e = r - p[u].dot(q[i])
        p[u] += lr * (e * q[i] - reg * p[u])
        q[i] += lr * (e * p[u] - reg * q[i])
```

---

If you want, I can:
- Add code examples specific to our backend (Python/FASTAPI) or frontend use, or
- Create a small example pipeline (TF‑IDF retrieval + BERT re‑rank) with sample data and tests.

