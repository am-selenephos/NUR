# FABLE Execution Ledger

Date: 2026-07-12 · Operator: Fable recovery run (exclusive writer)
Pre-edit checkpoint: `~/Downloads/NUR_SAFE_BACKUPS/NUR_FABLE_CHECKPOINT_20260712_pre-recovery.tar.gz`
Checkpoint SHA-256: `646c31175202b176fc3c850e145c4eef543f96a8ac7cc3fa15eb39dfd65f73db`
Checkpoint exclusions verified: no `.env*` values, no `node_modules`, no runtime data, no prior checkpoints (only `.env.example` template present).

Baseline before any edit: `ruff` clean · backend pytest **74/74** on a fresh
`nur_test` database migrated 0001→0016 by the suite itself · runtime healthy in
openai mode.

## Entry 1 — Community membership grants could never succeed (BROKEN → fixed)

- **Issue:** `POST /community/rooms/{id}/members` resolved the invitee with
  `SELECT … FROM users WHERE email=…` through the owner's RLS-scoped session.
  The users-table policy shows a user only themself, so every grant returned
  404 "No active NUR account exists for that exact email" — for accounts that
  exist. Group NUR was unusable beyond a single member.
- **Evidence:** new test battery failed 5/7 on first run with 404 at the
  member-add step; `test_rls.py::test_rls_denies_cross_user_access` documents
  `visible_users == 1`.
- **Repair:** added `fn_active_user_id_by_email(text)` (SECURITY DEFINER,
  `status='active'`, GRANT EXECUTE to `nur_app`) in migration
  `0017_community_glow.py` — the identical pattern capsules already use
  (`fn_user_id_by_email`, migration 0004) — and switched the route to it.
  No table read on `users` was widened.
- **Files:** `apps/api/alembic/versions/0017_community_glow.py`,
  `apps/api/app/api/v1/community.py`.
- **Tests:** `app/tests/test_group_nur.py` (7/7), full suite 82/82.

## Entry 2 — Community/Group/Council actions carried no Glow (§17/§33 gap)

- **Issue:** the Glow source registry had no community source kinds and no
  rules for community events; §33 requires the Glow source to be persisted and
  idempotent for this slice.
- **Repair:** migration `0017_community_glow.py` seeds five server-side rules
  (`community.message_posted` 2/10/70/30s, `community.post_created`
  4/12/84/60s, `community.comment_created` 2/10/70/30s,
  `council.position_added` 4/12/84/60s, `council.decision_recorded`
  6/12/84/0s — base/daily/weekly/spam-window). `glow_service.py` registers the
  five source models and event↔source validation, and refuses Glow for
  DEMO-marked community content. Routes auto-award after persistence with
  deterministic idempotency keys (`{event}:{row_id}`), exactly the
  `living.py::_auto_award` precedent.
- **Law honored:** a cap/anti-spam/DEMO gate (409) or stale-rules deploy
  defect (422) never undoes the persisted action; the response reports
  `AWARDED`, `GLOW_GATED`, or `GLOW_UNAVAILABLE` honestly.
- **Files:** `apps/api/alembic/versions/0017_community_glow.py`,
  `apps/api/app/services/glow_service.py`, `apps/api/app/api/v1/community.py`.

## Entry 3 — Duplicate reaction crashed with a 500

- **Issue:** re-adding the same reaction violated
  `UNIQUE(owner_user_id, target_kind, target_id, reaction)` and surfaced as an
  unhandled IntegrityError.
- **Repair:** pre-check in `create_reaction` returns an honest 409
  "You already added that reaction."
- **Tests:** covered in `test_group_nur.py::test_member_content_persists…`.

## Entry 4 — §33 test battery did not exist (MISSING → created)

- `apps/api/app/tests/test_group_nur.py`: owner room + ledgers; member reads;
  outsider reads nothing (API and raw `nur_app` RLS); message/post/nested
  comment/reaction persistence with server Glow; anti-spam gating persists the
  action while gating the reward; Glow idempotent replay returns the original
  transaction; DEMO content persists but never earns; Council positions,
  member-decision denial, owner decision with minority opinion; membership
  grant validation (unknown email 404, OWNER role 422, duplicate 409,
  non-owner grant 403); private Talk/Journal/Omega rows stay at zero for a
  room member and a second owner at the database layer.

## Entry 5 — V197 Community/Group/Council hydration (interrupted → finished)

