# V197 Control to Backend Map

Date: 2026-07-11  
Authority: `NUR_ULTIMATE_FOUNDER_MASTER_PROMPT_SOL_ULTRA.md` sections 7, 28, 33, and 35.

## Runtime boundary

`apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html` owns the outer entry/universe iframes. The exact decoded V197 documents own all visible DOM, CSS, stars, typography, layout, and native interaction. `apps/web/src/bridge/v197Bridge.ts` attaches after both frames load and delegates to:

- `v197ApiClient.ts`: cookie/CSRF API transport and owner snapshot;
- `v197Bindings.ts`: write/event bindings;
- `v197Hydration.ts`: read-only copy/data mutation in existing V197 slots;
- `v197I18n.ts`: locale/direction and the scope-chamber selector;
- `v197Rewards.ts`: persisted Glow rendering;
- `v197Polish.ts`: bridge-scoped geometry corrections without canonical-byte edits.

No React component owns a visible V197 node. `#root` is absent from the canonical host.

## Track A bindings

| V197 control/state | Bridge action | Backend | Persistence proof |
|---|---|---|---|
| signup/signin forms | register/login and reveal universe | `/api/v1/auth/*` | session survives navigation |
| Today composer | store check-in, Talk turn, eligible Glow | cognition + Glow | refreshed owner snapshot |
| Talk composer | send locale-aware turn | `/api/v1/cognition/talk` | thread and model/disabled response reload |
| Talk to Journal | seed canonical Journal input | save occurs through `/journal` | owner Journal reload |
| Talk to Plan | create Plan from persisted turn | `/plans` | Plan/step reload |
| Journal Save | create private entry | `/journal` | Journal reload |
| Plan check | complete/reopen owner step | `/plan-steps/:id` | state reload |
| Make easier | shorten persisted step | `/plan-steps/:id` | state reload |
| Return outcome | create Outcome, then request Glow | `/outcomes`, `/glow/rewards` | Timeline + Glow balance |
| Add System | create owner Orbit/System | `/orbits` | map/orbit summaries |
| System node | select active owner Orbit | `/profile/preferences` | selection reload |
| Search | owner-scoped ledger query | `/universe/search` | read only |
| Research stage | save local brief | `/research/briefs` | Research reload |
| Boundary choice | save default boundary | `/profile/preferences` | scope reload |
| language/writing | save locale and writing preference | `/profile/preferences` | refresh + Talk metadata |

## Community / Group NUR / Council bindings (Fable recovery, 2026-07-12)

| V197 control/state | Bridge action | Backend | Persistence proof | Status |
|---|---|---|---|---|
| Create Group room (`[data-action="community-create-room"]`, adjunct `#nur-v197-community-controls`) | create bounded room; owner auto-membership | `POST /community/rooms` | rooms reload + actor Timeline/audit rows | WIRED_REAL |
| Start Council (`[data-action="community-create-council"]`) | create COUNCIL room | `POST /community/rooms` | Consultation card shows persisted position/decision counts | WIRED_REAL |
| Post to room (`[data-action="community-post-message"]`, `#nur-v197-room-message`) | persist member message; server auto-awards idempotent Glow (`community.message_posted`) | `POST /community/rooms/:id/messages` | message + Glow transaction reload; DEMO content never earns | WIRED_REAL |
| Community card + `/universe/community` lens/lane | render persisted rooms with kind, caller role, DEMO marks; honest empty state | `GET /community/rooms` (+ Council `GET …/summary`) | snapshot reload | WIRED_REAL |
| Public-feed tabs (`[data-community-tab]`) | remain disabled; no external feed is faked | — | — | WIRED_DISABLED_HONEST |
| Add member (`#nur-v197-member-email`, `[data-action="community-add-member"]`) | grant MEMBER role by exact account email (SECURITY DEFINER lookup) | `POST /community/rooms/:id/members` | `community-group-nur.spec.ts` (recipient@nur.app grant) | WIRED_REAL |
| Council position (`#nur-v197-council-position`, `[data-action="council-add-position"]`) | persist member position; minority stays on ledger; server Glow | `POST /community/rooms/:id/positions` | `community-group-nur.spec.ts` | WIRED_REAL |
| Council decision (`#nur-v197-council-decision`, `[data-action="council-record-decision"]`) | owner-only decision with server Glow; member attempt is an honest 403 | `POST /community/rooms/:id/decision` | `community-group-nur.spec.ts` | WIRED_REAL |
| Latest room conversation (community card items) | up to three persisted messages, provenance + DEMO marks | `GET /community/rooms/:id/messages` | `track-a-hydration.test.ts` | WIRED_REAL |
| Council staged ORIENT→RETURN guided flow (`[data-stage]`, `.consultation-question button`) | stage chips stay disabled; position/decision persistence is live above | backend complete | `test_group_nur.py` | NEEDS_UI_SURFACE |

## Honest states

- Consultation staged flow, ritual scheduling, voice, and Plan direction editing remain visible but disabled with a complete explanation. Community rooms, the room composer, and Council state are live against the 0016/0017 backend as of this recovery run.
- No live people, replies, rooms, sources, or web activity are invented; only persisted owner-scoped rooms are shown, and seeded content must carry the DEMO mark.
- Capsule, Settings, and Omega visuals are deferred V197-native adjuncts and return explicit 404 responses; their backend modules are not deleted.

The exact selector-level inventory is `docs/interaction-registry.json`, enforced by `apps/web/e2e/button-registry.spec.ts`.
