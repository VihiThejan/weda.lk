# TF‑IDF Algorithm — Details and Implementation

This document describes TF‑IDF vectorization, indexing, retrieval, scoring, and practical implementation notes.

## 1. Vector representation
- Vocabulary: all terms (tokens) after normalization (lowercasing, stopword removal, optional stemming/lemmatization).
- Term frequency (tf): raw count f_{t,d} or normalized form. Common normalizations:
  - raw: tf = f_{t,d}
  - log: tf = 1 + log(f_{t,d}) if f_{t,d}>0
  - max normalization: tf = f_{t,d} / max_t' f_{t',d}

- Inverse document frequency (idf):

$$\text{idf}_t = \log\frac{N}{1 + \text{df}_t}$$

where N is number of documents and df_t is document frequency.

- TF‑IDF weight for term t in document d:

$$w_{t,d} = \text{tf}_{t,d} \cdot \text{idf}_t$$

- Represent document d as sparse vector v_d of weights w_{t,d}.

## 2. Indexing and retrieval
- Build an inverted index mapping term -> posting list of (doc_id, weight).
- Query q is tokenized and converted to TF‑IDF vector v_q (using same idf as index).
- Compute document scores via sparse dot product between v_q and document vectors (posting lists):

$$\text{score}(q,d) = v_q \cdot v_d$$

or normalized cosine similarity after L2 normalizing vectors.

- Use standard inverted index top‑k retrieval (accumulate scores from postings and return highest scored docs). Libraries: Lucene, Elastic, Whoosh, or custom using `scipy.sparse`.

## 3. Query expansion & weighting
- Expand synonyms (WordNet), use n‑grams, or boost terms based on domain knowledge.
- Boost idf or apply BM25 instead of strict TF‑IDF for better ranking (BM25 accounts for document length and term saturation).

BM25 scoring (short):

$$\text{score}(q,d)=\sum_{t\in q} idf_t \cdot \frac{f_{t,d}(k+1)}{f_{t,d} + k (1-b + b|d|/\text{avgdl})}$$

with k and b hyperparameters.

## 4. Pseudocode (sparse retrieval)

1. Precompute idf for vocabulary, and per‑document normalized TF‑IDF weights, store postings for each term.
2. For query q: build v_q and iterate each term t in q:
   - For each (doc_id, w_td) in postings[t]: accumulate score[doc_id] += w_tq * w_td
3. Normalize scores if using cosine similarity.
4. Return top‑k by score.

## 5. Implementation (scikit‑learn quick example)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1,2))
X = vectorizer.fit_transform(doc_texts)  # shape (n_docs, n_terms)
qv = vectorizer.transform([query])
scores = linear_kernel(qv, X).ravel()  # dot product on L2‑normalized TF‑IDF
```

## 6. Strengths, weaknesses & when to use
- Strengths: very fast with inverted index, interpretable, good at exact keyword matches.
- Weaknesses: lacks semantic generalization (synonyms, paraphrases).
- Use as first stage candidate retrieval; combine with semantic models for re‑ranking.


References: classic IR texts (Manning et al. — Introduction to Information Retrieval), BM25 papers.