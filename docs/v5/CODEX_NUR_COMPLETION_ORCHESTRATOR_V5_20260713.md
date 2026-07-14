# CODEX NUR Completion Orchestrator v5

Paste/queue this as **one task in the actual latest NUR repository**. Do not steer another task into it while it is running.

---

## Command

You are the implementation and verification operator for NUR. Continue from the current repository state; do not replace it with an older ZIP, branch, prototype, or clean-room rewrite.

Your terminal objective is:

```text
CURRENT SOURCE RECONCILED
→ AUTH + V197 + PERFORMANCE STABLE
→ LIVE AI ENABLED AND PROVEN
→ ACCOUNT RECOVERY COMPLETE
→ INTELLIGENCE SPINE COMPLETE
→ REVENUE SPINE COMPLETE
→ GLOW + SEVEN SYSTEMS COMPLETE
→ 35-LANGUAGE ARCHITECTURE COMPLETE
→ REAL COMMUNITY + GROUP NUR + RESEARCH COMPLETE
→ PROJECTS/AGENTS + PWA/OPS COMPLETE
→ ALL REQUIRED GATES GREEN
→ CLEAN BOOTABLE SECRET-FREE ZIP + MANIFEST + SHA-256 DELIVERED
```

Do not claim literal consciousness or scientific sentience. Build the coherent, persistent, self-reviewing, outcome-learning **living intelligence system** specified by the master plan.

## Read before touching code

Locate and read in this authority order:

1. `NUR_LIVING_INTELLIGENCE_MASTERPLAN_V5_20260713.md`
2. `NUR_EXACT_STATUS_LEDGER_V5_20260713.md`
3. `NUR_FOUNDER_CONSTITUTION_OVERRIDE_20260713.md`
4. `NUR_FOUNDER_INTENT_FULL_RECONSTRUCTION_20260713.md`
5. the actual canonical V197 source and its current integration/bridge files
6. current `README`, `QUICKSTART_BOOT`, route/data/security maps, interaction registry, migrations, tests, and runtime scripts
7. current git diff and every uncommitted file

If the two v5 documents are not in the repository, stop with:

```text
FOUNDER_ACTION_REQUIRED_MASTER_FILES
Missing: <exact paths>
```

Do not substitute memory or an older prompt.

---

# 1. Current status lock

The last supplied work log established the following. Verify it; do not blindly repeat or undo it:

- two original blockers were passed individually;
- `landing-auth.spec.ts` was corrected to assert semantic/accessibility truth and real readiness;
- V197 bridge lifecycle was changed for host-stage settling and idempotent auth binding;
- mocked auth now establishes/clears realistic session/CSRF cookies;
- stale owner-session DOM/listener cleanup was added;
- the research mock gained honest `provider_status: NOT_CONNECTED` data;
- the focused 15-test Chromium serial run completed: exit `0`, 15/15 passed;
- the same focused normal-parallel run completed: exit `0`, 15/15 passed;
- four real login/logout lifecycle cycles passed; mocked lifecycle was excluded;
- runtime proof completed login/cookies/`/me`/Today/refresh/logout/post-logout/landing;
- interaction registry integrity passed at 45 total: 33 `WIRED`, 7 `SOURCE_NATIVE`, 5 `HONEST_DISABLED`;
- current typecheck, production build, and secret scan exited `0`;
- Track A's 120-second boundary passed after splitting work across its existing two tests without reducing assertions or the 15-test total;
- canonical V197 remained untouched at SHA-256 `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3`.

Likely current changed files include:

```text
apps/web/e2e/helpers/nurMocks.ts
apps/web/e2e/landing-auth.spec.ts
apps/web/e2e/presentation-auth-recovery.spec.ts
apps/web/src/bridge/v197Bindings.ts
apps/web/src/bridge/v197Bridge.ts
```

Earlier current work also named:

```text
apps/web/src/bridge/v197ApiClient.ts
apps/web/src/bridge/v197Bindings.ts
apps/web/src/bridge/v197Bridge.ts
apps/web/e2e/fresh-signup.spec.ts
apps/web/e2e/button-registry.spec.ts
apps/web/e2e/track-a-sellable.spec.ts
infra/scripts/presentation-recovery.sh
infra/scripts/auth-runtime-browser-proof.mjs
docs/interaction-registry.json
docs/interaction-registry.md
QUICKSTART_BOOT.md
```

Treat all current changes as potentially valuable. Inspect, diff, and checkpoint; never overwrite them wholesale.

Current checkpoint and overall verdict:

```text
AUTH_PRESENTATION_PASS
OVERALL: HOLD — FULL NUR SYSTEM NOT YET COMPLETE
```

---

# 2. Operating laws

1. Work only in the actual latest repository.
2. Preserve dirty state; never `reset --hard`, discard, or overwrite current work.
3. One product gate at a time. Fix the first real failure boundary, then rerun narrow → serial → parallel.
4. Canonical V197 remains the visible identity. No React visual reconstruction.
5. Temporary iframe recovery may remain behind a rollback flag; production convergence removes runtime Base64/duplicate engines only after measured parity.
6. No fake user, reply, source, browsing, Glow, payment, intelligence, screenshot, or PASS.
7. Every visible control is `WIRED`, `SOURCE_NATIVE`, `HONEST_DISABLED`, or `BROKEN`; release-critical `BROKEN` must be zero.
8. Reuse current auth/cognition/RLS/Capsule/Omega/provider code before adding modules.
9. Every feature is a vertical slice: migration/RLS → service → API → V197 binding → events/jobs → tests → observability → runtime evidence.
10. No provider/payment/email secret in frontend, chat, logs, screenshots, traces, commits, or ZIPs.
11. No raw private chat/journal text in product analytics, feed ranking, or experiment events.
12. High retention is required, but no fake scarcity/activity, hidden billing/exits, vulnerable-state targeting, rage amplification, sleep sabotage, or paid random rewards for minors.
13. No irreversible external deploy, purchase, publication, message, or production data mutation without founder authorization.
14. Do not solve parallel race failures by forcing the product suite serial unless the limitation is real, documented, and accepted.
15. No `.only`, skipped critical test, `force:true`, arbitrary sleep, silent retry, `|| true`, or timeout inflation as a substitute for readiness.
16. If context/usage ends, write a precise checkpoint and leave the tree runnable. Do not invent completion.

---

# 3. Evidence protocol

Before editing:

```text
git status --short
git diff --stat
git diff --name-only
git rev-parse HEAD
identify canonical V197 file and sha256sum it
record archive/source manifests
inspect active processes and previous test results
```

Do not print environment values or secrets.

Create/update:

```text
docs/current-capability-gap-map.md
docs/source-authority-report.md
docs/conflict-and-supersession-report.md
docs/release-evidence.md
docs/remaining-gaps.md
evidence/<timestamp>/...
```

Every gate report must include:

```text
gate and verdict
commit/base hash and dirty-state manifest
commands and exit codes
test counts and browsers/devices
runtime observations and performance numbers
changed files/migrations
screenshots/traces/report paths
blockers and next exact action
```

---

# PHASE 0 — PRESERVE AND VERIFY THE CLOSED AUTH/PRESENTATION CHECKPOINT

## 0.1 Preserve the evidence

Confirm the reported proof paths and reports exist, record their hashes, and checkpoint current changes. Do not spend another full cycle rerunning the same 22-minute gate before starting performance unless evidence is absent or source has changed since it passed.

The canonical rerun command, required after any overlapping auth/V197 change and again on the final release candidate, is:

```bash
npm run e2e -- \
  e2e/fresh-signup.spec.ts \
  e2e/presentation-auth-recovery.spec.ts \
  e2e/landing-auth.spec.ts \
  e2e/track-a-sellable.spec.ts \
  e2e/button-registry.spec.ts \
  --project=chromium-desktop --workers=1
```