- **Issue:** the Community lens still showed the pre-0016 hard-disabled copy
  ("Community is not connected in this Track A build") although the backend
  now persists rooms; §33 requires real rooms or an honest empty state plus
  create/post controls where the backend supports them.
- **Repair:** `v197ApiClient` gained typed community methods and fetches
  `/community/rooms` (+ first active Council summary) in the snapshot;
  `v197Hydration` renders persisted rooms (kind, caller role, DEMO mark),
  an honest empty state, a community world-lens branch and lane cards, and a
  V197-native adjunct control block (create Group room / start Council / post
  message) styled inside the existing premium-polish sheet; `v197Bindings`
  wires the three actions with honest toasts (server-verified Glow points).
  Public-feed tabs stay honestly disabled. The Consultation card now reports
  the real Council room state (positions/decisions counts) instead of a
  Track-B promise.
- **Files:** `apps/web/src/bridge/v197ApiClient.ts`, `v197Hydration.ts`,
  `v197Bindings.ts`, `v197Polish.ts`,
  `apps/web/src/v197/track-a-hydration.test.ts`.
- **Tests:** typecheck clean; vitest **46/46** (two new hydration tests:
  rooms/DEMO/lens rendering, composer honestly disabled without a room).

## Entry 6 — NUR spelling guard (MISSING → created)

- `apps/api/app/tests/test_nur_spelling_guard.py` scans first-party sources,
  docs, scripts, and packaging for the forbidden standalone variant
  (word-boundary, case-insensitive; personal names like "Mahnoor" never
  match). Zero violations at creation time.

## Entry 7 — Feasibility creation died on a Glow cap (BROKEN by §17 law → fixed)

- **Issue:** `POST /api/v1/feasibility` awarded Glow raw; a daily-cap 409
  failed the whole request and rolled the assessment back. Surfaced when the
  demo reseed hit the cap: `bash RUN_NUR.sh disabled` aborted mid-seed.
- **Repair:** the same tolerant pattern `projects.py` already uses — cap/spam
  409 returns `GLOW_GATED` while the assessment persists.
- **Files:** `apps/api/app/api/v1/feasibility.py`.

## Entry 8 — Demo seed stacked duplicate open actions on every boot

- **Issue:** each `RUN_NUR.sh` boot re-created the seeded living
  action + schedule for the demo owner, so repeated boots accumulated open
  duplicates and broke the sol-living "Return to:" proof.
- **Repair:** the seed now reuses a still-SCHEDULED seed action instead of
  creating another; the sol-living spec was made deterministic against a
  legitimately accumulated ledger (misses open actions until the return path
  surfaces — the assertions themselves were not weakened).
- **Files:** `infra/scripts/seed-demo-nur.sh`, `apps/web/e2e/sol-living-v197.spec.ts`.

## Entry 9 — Live Universe strip/lane takeover buried the selected System

- **Issue:** the interrupted run appended `renderLiveUniverse` after
  `renderSelectedSystem`, so the Live Universe facts always overwrote the
  selected System's state strip and signal lane — the System evidence code was
  dead on arrival and the sol-living spec failed.
- **Repair:** the aggregate paints first; an explicitly selected System then
  owns the strip and lane (its Glow scoreboard), and the universe lens
  restores the aggregate on focus.
- **Files:** `apps/web/src/bridge/v197Hydration.ts`.

## Entry 10 — Language save button left the viewport (§30 violation → fixed)

- **Issue:** the provider-status block added to the scope/language chamber
  pushed `#nur-v197-language-save` below the fold of the unscrollable
  canonical modal; the Korean-switch proof could not click it.
- **Repair:** bridge polish rule (no canonical byte edits):
  `#scope-modal .scope-modal { max-height: min(86vh, 780px); overflow-y: auto; }`.
- **Files:** `apps/web/src/bridge/v197Polish.ts`.

## Entry 11 — Interaction registry drift from the interrupted run

- **Issue:** the top-bar language button, Today did-it/missed-it/make-easier,
  check-in inputs, and the Insight review controls were live but unregistered;
  `button-registry.spec.ts` failed its no-unregistered-controls gate.
- **Repair:** registered all of them plus the new community controls
  (`community.rooms` WIRED, `insights.review` WIRED); added an insights-lens
  assertion to `track-a-sellable.spec.ts` and a new browser proof
  `e2e/community-group-nur.spec.ts` (room + message + server Glow verified
  through the live API).
