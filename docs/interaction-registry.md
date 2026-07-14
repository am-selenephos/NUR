# V197 Interaction Registry - Track A

Date: 2026-07-11

Canonical source SHA: `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3`.

Status law:

- `WIRED`: action reaches a real route/API or persists owner state.
- `SOURCE_NATIVE`: canonical V197 visual/navigation behavior with no server-state claim.
- `HONEST_DISABLED`: visible control is blocked and names the unavailable Track A capability.

## Entry and auth

| Selector | Action | Backend | Status | Proof |
|---|---|---|---|---|
| `#f4-brand`, `#f4-begin`, `#f4-signin`, `#f4-what`, `[data-switch]`, `#f4-close` | return home/open/switch/close canonical V197 entry chambers | none | `SOURCE_NATIVE` | Track A desktop E2E |
| `#f4-signup-form input`, `#f4-consent-check`, `#f4-signup-form button[type=submit]` | validate and create owner/session/seven Systems | `POST /api/v1/auth/register` | `WIRED` | `track-a-sellable.spec.ts` |
| `#f4-signin-form input`, `#f4-signin-form button[type=submit]` | establish cookie session and enter Universe | `POST /api/v1/auth/login`, `GET /auth/me` | `WIRED` | desktop/mobile/WebKit E2E |

## Navigation and lenses

| Selector | Action | Backend | Status |
|---|---|---|---|
| `[data-page]` | Today/Talk/Journal/Plan/Systems + outer route | owner snapshot reads | `WIRED` |
| `.universe-nav-tabs [data-world-tab]` | Universe/Map/Orbits/Timeline/Insights lens + route | `/universe/*-summary` | `WIRED` |
| `[data-world-focus]` | canonical Research/Community/Web/Consultation/lens focus | Research is real local staging; Community/Consultation are honest states | `WIRED` or `HONEST_DISABLED` by state |
| `.universe-system-node[data-orbit-id]`, `.clean-system-row[data-orbit-id]` | persist selected owner System | `PATCH /profile/preferences` | `WIRED` |
| `.universe-search input` + Enter | owner-ledger search | `GET /universe/search` | `WIRED` |
| `.universe-deep`, `#open-web-search` | open canonical Research focus | local route/read model | `SOURCE_NATIVE` |
| `[data-context-tab]`, `[data-research-tab]` | switch existing V197 local panel | none | `SOURCE_NATIVE` |

## Today, Talk, Journal, Plan, Outcome, Glow

| Selector | Action | Backend | Status |
|---|---|---|---|
| `#today-input`, `[data-send=today]` | persist check-in, Talk turn, and eligible reward | cognition + Talk + Glow APIs | `WIRED` |
| `#talk-input`, `[data-send=talk]`, `#mobile-composer`, `[data-send=mobile]` | stream and persist selected-language Talk | `POST /cognition/talk/stream` | `WIRED` |
| `[data-action=talk-cancel]` (visible only during a live turn) | cancel the active provider run without persisting partial model text | `POST /cognition/talk-runs/:request_id/cancel` | `WIRED` |
| `.universe-prompt-row [data-action]` | set Talk/Plan mode without fake persistence | local mode; send uses Talk/Plan API | `WIRED` |
| `[data-thread-action=private]` | keep thread in owner boundary | no widening action | `SOURCE_NATIVE` |
| `[data-thread-action=journal]` | move latest persisted Talk into Journal draft | local draft only until Save | `WIRED` |
| `[data-thread-action=plan]` | create Plan from latest Talk | `POST /plans` | `WIRED` |
| `[data-thread-action=glow]` | idempotently reward an already persisted Talk | `POST /glow/rewards` | `WIRED` |
| `#journal-input`, `#journal-save` | persist private Journal entry | `POST /journal` | `WIRED` |
| `[data-journal-prompt]` | seed the Journal composer with a canonical prompt | none | `SOURCE_NATIVE` |
| `.plan-check[data-plan-step-id]` | complete/reopen persisted step | `PATCH /plan-steps/:id` | `WIRED` |
| `[data-action=make-easier]` | persist smaller step title | `PATCH /plan-steps/:id` | `WIRED` |
| `#nur-outcome-input`, `[data-action=return-outcome]` | create Outcome, then persisted Glow | `POST /outcomes`, `POST /glow/rewards` | `WIRED` |

## Systems, Research, scope, and hidden modal controls

