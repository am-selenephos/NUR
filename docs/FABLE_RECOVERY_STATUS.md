# FABLE Recovery Status

Date: 2026-07-12 · Scope: recovery + completion of the interrupted
Community/Group NUR/Council edge (§33 gate) plus regression proof.
Companion evidence: `docs/FABLE_EXECUTION_LEDGER.md`.

## How each verdict was earned

Every verdict below names its evidence. "Fresh-DB" means the backend test
bootstrap dropped and recreated `nur_test`, ran `alembic upgrade head`
(0001→0017) as `nur_admin`, and connected as `nur_app` (NOBYPASSRLS) — the
production role split, executed on every pytest run.

## Interrupted-edge verdicts

| Area | Verdict | Evidence |
| --- | --- | --- |
| Migration 0016 (rooms/memberships/messages/posts/comments/reactions/positions/decisions, FORCE RLS, composite ownership FKs) | VERIFIED_COMPLETE | Fresh-DB migration in every pytest run; RLS battery in `test_group_nur.py` |
| Community/Group/Council API routes | VERIFIED_COMPLETE (one BROKEN route repaired) | Member-add could never resolve an invitee under RLS — fixed via `fn_active_user_id_by_email` SECURITY DEFINER (ledger entry 1); 82/82 suite green |
| Community/Group/Council permission tests | CREATED (was MISSING) | `app/tests/test_group_nur.py`, 7 tests covering the full §33 battery |
| Community Glow (server-calculated, source-linked, idempotent, capped, DEMO-refused) | CREATED (was MISSING) | Migration 0017 rules + `glow_service` registry + route auto-award; tests prove idempotent replay and gated-but-persisted actions |
| V197 Community lens hydration | VERIFIED_COMPLETE for rooms/composer/Council state; VERIFIED_PARTIAL for deeper flows | Real rooms with roles + DEMO marks, honest empty state, create-room/start-Council/post-message adjunct controls, community world lens + lane cards; posts/comments/member-management surfaces remain API-only |
| Council facilitation | VERIFIED_PARTIAL | Positions/decisions/minority opinion/return-check persist and are tested; V197 shows Council state counts; staged ORIENT→RETURN flow UI not yet built |
| Demo seeding | VERIFIED_COMPLETE | `RUN_NUR.sh openai` reseeded demo owner/recipient with explicit credentials output |
| Secret handling | VERIFIED_COMPLETE | OpenAI smoke reports `key_printed: False`, `browser_secret_environment_removed: true`; keys stay in ignored `.env.local` |

## Regression verdicts (previously implemented areas)

| Area | Verdict | Evidence |
| --- | --- | --- |
| Auth/sessions/RLS core | VERIFIED_COMPLETE | `test_auth`, `test_rls` green on fresh DB |
| Sol living system (Today, Body/Mind/Life, systems, goals, schedules) | VERIFIED_COMPLETE | `test_sol_living_system` green |
| AM Projects (runs, evidence, reviews, glow) | VERIFIED_COMPLETE | `test_am_projects` green |
| Live Universe aggregator | VERIFIED_COMPLETE | `test_live_universe` green |
| Live intelligence / structured outputs / provider failures | VERIFIED_COMPLETE | `test_live_intelligence`, `test_ai_structured_outputs`, `test_ai_provider_failures` green |
| Capsules (bounded sharing, revocation, RLS) | VERIFIED_COMPLETE | `test_capsules` green |
| Omega owner-only ledgers | VERIFIED_COMPLETE | `test_omega` green + omega isolation asserted in `test_group_nur` |
| Web bridge unit surface (hydration, actions, contract, i18n host) | VERIFIED_COMPLETE | typecheck clean, vitest 46/46 |
| Runtime boot (openai mode) | VERIFIED_COMPLETE | `RUN_NUR.sh openai` exit 0: healthz/readyz/metrics gates, model_run + model_response persisted, response visible after refresh, Settings shows configured |
| NUR spelling law | GUARDED | New `test_nur_spelling_guard.py`; zero standalone forbidden variants in first-party material |

## Browser proof of this run (final)

Serial Playwright battery, chromium-desktop + chromium-mobile: **13 passed,
0 failed** — `track-a-sellable` (owner loop, disabled-provider Talk honesty,
Korean language switch, 1440 map geometry), `sol-living-v197` (Body/Mind/Life,
missed→Return-to→completed flow with Glow, 35-locale dropdown, systems inside
map bounds), `track-a-mobile-webkit` (chromium projects), `button-registry`
(registry internally complete, zero unregistered controls, honest-disabled
checks), and the new `community-group-nur` (room created and message persisted
through exact V197 controls with a server-verified Glow transaction).

Five regressions/defects from the interrupted edge were repaired to get here —
see `FABLE_EXECUTION_LEDGER.md` entries 7–11 (feasibility Glow-cap rollback,
seed duplicate stacking, Live Universe strip/lane takeover, language-save
viewport clipping, interaction-registry drift).

## Not proven in this run (honest boundary)

- WebKit: Playwright reports missing host libraries (`libicu74`, `libxml2`,
  `libflite1`; sudo required to install). WebKit remains UNPROVEN on this
  host; Chromium evidence is never relabeled as WebKit.
- Full 35-locale review status remains as documented in
  `docs/35-language-translation-engine.md`; the dropdown's 35 options and the
  Korean end-to-end switch are browser-proven, per-locale copy review is not.
- The full nine-width geometry battery beyond the proven 1440/mobile
  assertions stands on the earlier verdicts in `docs/v197-performance-report.md`.
