# Component 1 - Hybrid Multi-Algorithm Recommendation Engine

This module wraps the hybrid recommender from the training notebook into a FastAPI-ready service.

## Location
- Training assets are expected under `training/`.
- You can override the path with `COMPONENT1_TRAINING_DIR`.

## Expected files
- `provider_dataset_100k.xlsx`
- `user_interaction_dataset_120k.xlsx`
- `models/` (optional cache for SentenceTransformer)

## Environment overrides
- `COMPONENT1_TRAINING_DIR`
- `COMPONENT1_PROVIDER_DATASET`
- `COMPONENT1_INTERACTION_DATASET`
- `COMPONENT1_EMBEDDINGS_CACHE`
