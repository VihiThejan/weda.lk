# Architecture

## Monorepo

- packages/frontend: React + TypeScript client.
- packages/backend: FastAPI + MongoDB API.
- docs: Team process and architecture records.

## Frontend boundaries

- common: Reusable primitives and layout components.
- features: Feature-specific business modules.
- router: Route configuration and shell usage.

Rules:
1. Feature code should not import directly from other feature internals.
2. Shared components go in common only when at least two features need them.
3. Keep route-level pages in feature `pages` folders.

## Backend boundaries

- api: Request/response layer.
- services: Business use cases.
- repositories: MongoDB persistence operations.
- schemas: Pydantic DTO contracts.
- core: App config and infrastructure.

Rules:
1. Routes call services, not repositories directly in new features.
2. Repository methods should be persistence-focused and reusable.
3. Keep environment and connection logic inside core.
