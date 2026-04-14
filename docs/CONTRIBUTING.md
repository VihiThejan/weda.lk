# Contributing

## Branching

- Branch naming: `feature/<scope>-<short-name>`, `fix/<scope>-<short-name>`.
- Keep pull requests focused to one module or feature.

## Conflict-minimizing workflow

1. Claim folder ownership in the task board before coding.
2. Avoid editing shared files unless required.
3. Extract reusable UI into `packages/frontend/src/common` with team review.
4. For backend, keep changes within one layer when possible.

## Code standards

- Frontend: strict TypeScript, small components, named exports.
- Backend: type hints, clear service/repository separation.
- Add tests for changed behavior.

## Pull request checklist

1. Lint and tests pass locally.
2. No unrelated files changed.
3. Architecture boundaries respected.
4. Documentation updated if structure or setup changed.