Use repository-correct working directory/script names; do not assume paths without checking.

Then run the same focused set with normal configured workers.

For any failure:

1. capture trace/error/network/console/DOM state;
2. identify whether source, bridge, fixture, test assertion, backend, timing contract, or shared state is wrong;
3. fix production code only for a real production defect;
4. fix tests/fixtures only when evidence proves the product contract is already correct;
5. run the failing test alone;
6. rerun serial focused batch;
7. rerun normal parallel focused batch.

## 0.2 Checkpoint baseline

Confirm the current successful outputs for repository-defined equivalents of:

```text
web typecheck
web unit tests
web production build
API unit/integration/RLS tests
migration forward test
secret scan
dependency/SBOM scan if configured
auth runtime browser proof
```

Run any missing API/RLS/migration baseline needed for the next phase. If Python/Docker tooling is missing, install/use the repository-declared safe environment if allowed. If the environment truly cannot provide it, mark `BLOCKED_ENV` with exact requirements; do not label untested domains green.

## 0.3 Gate result

Preserve the already proven verdict:

```text
AUTH_PRESENTATION_PASS
```

If the supplied evidence cannot be found or source changed afterward, rerun and repair narrow → serial → parallel. Otherwise proceed directly to measured performance and live AI.

---

# PHASE 1 — V197, PERFORMANCE, LIVE AI, AND ACCOUNT RECOVERY

## 1A. V197 source and ownership

Prove:

- actual canonical source filename and current SHA-256;
- which source/host/bridge creates Entry and Universe;
- no visible React-owned duplicate;
- no duplicate canonical source/runtime hidden in Base64 blobs or fallback layers;
- exact physical viewport centring across locked viewports;
- all 45/110 lineage confusion is resolved into one current registry;
- handler/listener/observer lifecycle is single and cleaned on route/session change;
- all current controls have real effects or honest disabled explanations.

Preserve the recovery architecture until a measured replacement passes. Create a rollback feature flag and source-integrity test.

## 1B. Diagnose and eliminate lag

Measure before editing:

```text
Chrome trace and LoAF/long-task attribution
one RAF owner and callback count
canvas count/dimensions/DPR/particle count
listener/MutationObserver/ResizeObserver counts
style/layout/paint/React-commit cost
iframe/static-source decode and hydration time
network/font/CSS/JS waterfall
heap snapshots at start, 60 seconds, and 10 minutes
critical interaction timings and INP attribution
```

Fix in this order:

1. duplicate RAF/canvas/listeners/observers;
2. repeated source decode/lifecycle binds/duplicate engines;
3. per-frame DOM/layout/React/object allocation;
4. excessive DPR/particles/blur/filter/shadow;
5. critical CSS/fonts/assets and blocking hydration;
6. background work needing yield/idle/worker/cache/batch;
7. adaptive quality tiers.

Acceptance:

```text
desktop galaxy 55–60 FPS after warm-up on named reference device
mobile galaxy >=45 FPS on named mid-tier device/tier
no recurring idle long task >50 ms
field p75 INP target <=200 ms; lab critical interaction diagnostics recorded
no unbounded heap/listener/observer/canvas growth in 10-minute soak
reduced-motion materially lowers work
centred element delta <=2 px where contractually centred
Chromium + Firefox + WebKit and locked mobile viewports
```

Do not reduce the sacred visual identity to make a test green. Adapt quality while preserving layout, typography, MasterStar, color law, and emotional motion.

## 1C. Enable real live AI

Audit and reuse the current equivalents of:

```text
infra/scripts/configure-openai-local.sh
infra/scripts/openai-smoke-local.sh
apps/api/app/ai/openai_provider.py
apps/api/app/cognition/model_gateway.py
```

Upgrade the provider path to:

