# NUR

NUR is a local-first scoped beta for private project orbit work: Talk, Systems,
Project Orbit, Context Capsules, and the hidden NUR-Omega research layer.

This repository is bootable in local development mode. `START_NUR.sh` is the
human-facing launcher: on first interactive use it securely configures real
server-side OpenAI, then starts the complete system. `RUN_NUR.sh` remains the
operator runner and defaults to honest disabled mode when no mode is supplied.
OpenAI configuration writes only an ignored, mode-600 `.env.local`.
Do not place API keys in source, screenshots, logs, or zip artifacts.

## Quick Boot

```bash
bash START_NUR.sh
```

Linux users can double-click `START_NUR.desktop`. The first launch asks for an
OpenAI key with hidden input; later launches are one click. The distributable
ZIP never includes that key.

Open `http://localhost:5173`.

The root runner starts Postgres, Redis, FastAPI, the worker, Omega scheduler,
Vite, demo seed, health checks, and browser open as one local system. Use
`bash RUN_NUR.sh status`, `logs`, `seed`, `stop`, `doctor`, `reset-demo`, or
`package` for follow-up operations.

## Main Surfaces

- Web app: `apps/web`
- API: `apps/api`
- Shared TypeScript package: `packages/shared-types`
- Postgres/Redis compose: `docker-compose.yml`, `docker-compose.dev.yml`
- Boot scripts: `infra/scripts`
- Alembic migrations: `apps/api/alembic/versions`

## Omega v1

Omega is a research layer, not a consciousness, AGI, sentience, soul, or
autonomous real-world actor. It stores owner-scoped experiences, claims,
evidence edges, contradictions, predictions, learning proposals, review queue
items, and consolidation runs under forced Postgres RLS.

The hidden UI is available only when `VITE_NUR_ENABLE_OMEGA_RESEARCH=true`:

- `/universe/omega`
- `/universe/omega/review`

## Tests

```bash
python -m pytest apps/api/app/tests -q
npm --workspace apps/web run typecheck
npm --workspace apps/web test -- --run
VITE_NUR_ENABLE_OMEGA_RESEARCH=true npm --workspace apps/web run e2e -- e2e/omega-research.spec.ts --project=chromium-desktop
```

See `QUICKSTART_BOOT.md`, `RUNBOOK.md`, `DEMO_SCRIPT.md`, and
`SECURITY_NOTES.md` for the full local flow.