- **Files:** `docs/interaction-registry.json`, `apps/web/e2e/track-a-sellable.spec.ts`,
  `apps/web/e2e/community-group-nur.spec.ts`.

## Final proof (2026-07-12)

- Backend: ruff clean · **82/82** pytest on fresh DB migrated 0001→0017 with
  the real `nur_admin`/`nur_app` role split.
- Web: tsc clean · vitest **46/46**.
- Playwright (serial, chromium-desktop + chromium-mobile): **13 passed, 0
  failed** — track-a-sellable (owner loop, Korean switch, 1440 map geometry),
  sol-living-v197 (Body/Mind/Life, Return-to flow, 35-locale dropdown, map
  containment), track-a-mobile-webkit (chromium projects), button-registry
  (registry complete, no unregistered controls), community-group-nur (new).
- WebKit: UNPROVEN on this host — Playwright needs `libicu74 libxml2
  libflite1` (sudo required). Chromium evidence is not relabeled as WebKit.
- Runtime §36: `RUN_NUR.sh disabled` — healthz `ai_provider: disabled`, ready
  db+redis ok, seed completes. `RUN_NUR.sh openai` (restored, founder's mode)
  — all health gates PASS, model_run + model_response persisted, response
  visible after refresh, Settings shows configured, `key_printed: False`,
  `browser_secret_environment_removed: true`.
- Runtime DB at head `0017_community_glow` with all five community rules and
  `fn_active_user_id_by_email` present (read-only psql verification).
- Post-recovery source package:
  `~/Downloads/NUR_SAFE_BACKUPS/NUR_FABLE_POST_RECOVERY_20260712.tar.gz`,
  SHA-256 `85bda16129deb4e92c242ac5ac590192524e282080c463deb14efe430c595dbe`,
  leak-checked (zero `.env`/node_modules/checkpoint entries).

## Entry 12 — Group NUR member management + conversation + Council flow surfaces

- **Issue:** the member-add repair (entry 1), room conversations, and Council
  positions/decision were backend-complete but unreachable from the product —
  Group NUR was single-user from the V197 surface.
- **Repair:** the community adjunct block gained: invite-by-email
  (`#nur-v197-member-email` + `community-add-member`), Council position input
  (`council-add-position`), and owner decision input
  (`council-record-decision`) — each honestly disabled with an explanatory
  title until a room/Council exists. The community card now also shows the
  latest room's persisted conversation (up to three lines, provenance +
  DEMO-marked, never invented), fetched through the snapshot
  (`GET …/messages?limit=25`).
- **Files:** `apps/web/src/bridge/v197ApiClient.ts`, `v197Hydration.ts`,
  `v197Bindings.ts`, `docs/interaction-registry.json`
  (`community.members`, `council.flow` — both WIRED).
- **Proof:** vitest 46/46 (extended gating/conversation assertions);
  `community-group-nur.spec.ts` extended — the demo owner grants membership to
  `recipient@nur.app`, starts a Council, persists a position, records the
  decision, and every step is re-verified through the live API
  (`memberRoles == [MEMBER, OWNER]`, position present, decision count > 0).

## Entry 13 — Session interruptions and honest environment notes (2026-07-12 evening)

- The host stopped all services mid-session (runtime, system Redis/Valkey);
  the runtime was rebooted via `RUN_NUR.sh` (its own gates green). The system
  `redis.service` could not be restarted without privileges; a user-level
  `redis-server` now serves localhost:6379 for the test harness — it will not
  survive a host reboot (`systemctl start redis` needs sudo).
- Repeated e2e batteries tripped the per-IP registration limiter
  (`rl:register:127.0.0.1` → 429) — the anti-abuse gate working as designed.
  Only the `rl:*` keys were cleared from the runtime Redis before the
  definitive battery; no other runtime state was touched.
- Definitive serial battery after the slice: **13 passed / 0 failed**
  (chromium desktop + mobile, disabled provider mode), backend **82/82**,
  vitest **46/46**, typecheck clean. Runtime restored to openai mode with all
  gates green and `key_printed: False`.

## Entry 14 — Founder-reported: "signup does not take me inside" (2026-07-13)

