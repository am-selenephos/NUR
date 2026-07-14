# Existing Backend Reuse Inventory

Date: 2026-07-13

| Domain | Existing backend reused | Track A action |
|---|---|---|
| Auth/session/CSRF | `auth_service.py`, auth router, session cookies | Bound V197 signup/signin; no duplicate auth stack. |
| Orbits and seven Systems | Orbit models/routes and universe summaries | Registration/seed provisions the founder seven; map reads existing endpoints. |
| Cognition/Talk | cognition events, Talk service, model runs, provider abstraction | V197 Talk writes through `/cognition/talk`; disabled mode stays honest and real OpenAI mode has a redacted local smoke. |
| Journal | journal routes/models/conversion | V197 save persists and refreshes owner snapshot. |
| Plan/Outcome | plan, step, experiment, outcome routes | V197 composer, step completion, and Outcome are real. |
| Timeline/Insights | universe summary endpoints and Omega ledgers | Existing owner reads hydrate V197 lenses. |
| Preferences/i18n | profile preferences and migration 0010 | Language/writing preference is persisted and owner-scoped. |
| Research/Web Signals | migration 0010, owner-scoped product-surface routers and Timeline provenance | Research/Web questions remain honest local staging; no external source is invented. |
| Community/Group NUR | existing room/member/message/post/comment/reaction/Council migrations and routes | Reused and exposed through bounded V197-native rooms; no duplicate social model. |
| Consultation | room membership and Glow services | Extended with migration 0019 and a five-stage bounded Consultation ledger. |
| AM Projects | existing project/task/run/evidence/review/artifact models and approval gates | Reused through V197-native Project cockpit; external actions still require owner approval. |
| Capsule | shared-orbit models, grants, questions, revoke, RLS | Preserved and bound to recipient/owner V197-native adjunct states. |
| Omega | Omega tables/services/scheduler/review endpoints | Preserved and bound to V197-native dashboard/review/why-changed surfaces. |
| Notifications | audit ledger and owner identity/RLS patterns | Extended with migration 0020 for owner in-app reminders and quiet-hour preferences; no push delivery is claimed. |
| OpenAI | server provider, schemas, verifier, model runs | Preserved and proven locally with a real schema-valid, persisted model response; secret remains server-only. |
| Boot/ops | `RUN_NUR.sh`, Postgres, Redis, worker, beat | Reused; status proves all local processes healthy. |

New backend remains gap-driven: Glow/translation foundations, bounded Group NUR/Consultation, AM Project bindings, and truthful owner notification persistence reuse existing identity, RLS, audit, Timeline and provider layers.
