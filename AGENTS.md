# StepZero Project Rules

## Scope
- These rules apply only to this repository.
- If session-level instructions conflict, session-level instructions win.

## Collaboration Rules
- Use Git-Flow branch strategy:
- `main`: production-ready only, no direct push.
- `develop`: integration branch for ongoing development.
- `feature/*`: feature development branches.
- Branch naming for features: `feature/<issue-number>-<short-slug>` (example: `feature/1-login-page`).
- Commit message format must follow Conventional Commits: `type: subject`.
- Allowed commit types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`.
- PR title and PR description must be written in Korean so team members can review consistently.
- PR description should be concise and human-readable; do not paste raw terminal logs into PR body.

## Frontend Rules
- Run frontend dev server with `npm run dev` (configured as `next dev --webpack`).
- If `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is empty, the app must still render (graceful fallback).
- For UI data loading, always provide loading, error, and empty states.

## Backend Rules
- Environment load priority is `.env.local` then `.env`.
- `.env` must contain non-secret template values only.
- Any DB schema change requires an Alembic migration.
- Alembic migrations must be safe on pre-existing local DBs (idempotent where needed).

## API Rules
- Keep v1 compatibility for existing clients.
- Implement new endpoints/features in v2 first.
- When deprecating v1 behavior, add explicit deprecation signals in API responses/docs.

## Quality Gates
- Before concluding backend changes, run `cd app-backend && .venv/bin/pytest -q`.
- Before concluding frontend changes, run `cd app-frontend && npm run lint`.
- If migrations changed, run `cd app-backend && ./scripts/check_migrations.sh`.

## Security Rules
- Never print secrets in full (API keys, tokens, passwords).
- Secret checks must only report presence/format, not raw values.
- Temporary diagnostics files must not be committed.

## Artifact Rules
- Store test/debug artifacts under `.temp/artifacts/` instead of repository root.
- Prefer removing one-off artifacts after verification; keep only files needed for follow-up debugging.
- If artifact retention is needed, keep them grouped by purpose in a single subfolder.
