# Backend Service

FastAPI + MongoDB backend using layered architecture.

## Run locally

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Copy `.env.example` to `.env`
4. Start server: `uvicorn app.main:app --reload --port 8000`

## Layers

- `app/api`: HTTP routing layer.
- `app/services`: Business logic layer.
- `app/repositories`: Data access layer.
- `app/schemas`: Request/response contracts.
- `app/models`: Persistence-oriented models.
