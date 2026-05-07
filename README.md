# AI/ML Driven Maintenance Service Provider Platform (Sri Lanka)

Monorepo with React (TypeScript) frontend, FastAPI backend, and MongoDB 6.0+.

## Quick Start

1. Install pnpm and Node.js 20+.
2. Install Python 3.11+.
3. Copy env files:
   - `packages/backend/.env.example` to `packages/backend/.env`
4. Install dependencies:
   - `pnpm install`
   - backend Python dependencies from `packages/backend/README.md`
5. Run apps:
   - Frontend: `pnpm dev` (from repo root)
   - Backend: `cd packages/backend` then `python -m uvicorn app.main:app --reload`

## Repository Layout

- `packages/frontend`: React app with reusable shared components.
- `packages/backend`: FastAPI service with layered architecture.
- `docs`: Architecture and collaboration guidelines.