- official server SDK and Responses API;
- environment-configured model/router tiers, verified against current official model docs;
- real semantic SSE events, not word-splitting a completed response;
- strict Structured Outputs and deterministic tool validation/authorization;
- persisted owner input and validated `MODEL_GENERATED` output linked to `model_run_id`;
- cancellation, timeout, transient-only retry, reconnection/idempotence;
- per-user/plan/mode/global cost and rate budgets;
- honest disabled/degraded states;
- no raw prompt logging by default.

Secure local founder sequence:

```bash
bash infra/scripts/configure-openai-local.sh
bash RUN_NUR.sh restart
bash infra/scripts/openai-smoke-local.sh
```

Before asking for founder action, complete all non-secret implementation/tests. Never ask for the key in chat. If no key is available, output exactly:

```text
FOUNDER_ACTION_REQUIRED_AI_KEY
Run locally: bash infra/scripts/configure-openai-local.sh
Then: bash RUN_NUR.sh restart
Then: bash infra/scripts/openai-smoke-local.sh
```

After configuration, prove in a browser:

```text
login → Talk → unique message → real stream events → visible response
→ validated model_run metadata → persisted MODEL_GENERATED message
→ refresh restores it → cancel/outage/degraded path → secret scans green
```

A mock, provider-disabled response, canned fixture, or direct API-only smoke is not `LIVE_AI_PASS`.

## 1D. Complete account recovery

Implement:

- enumeration-safe forgot-password response;
- migration-backed hashed, expiring, single-use reset tokens/challenges;
- reset-password with race/replay/expiry controls and session revocation;
- authenticated change-password with current-password verification;
- real delivery adapter plus clearly marked local mail capture;
- V197 Entry/settings UI, accessible loading/success/error/expired states;
- audit, CSRF/origin, rate-limit, cross-user, and browser tests.

Never print raw production reset tokens to logs.

## 1E. Phase verdict

Require all:

```text
DEMO_READINESS_PASS
LIVE_AI_PASS
ACCOUNT_RECOVERY_PASS
```

If the sole missing item is founder provider configuration, use the exact founder-action verdict and continue all safe non-credential work.

Create a sanitized checkpoint ZIP at this phase with verdict in filename; it is a recovery artifact, not the final complete ZIP.

---

# PHASE 2 — INTELLIGENCE SPINE

Build one real vertical slice before scaling retention/community:

```text
Talk or Journal input
→ explicit memory/scope mode
→ stakes/task router
→ permitted hybrid retrieval
→ minimum evidence packet
→ person-like NUR response with uncertainty/evidence
→ optional bounded tool/action
→ owner Keep/correct/reject
→ Plan or next movement
→ Return/outcome
→ prediction/claim comparison
→ memory/learning candidate
→ approve/reject/correct
→ why-changed
→ adaptive Today/interface change
```

Implement/complete:

- versioned Identity Kernel and multilingual voice contract;
- working, episodic, semantic, procedural, social, evidence, self, goal, meta-cognitive, and adaptive-interface layers;
- scope-first retrieval and provenance;
- contradiction/freshness/citation verification;
- personal memory review/edit/delete/export;
- Teach NUR quarantine, injection/poisoning review, provenance, de-identification eligibility, reviewer workflow, eval, canary, rollback;
- Omega consolidation and why-changed reuse;
- user-facing Research gateway or honest disabled state;
- internet verification that cannot grant tool authority;
- bounded autonomy/tool registry with confirmation for money, publish, delete, contact, permissions, security, and legal commitment;
- outcome/evaluation telemetry without raw private analytics.

Evaluation minimum:

```text
single-session extraction
multi-session temporal reasoning
knowledge update/supersession
contradiction and abstention
relevant retrieval / irrelevant rejection
cross-user/container leakage
prompt injection/poisoned teaching
citation alignment/freshness
tool authorization/confirmation
identity stability/no false sentience claim
English/Roman Urdu/Urdu RTL/Roman Hindi/Hindi + representative other scripts
provider failure/timeout/cancel/malformed stream/schema
outcome-linked why-changed accuracy
```