| Selector | Action | Backend | Status |
|---|---|---|---|
| `#universe-composer-input`, `.universe-send`, `[data-action=add-system]` | Talk/Plan or create owner System according to mode | cognition/plans/orbits | `WIRED` |
| `#research-query`, `[data-research-submit]` | save local research question without invented sources | `POST /research/briefs` | `WIRED` |
| `#scope-open`, `#talk-scope`, `[data-open-scope]`, `.scope-modal-close` | open/close canonical boundary chamber | none | `SOURCE_NATIVE` |
| `[data-context-action]` | explain existing owner boundary/ledger state | none | `SOURCE_NATIVE` |
| `.scope-option[data-scope]`, `.v172-scope-option[data-scope]` | persist owner default boundary | `PATCH /profile/preferences` | `WIRED` |
| `#nur-v197-locale`, `#nur-v197-writing-preference`, `#nur-v197-language-save` | persist language/writing preference | `PATCH /profile/preferences` | `WIRED` |
| `[data-community-tab]`, `[data-stage]`, `.consultation-question button` | explain unavailable Community/Consultation state | none | `HONEST_DISABLED` |
| `[data-action=ritual]` | explain unavailable ritual scheduler | none | `HONEST_DISABLED` |
| `[data-track-a-action=edit-direction]` | explain unavailable Plan direction editor | none | `HONEST_DISABLED` |
| `.composer-action--voice` | explain unavailable voice input | none | `HONEST_DISABLED` |
| `#iSpark`, `#burst-btn`, `.nur-user` | canonical star/burst visual response only | none | `SOURCE_NATIVE` |
| `#nur-v197-owner-auth-menu [data-action='auth-logout']` | end the secure owner session and return to Entry | `POST /api/v1/auth/logout` | `WIRED` |

## V197-native visual adjuncts

| Route / selector | Action | Backend | Status | Proof |
|---|---|---|---|---|
| `/capsule/:id` + `[data-adjunct-action=capsule-ask]` | read only included sources and ask a source-bound question | `GET /capsules/:id/view`, `POST /capsules/:id/questions` | `WIRED` | `v197-adjuncts.spec.ts` desktop/mobile/real WebKit |
| `/capsule/:id` owner audit/revoke controls | inspect access ledger and close the room | `GET /capsules/:id/audit`, `POST /capsules/:id/revoke` | `WIRED` | backend Capsule/RLS tests + adjunct E2E |
| `/settings` language, writing, sound, motion, Omega controls | persist owner preferences; show provider status without a key | `GET/PATCH /profile/preferences`, `GET /healthz` | `WIRED` | `v197-adjuncts.spec.ts` |
| `/settings` export/delete | visible truthful beta boundary | none | `HONEST_DISABLED` | `v197-adjuncts.spec.ts` visual state |
| `/universe/omega*` dashboard/review/why-changed/export controls | inspect and govern owner evidence, reviews, claims and consolidation | `/omega/*` | `WIRED` | `v197-adjuncts.spec.ts` desktop/mobile/real WebKit |
| `/consultations*` create/contribute/stage controls | persist bounded ORIENT→GATHER→MAP→MOVE→RETURN work without erasing disagreement | `/consultations/*` | `WIRED` | `v197-adjuncts.spec.ts` + `test_consultations.py` |
| `/community*` room/thread/comment/reaction controls | render and mutate only persisted bounded room records | `/community/rooms/*` | `WIRED` | `v197-adjuncts.spec.ts` + `test_group_nur.py` |
| `/community/people`, `/community/saved`, `/community/moderation` | name the unavailable public-network state and return to bounded Community | none | `HONEST_DISABLED` | `v197-adjuncts.spec.ts` visual state |
| `/projects*` Project/task/evidence/run/review controls | expose owner project ledger and approval gates; never pre-authorize external action | `/projects/*` | `WIRED` | `v197-adjuncts.spec.ts` + `test_am_projects.py` |
| `/glow` balance/level/quest/streak/ledger controls | render persisted reward state only | `/glow/summary`, `/glow/scoreboard` | `WIRED` | `sol-live-new-surfaces.spec.ts` + Glow backend tests |
| `/notifications` reminder/read/frequency/quiet-hour controls | persist owner-written re-entry cues and preferences; no fake human ping | `/notifications*` | `WIRED` | `v197-adjuncts.spec.ts` + `test_notifications.py` |

Machine-readable selectors and statuses are in `docs/interaction-registry.json`. `button-registry.spec.ts` checks canonical Entry/auth/page/modal/mobile controls; `v197-adjuncts.spec.ts` opens hidden adjunct states and clicks their registered controls.
