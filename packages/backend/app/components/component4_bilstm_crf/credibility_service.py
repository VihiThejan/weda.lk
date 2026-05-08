from __future__ import annotations

import json
import logging
from threading import Lock
from typing import Optional

from .config import get_paths

logger = logging.getLogger(__name__)


def _provider_scores_csv_candidates(paths) -> list:
    repo_root = paths.model_dir.parents[5] if len(paths.model_dir.parents) > 5 else paths.model_dir.parent
    return [
        paths.provider_scores_path.with_suffix('.csv'),
        repo_root / 'Component4 new' / 'component4_model' / 'provider_scores.csv',
        repo_root / 'Component4' / 'component4_model' / 'provider_scores.csv',
    ]


class CredibilityService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._loaded = False
        self._df = None
        self._blend_cfg: dict = {}
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
            self._load_artifacts()
            self._loaded = True

    def _load_artifacts(self) -> None:
        import pandas as pd

        paths = self._paths
        csv_candidates = _provider_scores_csv_candidates(paths)

        def _read_csv_fallback() -> object:
            for candidate in csv_candidates:
                if candidate.exists():
                    return pd.read_csv(str(candidate))
            return None

        if not paths.provider_scores_path.exists():
            df = _read_csv_fallback()
            if df is None:
                raise FileNotFoundError(
                    f"provider_scores.parquet not found at {paths.provider_scores_path}"
                )
        if not paths.blend_config_path.exists():
            raise FileNotFoundError(
                f"blend_config.json not found at {paths.blend_config_path}"
            )

        if 'df' not in locals():
            try:
                df = pd.read_parquet(str(paths.provider_scores_path))
            except ImportError as exc:
                # Parquet engine not available (pyarrow/fastparquet). Try CSV fallbacks.
                df = _read_csv_fallback()
                if df is None:
                    raise RuntimeError(
                        "Parquet support is not available (install 'pyarrow' or 'fastparquet'), "
                        f"or provide a CSV at one of: {', '.join(str(p) for p in csv_candidates)}"
                    ) from exc
        if 'provider_id' in df.columns:
            df['provider_id'] = df['provider_id'].astype(str)
            df = df.set_index('provider_id')

        self._df = df

        with open(paths.blend_config_path) as f:
            self._blend_cfg = json.load(f)

        logger.info("Credibility service loaded: %d provider scores", len(df))

    def _assign_tier(self, s_final: float) -> str:
        thresholds = self._blend_cfg.get(
            'tier_thresholds', {'Elite': 0.8, 'Trusted': 0.65, 'Verified': 0.0}
        )
        if s_final >= thresholds.get('Elite', 0.8):
            return 'Elite'
        if s_final >= thresholds.get('Trusted', 0.65):
            return 'Trusted'
        return 'Verified'

    def get_provider_credibility(self, provider_id: str) -> Optional[dict]:
        self.ensure_loaded()
        pid = str(provider_id)
        if pid not in self._df.index:
            return None

        row = self._df.loc[pid]
        s_final = float(row.get('S_final', 0.0))
        result: dict = {
            'provider_id': pid,
            'S_final': round(s_final, 4),
            'tier': self._assign_tier(s_final),
        }
        for col in ('S_cred', 'S_overall', 'fraud_ratio', 'recency_boost',
                    'avg_rating', 'total_reviews', 'suspicious_count'):
            if col in row.index:
                val = row[col]
                result[col] = round(float(val), 4) if val is not None else None

        return result

    def rank_providers(self, provider_ids: list[str]) -> list[dict]:
        self.ensure_loaded()
        known, unknown = [], []
        for pid in provider_ids:
            cred = self.get_provider_credibility(pid)
            if cred:
                known.append(cred)
            else:
                unknown.append({'provider_id': str(pid), 'S_final': None, 'tier': 'Unknown'})

        known.sort(key=lambda x: x['S_final'], reverse=True)
        ranked = []
        for rank, entry in enumerate(known + unknown, 1):
            entry['rank'] = rank
            ranked.append(entry)
        return ranked

    @property
    def total_providers(self) -> int:
        if self._df is not None:
            return len(self._df)
        return 0


_credibility_service: CredibilityService | None = None
_credibility_lock = Lock()


def get_credibility_service() -> CredibilityService:
    global _credibility_service
    if _credibility_service is None:
        with _credibility_lock:
            if _credibility_service is None:
                _credibility_service = CredibilityService()
    return _credibility_service
