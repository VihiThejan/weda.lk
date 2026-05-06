from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent


def _find_repo_root(start_dir: Path) -> Path:
    current = start_dir
    for _ in range(8):
        if (current / "packages").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return start_dir


def _resolve_training_dir() -> Path:
    env_value = os.getenv("COMPONENT1_TRAINING_DIR")
    if env_value:
        return Path(env_value)

    local_dir = BASE_DIR / "training"
    if local_dir.exists():
        return local_dir

    repo_root = _find_repo_root(BASE_DIR)
    legacy_dir = repo_root / "model-test"
    return legacy_dir


@dataclass(frozen=True)
class Component1Paths:
    training_dir: Path
    models_dir: Path
    provider_dataset: Path
    interaction_dataset: Path
    embeddings_cache: Path


def get_paths() -> Component1Paths:
    training_dir = _resolve_training_dir()
    models_dir = training_dir / "models"

    provider_dataset = Path(
        os.getenv("COMPONENT1_PROVIDER_DATASET", str(training_dir / "provider_dataset_100k.xlsx"))
    )
    interaction_dataset = Path(
        os.getenv(
            "COMPONENT1_INTERACTION_DATASET",
            str(training_dir / "user_interaction_dataset_120k.xlsx"),
        )
    )
    embeddings_cache = Path(
        os.getenv("COMPONENT1_EMBEDDINGS_CACHE", str(training_dir / "provider_embeddings.npy"))
    )

    return Component1Paths(
        training_dir=training_dir,
        models_dir=models_dir,
        provider_dataset=provider_dataset,
        interaction_dataset=interaction_dataset,
        embeddings_cache=embeddings_cache,
    )
