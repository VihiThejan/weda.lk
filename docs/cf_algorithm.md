# Collaborative Filtering (CF) — Algorithms and Implementation

This file explains common CF algorithms in detail: user‑based and item‑based neighborhood methods, matrix factorization (SGD / ALS), and handling implicit feedback. It includes formulas, algorithmic steps, pseudocode, complexity, and practical tips.

## 1. Data model
- Let U be users, I be items. Observed interactions (explicit ratings or implicit events) are represented as a set \(\Omega = \{(u,i,r_{u,i})\}\).
- For explicit ratings, \(r_{u,i}\) is typically in a bounded scale (e.g., 1–5).
- For implicit feedback, \(r_{u,i}\) can be 1 for an event (click, booking) and 0 for missing.

## 2. Neighborhood methods (item‑based and user‑based)

### Similarity
- Cosine similarity between two item vectors (columns of rating matrix):

$$s_{i,j} = \frac{\sum_{u\in U_{ij}} r_{u,i} r_{u,j}}{\sqrt{\sum_{u\in U_{ij}} r_{u,i}^2}\sqrt{\sum_{u\in U_{ij}} r_{u,j}^2}}$$

where \(U_{ij}\) is users who rated both i and j. Use shrinkage to reduce noise for low overlap.

### Prediction (item‑based top‑k neighbors)

$$\hat r_{u,i} = \bar r_u + \frac{\sum_{j\in N_k(i)} s_{i,j} (r_{u,j} - \bar r_u)}{\sum_{j\in N_k(i)} |s_{i,j}|}$$

- \(\bar r_u\) is user's mean rating (optional centering).
- Choose top‑k similar items \(N_k(i)\) that user u has rated.

### Pseudocode (item‑based)

1. Build item vectors (sparse) from interactions.
2. Compute item×item similarities (use sparse operations; compute only pairs with co‑occurrence).
3. For user u, for each candidate item i: find top‑k neighbors j rated by u and compute \(\hat r_{u,i}\).

### Complexity & scaling
- Computing full item×item similarity is O(|I|^2) worst case. Use sparsity, or compute on demand for popular items.
- Store only top‑N neighbors per item.

## 3. Matrix Factorization (latent factors)

### Model
- Learn latent factors \(P\in\mathbb{R}^{|U|\times f}\) and \(Q\in\mathbb{R}^{|I|\times f}\):

$$\hat r_{u,i} = p_u^T q_i + b_u + b_i + \mu$$

where \(b_u,b_i\) are biases and \(\mu\) is global mean.

### Loss (explicit)

$$L = \sum_{(u,i)\in\Omega} (r_{u,i} - p_u^T q_i - b_u - b_i - \mu)^2 + \lambda(\|p_u\|^2 + \|q_i\|^2 + b_u^2 + b_i^2)$$

- Optimize with SGD: iterate observed interactions, update parameters using gradient steps.

### SGD update (one sample)

Let e = r_{u,i} - p_u^T q_i - b_u - b_i - \mu

p_u <- p_u + lr * (e * q_i - lambda * p_u)

q_i <- q_i + lr * (e * p_u - lambda * q_i)

b_u <- b_u + lr * (e - lambda * b_u)

b_i <- b_i + lr * (e - lambda * b_i)

### Implicit feedback (Hu, Koren, Volinsky)
- Use confidence weighting where observed interactions have high confidence. Minimize weighted squared error with ALS or adapt SGD.

### Pseudocode (MF SGD)

Initialize p_u, q_i, biases
for epoch in epochs:
  shuffle(observed)
  for (u,i,r) in observed:
    e = r - predict(u,i)
    update p_u, q_i, b_u, b_i

### Complexity
- Per SGD step: O(f). Total cost O(|\Omega| * f * epochs).
- Works well for medium datasets; for large ones use optimized libraries (implicit, LightFM, Spotlight) and parallel ALS (alternating least squares).

## 4. Cold start and hybridization
- New items/users: use content features to initialize factors (feature‑aware factorization) or rely on TF‑IDF/BERT content retrieval for cold start.
- Combine CF and content via weighted sum or learning‑to‑rank.

## 5. Practical tips & libraries
- Use `implicit` for implicit ALS; `lightfm` for hybrid matrix factorization with content; `surprise` for learning and evaluation on explicit ratings.
- Regularize and validate with held‑out sets; use `precision@k`, `recall@k`, `ndcg@k`.


---

References: Koren et al. (Matrix Factorization), Hu et al. (Collaborative Filtering for Implicit Feedback).