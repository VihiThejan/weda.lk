from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from threading import Lock
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer

from .config import get_paths

logger = logging.getLogger(__name__)

WEIGHTS = {
    "tfidf": 0.30,
    "bert": 0.35,
    "cf": 0.35,
}


@dataclass
class RecommenderArtifacts:
    provider_df: pd.DataFrame
    interaction_df: pd.DataFrame
    tfidf_vectorizer: TfidfVectorizer
    tfidf_matrix: np.ndarray
    bert_model: SentenceTransformer
    provider_embeddings: np.ndarray
    user_preferences: dict
    provider_credibility: pd.DataFrame


class HybridRecommenderService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._loaded = False
        self._artifacts: RecommenderArtifacts | None = None
        self._paths = get_paths()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._artifacts = self._load_artifacts()
            self._loaded = True

    def _load_artifacts(self) -> RecommenderArtifacts:
        paths = self._paths
        provider_df = self._load_provider_dataset(paths.provider_dataset)
        interaction_df = self._load_interaction_dataset(paths.interaction_dataset)

        provider_df = self._prepare_provider_df(provider_df, interaction_df)

        tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),
            stop_words="english",
        )
        tfidf_matrix = tfidf_vectorizer.fit_transform(provider_df["combined_text"])

        bert_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=str(paths.models_dir))
        provider_embeddings = self._load_or_build_embeddings(
            paths.embeddings_cache,
            bert_model,
            provider_df["combined_text"].tolist(),
        )

        provider_credibility, user_preferences = self._build_cf_components(
            provider_df,
            interaction_df,
        )

        logger.info("Component 1 artifacts loaded")

        return RecommenderArtifacts(
            provider_df=provider_df,
            interaction_df=interaction_df,
            tfidf_vectorizer=tfidf_vectorizer,
            tfidf_matrix=tfidf_matrix,
            bert_model=bert_model,
            provider_embeddings=provider_embeddings,
            user_preferences=user_preferences,
            provider_credibility=provider_credibility,
        )

    def _load_provider_dataset(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Provider dataset not found at {path}")
        return pd.read_excel(path)

    def _load_interaction_dataset(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Interaction dataset not found at {path}")
        return pd.read_excel(path)

    def _prepare_provider_df(self, provider_df: pd.DataFrame, interaction_df: pd.DataFrame) -> pd.DataFrame:
        provider_df = provider_df.copy()

        if "description" not in provider_df.columns:
            provider_df["description"] = ""
        provider_df["description"] = provider_df["description"].fillna("")

        if "service" not in provider_df.columns:
            provider_df["service"] = ""
        provider_df["service"] = provider_df["service"].fillna("")

        provider_df["description_clean"] = provider_df["description"].apply(self._clean_text)
        provider_df["service_clean"] = provider_df["service"].apply(self._clean_text)
        provider_df["combined_text"] = (
            provider_df["service_clean"].astype(str) + " " + provider_df["description_clean"].astype(str)
        )

        if "booking_status" in interaction_df.columns:
            booking_status = interaction_df["booking_status"]
            if booking_status.dtype == object:
                interaction_df = interaction_df.copy()
                interaction_df["booking_status"] = booking_status.str.lower().isin(
                    ["completed", "success", "successful", "true", "1"]
                ).astype(float)

        interaction_metrics = interaction_df.groupby("provider_id").agg(
            avg_rating=("rating", "mean"),
            interaction_count=("rating", "count"),
            booking_success_rate=("booking_status", "mean"),
        )
        interaction_metrics = interaction_metrics.reset_index()

        provider_df = provider_df.merge(interaction_metrics, on="provider_id", how="left")

        if "rating" in provider_df.columns:
            provider_df["avg_rating"] = provider_df["avg_rating"].fillna(provider_df["rating"])
        else:
            provider_df["avg_rating"] = provider_df["avg_rating"].fillna(0)

        provider_df["interaction_count"] = provider_df["interaction_count"].fillna(0)
        provider_df["booking_success_rate"] = provider_df["booking_success_rate"].fillna(0)

        if "price_lkr" not in provider_df.columns and "price" in provider_df.columns:
            provider_df["price_lkr"] = provider_df["price"]

        return provider_df

    def _clean_text(self, text: str) -> str:
        if pd.isna(text):
            return ""
        return str(text).lower()

    def _load_or_build_embeddings(
        self,
        cache_path: Path,
        bert_model: SentenceTransformer,
        texts: list[str],
    ) -> np.ndarray:
        if cache_path.exists():
            return np.load(cache_path)

        embeddings = bert_model.encode(
            texts,
            batch_size=128,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_path, embeddings)
        return embeddings

    def _build_cf_components(
        self,
        provider_df: pd.DataFrame,
        interaction_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict]:
        provider_credibility = provider_df.copy()

        provider_credibility["credibility_score"] = (
            (provider_credibility["avg_rating"] / 5.0) * 0.5
            + provider_credibility["booking_success_rate"] * 0.3
            + np.tanh(provider_credibility["interaction_count"] / 100) * 0.2
        )

        credibility_scaler = MinMaxScaler(feature_range=(0, 1))
        provider_credibility["credibility_score"] = credibility_scaler.fit_transform(
            provider_credibility[["credibility_score"]]
        ).flatten()
        provider_credibility["credibility_score"] = provider_credibility[
            "credibility_score"
        ].fillna(0.5)

        user_preferences = (
            interaction_df.groupby("user_id")["provider_id"].apply(list).to_dict()
        )
        return provider_credibility, user_preferences

    def compute_tfidf_scores(self, query: str) -> np.ndarray:
        artifacts = self._require_artifacts()
        query_vector = artifacts.tfidf_vectorizer.transform([query.lower()])
        scores = cosine_similarity(query_vector, artifacts.tfidf_matrix)[0]
        return scores

    def compute_bert_scores(self, query: str) -> np.ndarray:
        artifacts = self._require_artifacts()
        query_embedding = artifacts.bert_model.encode(query, convert_to_numpy=True)
        scores = cosine_similarity([query_embedding], artifacts.provider_embeddings)[0]
        return scores

    def compute_cf_scores(self, user_id: int) -> np.ndarray:
        artifacts = self._require_artifacts()
        provider_df = artifacts.provider_df
        provider_credibility = artifacts.provider_credibility
        cf_scores = provider_credibility["credibility_score"].values.copy()

        if user_id in artifacts.user_preferences:
            user_history = artifacts.user_preferences[user_id]
            for prov_id in user_history:
                provider_idx = provider_df[provider_df["provider_id"] == prov_id].index
                if len(provider_idx) > 0:
                    cf_scores[provider_idx[0]] *= 1.2

        cf_scores = np.clip(cf_scores, 0, 1)
        cf_scores = np.nan_to_num(cf_scores, nan=0.5)
        return cf_scores

    def normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        if len(scores) == 0:
            return scores
        min_score = np.min(scores)
        max_score = np.max(scores)
        if max_score == min_score:
            return np.ones_like(scores) * 0.5
        return (scores - min_score) / (max_score - min_score)

    def combine_scores(
        self,
        tfidf_scores: np.ndarray,
        bert_scores: np.ndarray,
        cf_scores: np.ndarray,
    ) -> np.ndarray:
        tfidf_norm = self.normalize_scores(tfidf_scores)
        bert_norm = self.normalize_scores(bert_scores)
        cf_norm = self.normalize_scores(cf_scores)
        hybrid_scores = (
            WEIGHTS["tfidf"] * tfidf_norm
            + WEIGHTS["bert"] * bert_norm
            + WEIGHTS["cf"] * cf_norm
        )
        return hybrid_scores

    def rank_providers(
        self,
        query: str,
        user_id: int,
        top_k: int = 20,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
    ) -> pd.DataFrame:
        artifacts = self._require_artifacts()

        tfidf_scores = self.compute_tfidf_scores(query)
        bert_scores = self.compute_bert_scores(query)
        cf_scores = self.compute_cf_scores(user_id)
        hybrid_scores = self.combine_scores(tfidf_scores, bert_scores, cf_scores)

        results_df = artifacts.provider_df.copy()
        results_df["tfidf_score"] = tfidf_scores
        results_df["bert_score"] = bert_scores
        results_df["cf_score"] = cf_scores
        results_df["hybrid_score"] = hybrid_scores

        if min_rating > 0 and "rating" in results_df.columns:
            results_df = results_df[results_df["rating"] >= min_rating]

        if max_price is not None and "price_lkr" in results_df.columns:
            results_df = results_df[results_df["price_lkr"] <= max_price]

        if location is not None and "location" in results_df.columns:
            results_df = results_df[results_df["location"].str.lower() == location.lower()]

        results_df = results_df.sort_values("hybrid_score", ascending=False)
        results_df = results_df.head(top_k).reset_index(drop=True)

        output_columns = [
            "provider_id",
            "provider_name",
            "service",
            "location",
            "rating",
            "price_lkr",
            "experience_years",
            "hybrid_score",
            "tfidf_score",
            "bert_score",
            "cf_score",
            "interaction_count",
            "booking_success_rate",
        ]
        results_df = results_df[[col for col in output_columns if col in results_df.columns]]
        return results_df

    def recommend(
        self,
        query: str,
        user_id: int,
        top_k: int = 20,
        min_rating: float = 0.0,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
    ) -> dict:
        self.ensure_loaded()

        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")

        if top_k <= 0 or top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        results_df = self.rank_providers(
            query=query,
            user_id=user_id,
            top_k=top_k,
            min_rating=min_rating,
            max_price=max_price,
            location=location,
        )

        recommendations: list[dict] = []
        for idx, row in results_df.iterrows():
            recommendations.append(
                {
                    "rank": idx + 1,
                    "provider_id": str(row.get("provider_id", "")),
                    "provider_name": str(row.get("provider_name", "")),
                    "service": str(row.get("service", "")),
                    "location": str(row.get("location", "")),
                    "rating": float(row.get("rating", 0.0)),
                    "price": float(row.get("price_lkr", 0.0)),
                    "experience_years": int(row.get("experience_years", 0)),
                    "scores": {
                        "hybrid": float(row.get("hybrid_score", 0.0)),
                        "tfidf": float(row.get("tfidf_score", 0.0)),
                        "bert": float(row.get("bert_score", 0.0)),
                        "cf": float(row.get("cf_score", 0.0)),
                    },
                    "engagement": {
                        "interaction_count": int(row.get("interaction_count", 0)),
                        "booking_success_rate": float(row.get("booking_success_rate", 0.0)),
                    },
                }
            )

        return {
            "status": "success",
            "query": query,
            "user_id": str(user_id),
            "timestamp": datetime.now().isoformat(),
            "total_results": len(recommendations),
            "recommendations": recommendations,
            "weights_used": WEIGHTS,
        }

    def _require_artifacts(self) -> RecommenderArtifacts:
        self.ensure_loaded()
        if self._artifacts is None:
            raise RuntimeError("Component 1 artifacts are not loaded")
        return self._artifacts


_service: HybridRecommenderService | None = None
_service_lock = Lock()


def get_recommender_service() -> HybridRecommenderService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = HybridRecommenderService()
    return _service