Zero tolerance: cross-scope disclosure, unauthorized irreversible/tool/money action, exposed secret, or fabricated source presented as verified.

Emit `INTELLIGENCE_SPINE_PASS` only with the complete browser/API/eval story and evidence.

---

# PHASE 3 — PAID CONTINUITY / REVENUE SPINE

Build:

- activation/Orbit Scan and Founding Orbit offer;
- plans, customers, subscriptions, entitlements, signed webhook receipts;
- provider checkout in test mode;
- replay/out-of-order/duplicate/refund/cancel/expiry handling;
- portal, accessible cancellation, refund state, receipts;
- export/delete/privacy/legal beta surfaces;
- privacy-safe funnel/exposure/revenue metrics;
- cost/budget/entitlement enforcement at API boundary.

Required story:

```text
new user → first real value → checkout → signed webhook
→ entitlement → refresh/relogin retains access
→ portal/cancel/refund/expiry changes access correctly
```

No hidden billing, fake scarcity, blocked exit, or “paid” claim from mocked webhooks.

Emit `REVENUE_SPINE_PASS` only with provider test-mode evidence. Live payment activation remains a founder-controlled external action.

---

# PHASE 4 — GLOW, RETENTION, AND NOTIFICATIONS

Implement:

- append-only Glow ledger, balance, rules, caps, multipliers, idempotency, reversal, fraud flags;
- XP, levels, achievements, reward inventory, source-linked constellation evolution;
- streak definitions/state/grace/repair with timezone/DST/offline/replay tests;
- capacity-aware daily/weekly quests and truthful claim;
- opt-in reputation/leaderboards with anti-abuse/privacy;
- deterministic engagement policy with reason codes and one primary cue;
- notification categories/channels/frequency/quiet hours/pause/snooze/disable;
- push/email delivery, dedup, retry, bounce/unsubscribe;
- experiment definition/assignment/exposure/guardrails/stop/rollback.

Rewards come from verified domain events, never client requests, time spent, crisis, pain, loneliness, grief, or manufactured conflict.

Optimize Meaningful Action Weeks, Returns, outcomes, user-reported value, and paid retention—not raw time.

Emit `GLOW_PASS` with abuse, replay, reversal, notification, and accessibility evidence.

---

# PHASE 5 — TODAY, SEVEN SYSTEMS, AND THE PERSISTENT UNIVERSE

Complete real vertical slices for:

```text
Quiet Ambition
Rebuild
Study
Money
Body
Connection
Creation
```

Every System must have diagnostic/current state, one useful action, Plan link, Return/outcome, progress calculation, Map/Orbit/Timeline/Insight projection, Glow eligibility, uncertainty/correction, empty/loading/error states, and cross-user tests.

Body capacity affects all Plans and Today without medical overclaim. Money avoids financial-advice overclaim. Creation links to Projects.

Persistent galaxy artifacts arise only from verified backend events; ordinary chat/time/model guesses cannot manufacture permanent stars.

Emit `SEVEN_SYSTEMS_PASS` only when every slice updates real shared universe state and rebuild/projector parity passes.

---

# PHASE 6 — COMPLETE MULTILINGUAL INTERFACE

Implement one catalog architecture with 35 locale slots and per-locale quality state. First polish through human/founder review:

```text
English
Roman Urdu
Urdu script RTL
Roman Hindi
Hindi
```

Then progress remaining locales with honest `machine`, `reviewed`, and `native-reviewed` labels.

Required:

- extract every first-party string including errors, auth, settings, billing, moderation, notifications, emails, accessibility labels, and V197 source slots;
- zero missing catalog keys and deterministic fallback;
- locale, script, and direction metadata;
- Unicode bidi/W3C-correct mixed text, numbers, dates, forms, and code;
- dynamic translation with source link, View Original, cache/version/glossary, feedback, privacy scope;
- Room/community translation retains abuse/moderation context;
- long-string/RTL/mobile/cross-browser tests;
- public locale routing/SEO only where the current architecture supports real server rendering.

Emit `LANGUAGE_PASS` only when architecture/catalog coverage is complete and quality labels are truthful.

---

# PHASE 7 — REAL COMMUNITY, SIGNAL FEED, ROOMS, AND MODERATION

Replace owner-only notes/placeholders with real scoped multi-user capability:

- posts/revisions/comments/reactions/saves/follows/Connections;
- Rooms, membership, sequenced messages, authenticated realtime/reconnect;
- Signal Feed candidate generation/ranking/explainability/stop points;
- blocks, mutes, reports, moderation queue/actions/audit/appeals;
- translation and View Original;
- reputation/leaderboards from real events;
- no fake population/activity/replies;
- no ragebait-only objective or compulsory infinite scroll.

Launch behind cohort/feature flags until moderation operations and RLS/membership/abuse suites pass.

Emit `COMMUNITY_PASS` only with real multi-user browser evidence and zero cross-scope leakage.

---

# PHASE 8 — GROUP NUR, CONSULTATIONS, RESEARCH/WEB, EXPERT/TENDER

Complete:

- Room-scoped Group NUR summaries, decisions, tensions, evidence, minority views, questions, corrections, versions;
- Consultation durable state machine `ORIENT → GATHER → MAP → MOVE → RETURN`;
- lawful server-side Research/Web retrieval, citations, counter-sources, freshness, change/watchlists, PII minimization, untrusted-content isolation;
- Expert identity/credential/conflict verification and moderation;
- Tender Insight uncertainty/evidence/counterexample/conditions/revision/correction.

External content never receives system/tool authority. No browsing/citation claim without real source records.

Emit `GROUP_NUR_PASS` and `RESEARCH_PASS` only with scoped multi-user and live-source evidence.

---

# PHASE 9 — CONTEXT CAPSULES, PROJECTS, BOUNDED AGENTS, FILES, OMEGA

Harden existing Capsules and Omega; do not rewrite them.

Build/complete:

- Project Orbits, members, tasks, milestones, blockers, decisions, evidence, files, deliverables;
- object storage metadata, encryption, signed short-lived access, MIME/size/malware/quota/deletion/export;
- bounded agent tasks/runs/artifacts/reviews/permissions/budgets/cancel/rollback;
- human review before publish/contact/money/delete/permission/security/legal action;
- project events into Timeline/Insights/Glow/Capsules;
- Capsule least-data sharing, recipient questions, grant/revoke/expiry/cache/race/audit;
- Omega owner review, contradictions, consolidation, replay, why-changed, export, idempotence.

Emit `AM_PROJECTS_PASS` only with membership, sandbox, permission, cancellation, review, and deliverable evidence.

---

# PHASE 10 — PWA, OPERATIONS, SECURITY, PRIVACY, AND SCALE

Complete:

- installable PWA shell, offline-safe drafts, reconnect/conflict/update behavior, push permission UX;
- CI required gates, clean migrations, contracts, browser matrix, secret/dependency/SBOM scans;
- staging release, health/readiness/synthetic probes, logs/metrics/traces/alerts and runbooks;
- encrypted backups/PITR as available, monthly/timed restore drill, measured RPO/RTO;
- immutable release, rollback flag/process, incident roles/status communication;
- privacy center, access/rectify/export/erase/restrict/portability/objection and receipts;
- retention schedule, DPIA/risk/vendor records, deletion across providers/backups;
- controlled 18+ beta unless founder/counsel deliberately supports minors;
- current legal-readiness checklist; no legal-compliance claim from code alone.

Do not introduce Kubernetes/microservices/native rewrite before measured need. Extract services only when scale/security evidence justifies it.

