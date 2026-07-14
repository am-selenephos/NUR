# NUR Route Map

Date: 2026-07-11

Presentation authority is the byte-checked V197 host at `apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html` (SHA-256 `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3`). Vite is a zero-visual host and bridge loader. React does not render the visible interface.

## Track A native routes

These URLs serve the same canonical V197 document. The bridge reads `location.pathname`, opens the corresponding existing V197 page/lens, then hydrates it from owner-scoped APIs.

| Route | Existing V197 state | Persisted read/write path | Track A state |
|---|---|---|---|
| `/` | landing/auth threshold | `/api/v1/auth/me`, `/auth/register`, `/auth/login` | live |
| `/today` | Today page | cognition event, Talk, current state, Glow summary | live |
| `/talk` | Talk page | `/cognition/talk`, `/talk-thread`, Journal/Plan/Outcome actions | live; provider is honest when disabled |
| `/journal` | Journal page | `/journal` | live |
| `/plan` | Plan page | `/plans`, `/plan-steps/:id`, `/outcomes` | live |
| `/systems`, `/universe` | Systems Universe | map/orbit/insight summaries, research briefs, Glow | live |
| `/universe/map` | Map lens | `/universe/map-summary` | live read model + real node selection |
| `/universe/orbits` | Orbits lens | `/universe/orbits-summary`, `/orbits` | live read model |
| `/universe/timeline` | Timeline lens | `/universe/timeline` | live owner ledger |
| `/universe/insights` | Insights lens | `/universe/insights-summary` | live owner evidence state |
| `/universe/research` | Research field | `/research/briefs` | live local staging; no invented web data |
| `/universe/community` | Community field | none | honest disabled Track B state |
| `/universe/web-signals` | Web Signals field | local research staging only | honest local state; no live web claim |

## V197-native adjunct routes

These routes serve the same canonical V197 host. The nonvisual bridge mounts a semantic plain-DOM chamber inside the canonical Universe frame; no React visual root or React geometry stylesheet is loaded.

| Route | Backend retained | Presentation state |
|---|---|---|
| `/capsule/:id` | Capsule create/grant/view/ask/revoke/audit | live bounded recipient room or owner lifecycle chamber |
| `/settings` | provider state and owner preferences | live owner preference chamber; export/delete honestly disabled |
| `/universe/omega` | Omega dashboard/export/scheduler | live owner-only evidence dashboard |
| `/universe/omega/review` | owner review queue actions | live owner confirmation gate |
| `/universe/omega/why-changed/:claimId` | why-changed/evidence APIs | live provenance explanation |

The automated source of control truth is `docs/interaction-registry.json`; `button-registry.spec.ts` and `v197-adjuncts.spec.ts` check canonical, modal, mobile and adjunct controls.
