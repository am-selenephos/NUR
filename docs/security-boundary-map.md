# NUR Security Boundary Map

Date: 2026-07-09

## Secrets

- OpenAI keys are never stored in source, frontend env, Docker image, screenshots, logs, or packages.
- `infra/scripts/configure-openai-local.sh` writes ignored `.env.local` with hidden input and mode `600`.
- `RUN_NUR.sh openai` fails closed if `.env.local` is missing or incomplete.
- Bootable packages exclude `.env`, `.env.local`, `.env.*`, node_modules, build/dist, test results, proof folders, `.git`, DB volumes, Redis dumps, and secret-like artifacts.

## Owner Data

- Owner records include `owner_user_id` and are protected by RLS.
- New product tables for Research, Community, Web Signals, and provider capabilities use owner-only RLS and `FORCE ROW LEVEL SECURITY`.
- Runtime app role is `nur_app` with no bypass RLS.
- Superuser access is limited to migrations/tests and is not used by runtime API sessions.

## Recipient Capsule Boundary

- Capsule grants expose only approved Orbit sources.
- Recipients cannot access owner Talk, Journal, Timeline, Omega, general memory, or excluded sources.
- Revoked and expired rooms block content and question answering.
- Capsule answers include source refs and do not expose chain-of-thought.

## Omega Boundary

- Omega tables are owner-only.
- Omega UI is hidden behind `NUR_ENABLE_OMEGA_RESEARCH=true`.
- Omega tracks evidence, contradictions, predictions, and learning proposals; it does not claim sentience, AGI, soul, or autonomous real-world action.
- Recipient Capsule isolation from Omega is tested at the API layer.

## Frontend Boundary

- No frontend OpenAI SDK.
- No `VITE_OPENAI_API_KEY` or public key path.
- Visible primary controls are registered in `docs/interaction-registry.md` and enforced by Playwright.
- Honest disabled states are required for future/destructive controls.