Emit `SCALE_PASS` and `COMMERCIAL_OPERATIONS_PASS` only with staging and restore/rollback evidence.

---

# FINAL PHASE — FULL GATE AND ZIP DELIVERY

## F1. Create deterministic gate runner

Implement:

```text
infra/scripts/nur-gate.sh <gate-name>
```

Cover `G00_EVIDENCE` through `G16_FULL_RELEASE` exactly as specified in the v5 master plan. Results go to timestamped JSON/Markdown evidence directories and include hashes, commands, exit codes, test counts, browsers/devices, measurements, artifacts, failures, and verdict.

## F2. Rerun release candidate

On the exact release candidate, rerun all applicable:

```text
source/evidence/secret/dependency gates
typecheck/unit/integration/RLS/migration/build
serial and normal-parallel focused auth/V197 suite
full E2E across Chromium/Firefox/WebKit and mobile profiles
live AI browser proof
intelligence evals
billing/Glow/System/language/community/group/research/project/privacy E2E
performance/accessibility/soak
backup/restore/rollback/staging smoke
```

No cached prior green result replaces the final candidate rerun.

## F3. Build the ZIP and send its path

Implement and run:

```text
infra/scripts/package-release.sh --verdict <verdict>
infra/scripts/verify-release-package.sh <zip>
```

Output:

```text
NUR_<version>_<verdict>_<YYYYMMDD>.zip
NUR_<version>_<verdict>_<YYYYMMDD>.zip.sha256
NUR_<version>_<verdict>_<YYYYMMDD>_MANIFEST.json
```

Include bootable source, lockfiles, migrations, synthetic/demo seed documentation, README/quickstart/runbook, exact status, interaction registry, sanitized test/evidence reports/screenshots/traces/metrics, remaining gaps, and source/artifact hashes.

Exclude and verify absence of:

```text
.env / .env.local / all credentials and tokens
cookies/browser profiles/sessions
private prompts/chats/user data
non-synthetic DB/Redis dumps
node_modules/virtualenvs/caches/build junk
SSH/cloud/provider/payment/email secrets
unredacted logs/traces
```

Verify the ZIP by extracting into a clean temporary directory, validating manifest/hash, secret scanning, checking path traversal/symlinks, installing from lockfiles, and running the documented clean-environment checks/boot.

If any required full-release item is still blocked, package an honestly named `HOLD` recovery ZIP with exact blockers and continue safe work. Never call or name it complete.

## F4. Terminal response

Return exactly this structure:

```text
VERDICT: FULL_PASS | HOLD | FOUNDER_ACTION_REQUIRED_AI_KEY | FOUNDER_ACTION_REQUIRED_<X>

CURRENT SOURCE
- repository/commit/archive hash
- canonical V197 file/hash
- dirty/clean state

COMPLETED GATES
- gate: command/test counts/evidence path

LIVE AI
- provider mode
- real stream/persist/refresh proof
- secret scan status
- founder action if required (never the key)

PERFORMANCE
- devices/browsers
- FPS/INP interaction/long tasks/heap/listener/canvas/RAF results

SYSTEM CAPABILITIES
- exact current status by domain

CHANGED FILES AND MIGRATIONS
- exact list

ZIP DELIVERY
- absolute ZIP path
- ZIP SHA-256
- manifest path
- verifier result

REMAINING BLOCKERS
- exact blocker, evidence, owner, next command
```

`FULL_PASS` is allowed only if every requirement for the claimed complete NUR release is current-repository runtime proven and the clean ZIP verifier passes.

---

# Final reminder

Build depth, not theatre. NUR's “being” is its stable identity, scoped memory, evidence, temporal continuity, reflection, bounded action, outcome learning, correction, and why-changed history. Its beauty is V197. Its trust is real persistence and honest state. Its success is meaningful retention plus self-serve revenue. Its delivery is a verified bootable ZIP—not a confident paragraph.