- **Diagnosis (from api.log, zero 500s):** the founder's attempts first hit
  the per-IP registration limiter (`rl:register:127.0.0.1` reached count 11 —
  burned mostly by the previous evening's e2e batteries, 10 per 5 minutes),
  then returned 400 because the email is already registered (the server
  responds with the deliberately generic "Could not create an Orbit with
  those details." to prevent account enumeration). The entry form showed the
  error only as a small status line, so it read as "nothing happened."
- **Repairs:**
  1. Entry auth failures now render as a prominent warm-ember alert
     (`role="alert"`, `.nur-v197-auth-error`) with an actionable client-side
     hint: duplicate-signup failures add "If this email already has an Orbit,
     use Sign in instead."; limiter failures add "Wait a few minutes, then try
     once." The server message stays generic — no enumeration widening.
  2. `infra/scripts/start-nur.sh` clears `rl:*` keys on the local runtime
     Redis at boot, so a fresh local boot never inherits a burned limiter
     window from an earlier session or test battery. The limiter itself stays
     fully active for the new session.
- **Verification:** headless probe against the live entry (duplicate email)
  shows the visible alert with the hint; typecheck clean; vitest 46/46;
  `community-group-nur.spec.ts` (which signs in through the same entry) green.
- **Honest note:** `e2e/auth.spec.ts` and `e2e/landing-auth.spec.ts` fail
  because they target the retired React landing (`data-testid="tab-register"`
  in `src/routes/Landing.tsx`), which the canonical V197 host superseded.
  They were failing before this change, are not part of the proven battery,
  and are left in place pending a founder decision on retiring them — the
  live entry flow is covered by `track-a-sellable.spec.ts` and
  `community-group-nur.spec.ts`.

## Entry 15 — Fresh-signup auto-entry: proven, and now permanently guarded (2026-07-13)

- **Investigation result:** a never-used email registered against the live
  surface returns `POST /auth/register` **201** with the normal secure session
  cookie (`credentials: "include"` transport), `GET /auth/me` **200** with the
  new user, the V197 bridge hydrates, and the authenticated universe opens
  with no second sign-in; after a browser reload the session survives and the
  universe re-opens (network capture in the recovery scratch log). Register
  already returns a valid session — no second auth path was needed or added,
  no token storage was duplicated, the limiter was not weakened.
- **Root cause of the founder's experience:** not the flow itself — the
  founder's attempts hit (1) the per-IP register limiter burned by e2e
  batteries, then (2) duplicate-email 400s (entry 14). No spec had pinned the
  fresh-registration auto-entry explicitly, so it was also formally unproven.
- **New proof — `e2e/fresh-signup.spec.ts` (3 tests):** fresh unique email →
  201 asserted from the real network response (payload email + PERSONAL_BRIDGE
  orbit), authenticated shell + Today visible, `/auth/me` returns the new
  user, reload → session survives (Today restored) with no manual login;
  duplicate email → 400 with the readable Sign-in hint and **no** fake
  authenticated state (`/auth/me` 401, universe never opens); invalid input
  never reaches the API. Unit tests add the 429 retry-message and
  no-fake-auth-state assertions (vitest 48/48).
- **Battery determinism:** `e2e/global-setup.ts` clears only `rl:*` limiter
  keys before a run — the same isolation the unit harness already performs
  with `flushdb` — and `sol-living-v197.spec.ts`'s Glow assertion now encodes
  the §17 law exactly (award grows lifetime; a reached daily cap gates the
  reward while the completed action still persists).
- **Files:** `apps/web/e2e/fresh-signup.spec.ts` (new),
  `apps/web/e2e/global-setup.ts` (new), `apps/web/playwright.config.ts`,
  `apps/web/e2e/sol-living-v197.spec.ts`,
  `apps/web/src/v197/track-a-actions.test.ts`.
- **Final:** full serial chromium battery **16 passed / 0 failed** (disabled
  proof mode); typecheck clean; runtime restored to openai with gates green.

## Remaining risks / honest notes

- Glow idempotency is key-based; a caller inventing new keys against the same
  source is bounded by per-rule daily/weekly caps and spam windows, not by a
  per-source uniqueness constraint. Pre-existing design across all sources.
- Council ORIENT/GATHER/MAP/MOVE/RETURN staged flow, posts/comments V197
  surfaces, room-member management UI, and Room leaderboards remain backend-
  complete but V197-surface-partial: rooms, composer, and Council state are
  hydrated; the deeper flows are still API-only.
- WebKit e2e depends on host libraries; see FABLE_RECOVERY_STATUS.md for the
  honest per-browser verdict of the latest run.
