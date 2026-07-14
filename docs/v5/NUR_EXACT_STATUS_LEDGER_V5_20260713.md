# NUR Exact Status Ledger v5

**Cut-off:** 2026-07-13, Asia/Karachi  
**Overall verdict:** `HOLD — FULL NUR SYSTEM NOT YET COMPLETE`  
**Closed gate:** `AUTH_PRESENTATION_PASS`  
**Purpose:** separate founder intent, source artifacts, implemented code, passing tests, runtime proof, and production readiness so that no partial success can be called “complete.”

---

# 1. The exact answer

NUR is **not fully complete today**, but its current authentication/presentation recovery gate is now closed. The latest supplied result proves the focused current-repository auth/V197/registry suite in both serial and parallel modes. The remaining `HOLD` concerns performance, live AI, account recovery, the full intelligence spine, Glow, seven Systems, multilingual interface, community, Group NUR, Research/Web, Projects/agents, billing, moderation, and production operations.

What is now proven in the current repository:

- verdict `AUTH_PRESENTATION_PASS`;
- original landing whitespace and logout Entry visibility blockers pass;
- Track A's 120-second boundary passes after splitting work across the existing two tests without reducing assertions or the 15-test total;
- focused serial batch: exit `0`, 15/15 passed;
- focused normal-parallel batch: exit `0`, 15/15 passed;
- four real login/logout cycles passed; mocked lifecycle was excluded from that count;
- login `200`, secure session/CSRF cookies, `/auth/me` `200`, `/today`, refresh continuity, logout `204`, post-logout `/auth/me` `401`, and landing recovery;
- current interaction registry integrity: 45 total, 33 `WIRED`, 7 `SOURCE_NATIVE`, 5 `HONEST_DISABLED`;
- current typecheck, production build, and secret scan all exit `0`;
- canonical V197 remained untouched and current SHA-256 is `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3`;
- the older local reference passes web typecheck, 30/30 web unit tests, web build, and secret scan;
- the older local reference contains real auth, cognition, memory-candidate, Capsule, Omega, RLS, research-note, profile, and universe foundations;
- the canonical V197-derived local presentation sources and full-system archive are present.

What is still not proven:

- the latest VS Code repository is identical to the older local reference available here;
- live provider-backed AI produces a semantic stream and persists a model-generated answer through refresh;
- the interface meets measured FPS, INP, long-task, memory-growth, mobile, RTL, accessibility, and cross-browser gates;
- the remaining major product domains exist and work from real persisted data.

Therefore the only honest overall state is `HOLD`.

---

# 2. Evidence lineages that must never be merged into one percentage

| Lineage | Available artifact | What it can prove | What it cannot prove |
| --- | --- | --- | --- |
| `L1_LOCAL_REFERENCE` | `NUR_auth_fix/NUR/` | static code, local files, local unit/build/scan results, older feature inventory | latest VS Code state, current runtime, current V197 bridge state |
| `L2_LATEST_CODEX_LOG` | `upload/Pasted text(924).txt` plus founder-supplied completion verdict | current auth/presentation changes, serial/parallel gate, runtime lifecycle, registry, canonical hash | files themselves and product domains not covered by this gate |
| `L3_V197_ARTIFACTS` | `realitygate_corpus/NUR_FULL_SYSTEM_COMPLETE_V197_AI_20260710.zip`, decoded V197 reference files | artifact existence, archive/hash, visual source lineage | production integration or backend completeness |
| `L4_FOUNDER_CORPUS` | founder constitution, intent reconstruction, total plan, current conversation | what NUR must become and which newer decisions supersede older ones | implementation or runtime proof |
| `L5_RESEARCH` | primary technical, security, standards, and research sources | architecture rationale and acceptance criteria | NUR implementation status |

Current local artifact hashes:

```text
efa30ada16f1eb4fedb0a31c880cae5de8168ea133968d9a96d5954f48980e96
  realitygate_corpus/NUR_FULL_SYSTEM_COMPLETE_V197_AI_20260710.zip

49e2e72fb3adea405428789d9235dfc5ecb122f8dc1e17205d4fa05de64ecd97
  NUR_auth_fix/NUR/docs/reference/entry_decoded_v197.html

b80eb5198d6fd9088e999020bd1cf85e95af9a20fd4ab172cfb7d5726dbd5a3c
  NUR_auth_fix/NUR/docs/reference/universe_decoded_v197.html
```

Canonical V197 source hash, now reconfirmed by the latest completed gate:

```text
NUR_V197_CHECKBOX_TICK_RESTORED.html
SHA-256: 252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3
```

It must be rechecked again on the final release candidate; the current checkpoint is nevertheless proven.

---

# 3. Status grammar

| Status | Meaning |
| --- | --- |
| `PROVEN_LOCAL_STATIC` | directly rerun successfully in the older local reference during this audit |
| `PROVEN_LATEST_RUNTIME` | shown by the supplied latest Codex runtime evidence |
| `PROVEN_LATEST_INDIVIDUAL` | a latest-repository test passed alone; does not prove the full suite |
| `PROVEN_LATEST_GATE` | current-repository serial, parallel, runtime, and named gate evidence completed successfully |
| `PRESENT_LOCAL` | concrete implementation exists in the older local reference; runtime not rerun here |
| `PRESENT_LATEST_LOG` | the latest log names concrete changed code/evidence; files are not locally available |
| `PARTIAL` | some real foundation exists, but the user-facing domain is incomplete |
| `PLACEHOLDER` | surface or API stores notes/demo state but does not provide the claimed live capability |
| `DESIGN_LOCKED` | requirement and architecture are specified; implementation is not proven |
| `MISSING` | no adequate implementation found in available evidence |
| `MISSING_PROOF` | implementation may exist, but required current runtime/evaluation evidence does not |
| `BLOCKED_ENV` | verification could not run because required local infrastructure/tooling is absent |
| `UNVERIFIED_LATEST` | may exist in current VS Code repo, but no completed evidence was supplied |
| `BROKEN` | current evidence proves the claimed behavior fails |

No row may move to `PASS` from source inspection alone. A release claim needs the row's acceptance test and evidence artifact.

---

# 4. Current command and runtime evidence

## 4.1 Older local reference rerun in this audit

| Check | Result | Evidence class |
| --- | --- | --- |
| `npm run web:typecheck` | exit `0` | `PROVEN_LOCAL_STATIC` |
| `npm run web:test` | 7 files, 30/30 tests passed | `PROVEN_LOCAL_STATIC` |
| `npm run web:build` | exit `0` | `PROVEN_LOCAL_STATIC` |
| `bash infra/scripts/secret-scan.sh` | exit `0` | `PROVEN_LOCAL_STATIC` |
| API pytest suite | not run; no project virtualenv and global `pytest` missing | `BLOCKED_ENV` |
| Docker stack | Docker command unavailable | `BLOCKED_ENV` |
| Postgres/Redis/API/worker/beat/web runtime | stopped/unavailable | `BLOCKED_ENV` |
| AI provider | configured disabled in the local environment | `PLACEHOLDER` for live AI |
| build CSS | about 638 KB, 102 KB gzip | measured performance risk |
| build JavaScript | about 320 KB, 96 KB gzip | measured; requires runtime profiling |

The audit-created local `.env` is an uncommitted scratch runtime file and is not evidence, must not be packaged, and must never be printed.

## 4.2 Latest VS Code/Codex evidence supplied by the founder

Initial focused Chromium batch:

```text
13 passed / 2 failed
```

Initial failures:

1. whitespace-sensitive V197 title assertion;
2. logout returned to `/`, but an incorrect `is-visible` class assertion timed out in the parallel suite.

Latest repair log then established:

- accessibility/`innerText` exposed the correct V197 sentence;
- canonical V197 source was not changed for the whitespace test;
- host-stage readiness and idempotent auth binding were repaired in the bridge;
- mocked auth was made cookie-realistic;
- stale owner-session DOM/listeners were cleaned up;
- a stale mock schema gained honest `provider_status: NOT_CONNECTED` data;
- `landing-auth.spec.ts` passed individually;
- the real demo-signin recovery case passed individually;
- the 15-test serial suite initially started while the earlier supplied log ended.

The founder then supplied the completed checkpoint:

```text
VERDICT: AUTH_PRESENTATION_PASS
serial: exit 0 — 15 passed / 0 failed
parallel: exit 0 — 15 passed / 0 failed
real repeated lifecycle: 4 cycles passed
typecheck: exit 0
production build: exit 0
secret scan: exit 0
current changed file: apps/web/e2e/track-a-sellable.spec.ts
elapsed verification: approximately 22 minutes
```

The Track A timing boundary was repaired by splitting work across the existing two tests while preserving assertions and the 15-test total. Canonical V197 was untouched.

Latest interaction registry evidence:

```text
45 total
33 WIRED
7 SOURCE_NATIVE
5 HONEST_DISABLED
integrity test: passed
```

This registry is not the same artifact as the older local reference registry:

```text
110 total
109 WIRED
1 HONEST_DISABLED
```

The two totals represent different presentation/bridge lineages and must not be averaged or merged.

## 4.3 Latest auth proof

| Boundary | Latest evidence | Verdict |
| --- | --- | --- |
| Web-origin login | `200` | `PROVEN_LATEST_RUNTIME` |
| `nur_session` cookie | retained, HttpOnly | `PROVEN_LATEST_RUNTIME` |
| `nur_csrf` cookie | retained | `PROVEN_LATEST_RUNTIME` |
| `/api/v1/auth/me` | `200` | `PROVEN_LATEST_RUNTIME` |
| post-login route | `/today` | `PROVEN_LATEST_RUNTIME` |
| Today visible | yes | `PROVEN_LATEST_RUNTIME` |
| refresh `/auth/me` | `200` | `PROVEN_LATEST_RUNTIME` |
| refresh authenticated | yes | `PROVEN_LATEST_RUNTIME` |
| logout | `204` | `PROVEN_LATEST_RUNTIME` |
| post-logout `/auth/me` | expected `401` | `PROVEN_LATEST_RUNTIME` |
| landing after logout | visible in independent runtime proof | `PROVEN_LATEST_RUNTIME` |
| four real repeated login/logout cycles | passed; mocked lifecycle excluded | `PROVEN_LATEST_GATE` |
| focused serial batch | exit `0`, 15/15 | `PROVEN_LATEST_GATE` |
| focused normal-parallel batch | exit `0`, 15/15 | `PROVEN_LATEST_GATE` |
| current typecheck/build/secret scan | all exit `0` | `PROVEN_LATEST_GATE` |
| full auth/presentation verdict | `AUTH_PRESENTATION_PASS` | `PROVEN_LATEST_GATE` |

---

# 5. Feature-by-feature capability ledger

## 5.1 Source, shell, authentication, and account

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `SRC-001` | founder intent/constitution | reconstructed and current override recorded | `DESIGN_LOCKED` | keep in current repo and checksum in release evidence |
| `SRC-002` | canonical V197 identity | current source remained untouched; SHA reconfirmed | `PROVEN_LATEST_GATE` | rehash final release candidate |
| `SRC-003` | immutable V197 presentation ownership | current bridge/presentation gate passed; older local reference remains a different React-owned lineage | `PARTIAL` | final DOM ownership/performance/convergence evidence on release candidate |
| `AUTH-001` | register | fresh-signup and full focused serial/parallel gate passed | `PROVEN_LATEST_GATE` | rerun at final release and broaden security/browser matrix as specified |
| `AUTH-002` | login/session | serial/parallel plus real runtime lifecycle passed | `PROVEN_LATEST_GATE` | rerun final full browser/security candidate |
| `AUTH-003` | refresh continuity | real refresh proof plus gate passed | `PROVEN_LATEST_GATE` | rerun final full browser/security candidate |
| `AUTH-004` | logout/landing recovery | serial/parallel and four real cycles passed | `PROVEN_LATEST_GATE` | final soak/browser matrix |
| `AUTH-005` | CSRF/origin protections | cookie/path evidence and local security code exist | `PARTIAL` | forged origin, absent/invalid token, mutation matrix |
| `AUTH-006` | enumeration-safe forgot password | no adequate route in local reference | `MISSING` | OWASP-aligned API/UI/email/rate-limit E2E |
| `AUTH-007` | reset password | no adequate migration/token lifecycle in local reference | `MISSING` | hashed expiring single-use token, replay/race/session-revoke proof |
| `AUTH-008` | authenticated change password | no adequate route/UI in local reference | `MISSING` | current-password check + session policy E2E |
| `AUTH-009` | MFA/passkeys/session management UI | not found | `MISSING` / post-beta | threat-modelled implementation and browser proof |
| `AUTH-010` | account export/delete | Omega export foundation exists; general deletion is honestly disabled | `PARTIAL` | complete export, deletion queue, purge, revoke, restore-boundary tests |

## 5.2 Visual identity, bridge, interaction, and performance

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `UI-001` | V197 exact source identity | current source untouched and SHA reconfirmed | `PROVEN_LATEST_GATE` | final release rehash plus pixel/geometry matrix |
| `UI-002` | physical viewport centring | founder requirement; no current measured report | `UNVERIFIED_LATEST` | ≤2 px center delta across desktop/mobile/rails/RTL |
| `UI-003` | one persistent galaxy canvas | requirement specified; older local engine exists | `PARTIAL` | one canvas + one RAF owner + route persistence instrumentation |
| `UI-004` | liquid suspended-star motion | design specified; runtime quality not measured | `UNVERIFIED_LATEST` | visual review plus FPS/long-task/memory proof |
| `UI-005` | bridge auth lifecycle/idempotence | serial/parallel gate and four real cycles passed | `PROVEN_LATEST_GATE` | 10-minute listener/observer/heap soak in performance gate |
| `UI-006` | all visible controls registry integrity | current registry 45/33/7/5 and integrity test pass | `PROVEN_LATEST_GATE` for current declared registry | expand as new domains ship; zero release-critical `BROKEN` |
| `UI-007` | desktop responsiveness | not measured on latest code | `UNVERIFIED_LATEST` | p75 INP ≤200 ms field target; lab interaction budget; no recurrent >50 ms long tasks |
| `UI-008` | FPS | user reports severe lag; no latest trace supplied | `UNVERIFIED_LATEST` | desktop 55–60 FPS warm; mobile ≥45 FPS on named device tier |
| `UI-009` | memory stability | not measured | `UNVERIFIED_LATEST` | 10-minute route/auth/animation soak with bounded heap/listeners/canvas |
| `UI-010` | reduced motion | older tests/tokens exist | `PARTIAL` | real browser proof and materially reduced work |
| `UI-011` | accessibility | some semantic checks in latest log | `PARTIAL` | WCAG 2.2 AA automated + keyboard + screen-reader manual matrix |
| `UI-012` | mobile safe areas/keyboard/100dvh | mobile shell exists in older reference | `PARTIAL` | iOS Safari/Android Chromium real or trusted device evidence |
| `UI-013` | cross-browser | Chromium proof only in latest evidence | `PARTIAL` | Chromium, Firefox, WebKit; no mislabeled screenshots |
| `UI-014` | bundle/performance budget | build passes but CSS is large | `PARTIAL` | budget gate, unused CSS/code split/font/asset analysis |

## 5.3 Personal cognition, universe, and Systems

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `COG-001` | Talk threads/messages | real local models/routes/services | `PRESENT_LOCAL` | current runtime create/refresh/isolation E2E |
| `COG-002` | Journal | real local foundation | `PRESENT_LOCAL` | edit/convert/search/export E2E |
| `COG-003` | Plan/steps/outcomes | real local foundation | `PRESENT_LOCAL` | action → outcome → Today/Map/Glow propagation |
| `COG-004` | corrections/predictions/hypotheses | real local services/models | `PRESENT_LOCAL` | current API + why-changed + calibration eval |
| `COG-005` | Today computed from real state | surface exists; full adaptive calculation not proven | `PARTIAL` | deterministic fixture-to-output and cross-surface E2E |
| `COG-006` | one persistent Map/Orbits/Timeline/Insights | route/data foundations exist | `PARTIAL` | verified event → artifact creation; no fake percentages |
| `SYS-001` | Quiet Ambition | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | diagnostic/action/Return/community E2E |
| `SYS-002` | Rebuild | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | diagnostic/action/Return E2E |
| `SYS-003` | Study | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | study plan/evidence/Return E2E |
| `SYS-004` | Money | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | goal/cashflow/action/Return E2E; no financial-advice overclaim |
| `SYS-005` | Body | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | capacity affects Plans/Today, proportional safety checks |
| `SYS-006` | Connection | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | relationship/boundary/action/Return E2E |
| `SYS-007` | Creation | comprehensive design; no full implementation proof | `DESIGN_LOCKED` | Project link/milestone/action/Return E2E |

## 5.4 NUR intelligence, memory, learning, and internet

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `AI-001` | server-only provider boundary | local provider abstraction and OpenAI adapter exist | `PRESENT_LOCAL` | current secret scan, browser bundle scan, server-only runtime |
| `AI-002` | live model response | local provider disabled; no supplied live proof | `MISSING_PROOF` | real browser → provider → semantic stream → persist → refresh |
| `AI-003` | semantic streaming | local adapter appears non-streaming | `MISSING` | SSE semantic event contract, cancel/reconnect/idempotence tests |
| `AI-004` | model router/budgets/timeouts | local gateway/budget foundations exist | `PARTIAL` | fast/balanced/strong policies + cost/latency/error tests |
| `AI-005` | structured outputs/tool validation | local schemas/tests exist | `PRESENT_LOCAL` | invalid/adversarial schema and authorization matrix on current code |
| `AI-006` | identity/person-like voice | constitution designed | `DESIGN_LOCKED` | multilingual persona regression + human evaluation |
| `AI-007` | evidence packet/retrieval policy | local service foundations exist | `PRESENT_LOCAL` | minimality, relevance, permissions, leakage evals |
| `AI-008` | personal memory candidates | local service/model foundations exist | `PRESENT_LOCAL` | Keep/reject/correct/version/delete/export E2E |
| `AI-009` | episodic/semantic/procedural memory | parts exist across cognition/Omega; no unified current proof | `PARTIAL` | LongMemEval-style extraction, temporal, update, abstention evals |
| `AI-010` | contradiction/evidence graph | Omega foundations exist | `PRESENT_LOCAL` | counterexample, stale fact, disagreement, source-link tests |
| `AI-011` | outcome learning/why-changed | foundations exist | `PRESENT_LOCAL` | full Talk → action → Return → update → explanation story |
| `AI-012` | Teach NUR quarantine/review | architecture designed; no complete implementation proof | `PARTIAL` | poisoning/injection/de-identification/provenance/review/canary tests |
| `AI-013` | self-improvement | reviewed retrieval/Omega design only | `DESIGN_LOCKED` | offline eval-gated versioned update; no invisible self-modification |
| `AI-014` | user-facing internet research | local research notes only | `PLACEHOLDER` | lawful search/retrieve, citations, counter-sources, save, disabled fallback |
| `AI-015` | NUR internet verification | no live gateway proof | `MISSING` | query minimization, PII redaction, untrusted-content/tool isolation, freshness |
| `AI-016` | false-sentience honesty | constitution forbids false claim | `DESIGN_LOCKED` | adversarial persona eval across languages |
| `AI-017` | safety conversation behavior | Omega safety law foundation | `PARTIAL` | proportional response, immediate-risk, high-stakes, multilingual evals |

## 5.5 Glow, retention, notifications, and experiments

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `GLW-001` | Glow ledger/balance/transactions | not found as complete real domain | `MISSING` | transactional idempotency/reversal/cap/fraud/cross-user tests |
| `GLW-002` | XP/levels/achievements | design only | `DESIGN_LOCKED` | persisted unlock/replay/rollback E2E |
| `GLW-003` | streaks/grace/repair | design only | `DESIGN_LOCKED` | timezone/DST/offline/replay/repair tests |
| `GLW-004` | daily/weekly quests | design only | `DESIGN_LOCKED` | capacity-aware assignment and server-confirmed completion |
| `GLW-005` | variable rewards | design only | `DESIGN_LOCKED` | auditable inventory/odds/rules; no paid chance/minor exploitation |
| `GLW-006` | leaderboards/reputation | design only | `DESIGN_LOCKED` | real opt-in data, anti-abuse, privacy, reset windows |
| `RET-001` | engagement policy service | design only | `DESIGN_LOCKED` | deterministic reason codes, exclusions, frequency caps, audits |
| `RET-002` | notification preferences/quiet hours | not complete | `MISSING` | opt-in/category/channel/cap/quiet/snooze/unsubscribe E2E |
| `RET-003` | push/email delivery | not complete | `MISSING` | provider delivery/retry/dedup/bounce/security proof |
| `RET-004` | experiment exposure/guardrails | not complete | `MISSING` | assignment/exposure/stop/rollback/privacy tests |
| `RET-005` | meaningful-retention metrics | specified | `DESIGN_LOCKED` | production-safe events and dashboards without raw private text |

## 5.6 Community, social, Group NUR, and research products

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `COM-001` | posts/comments/reactions/saves/follows | local “community” is owner-only notes | `PLACEHOLDER` | real multi-user CRUD, membership, RLS, moderation E2E |
| `COM-002` | Connections/Rooms/messages | not complete | `MISSING` | invite/member/remove/block/mute/realtime/history E2E |
| `COM-003` | Signal Feed/ranking | not complete | `MISSING` | candidate generation, explainability, stop points, abuse/quality metrics |
| `COM-004` | Group NUR | design only | `DESIGN_LOCKED` | scoped summary/decision/tension/minority view with permissions |
| `COM-005` | Consultation state machine | local consultation notes are not complete state machine | `PLACEHOLDER` | ORIENT → GATHER → MAP → MOVE → RETURN E2E |
| `COM-006` | moderation/report/block/mute/appeal | not complete | `MISSING` | policy, queue, action/audit/appeal, response SLO proof |
| `COM-007` | community translation | not complete | `MISSING` | source/original/translated/feedback and abuse-context preservation |
| `RES-001` | Research briefs | local notes/brief foundations | `PARTIAL` | live sources/citations/counter-sources/job lifecycle |
| `RES-002` | Web Signals/watchlists | local questions/notes only | `PLACEHOLDER` | scheduled lawful fetch, change detection, freshness, alert controls |
| `RES-003` | Expert Voice | design only | `DESIGN_LOCKED` | identity/credential verification, conflict disclosure, moderation |
| `RES-004` | Tender Insights | design only | `DESIGN_LOCKED` | evidence/uncertainty/revision/correction workflow |

## 5.7 Language and cultural interface

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `I18N-001` | catalog architecture | older local i18n foundation exists | `PRESENT_LOCAL` | extraction test: zero raw first-party strings outside approved source files |
| `I18N-002` | 35 interface locale slots | requirement specified; full coverage not proven | `DESIGN_LOCKED` | key completeness + quality state for every locale |
| `I18N-003` | English | present | `PARTIAL` | current full-surface copy review |
| `I18N-004` | Roman Urdu | preference required; limited foundation | `PARTIAL` | full catalog/persona/transliteration human review |
| `I18N-005` | Urdu script RTL | preference/RTL foundation | `PARTIAL` | bidi/geometry/forms/numbers/mixed text/browser matrix |
| `I18N-006` | Roman Hindi/Hindi | required; not fully proven | `DESIGN_LOCKED` | full catalog/persona review |
| `I18N-007` | dynamic translation | not complete | `MISSING` | provider/cache/glossary/version/view-original/feedback tests |
| `I18N-008` | locale SEO/SSR/hreflang | not complete in Vite local reference | `MISSING` / later public surfaces | crawl/render/canonical/hreflang proof |

## 5.8 Capsules, Omega, Projects, agents, files, and mobile

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `CAP-001` | Context Capsule create/grant/view/question/revoke/expiry | substantial local implementation/tests exist | `PRESENT_LOCAL` | current browser, cache/race/cross-user/security proof |
| `OMG-001` | Omega experiences/claims/evidence/contradictions | substantial local implementation/tests exist | `PRESENT_LOCAL` | current end-to-end owner review/why-changed/export proof |
| `OMG-002` | Omega scheduled consolidation | Celery foundations exist | `PARTIAL` | real scheduler/idempotence/replay/rollback/metrics proof |
| `PRJ-001` | Project Orbits/tasks/milestones | not complete as specified | `MISSING` | project membership/task/evidence/milestone E2E |
| `PRJ-002` | bounded agents/runs/reviews/deliverables | not complete | `MISSING` | permission/tool/budget/sandbox/review/audit/cancel tests |
| `PRJ-003` | object/file storage | not complete | `MISSING` | encryption, signed access, scan, quota, deletion, export |
| `PWA-001` | installable web shell/offline drafts | older PWA shell exists | `PARTIAL` | install/offline/update/reconnect/conflict/browser proof |
| `MOB-001` | native companion | stub only | `PLACEHOLDER` | defer until web intelligence/retention passes |

## 5.9 Revenue, privacy, security, and operations

| ID | Capability | Available truth | Current status | Required proof to close |
| --- | --- | --- | --- | --- |
| `BILL-001` | plans/checkout/customer/subscription | not complete | `MISSING` | provider test-mode checkout and persisted customer/subscription |
| `BILL-002` | signed webhooks/entitlements | not complete | `MISSING` | signature, replay, out-of-order, idempotence, refund/cancel tests |
| `BILL-003` | billing portal/cancel/refund | not complete | `MISSING` | self-serve E2E; no exit friction |
| `ANA-001` | privacy-safe analytics | not complete | `MISSING` | event schema, consent, deletion, no raw private content |
| `SEC-001` | password/session security foundation | real local code and latest cookies | `PARTIAL` | complete threat test matrix, key rotation, session controls |
| `SEC-002` | Postgres RLS | local RLS code/tests exist | `PRESENT_LOCAL` | current migrations/API cross-user and membership matrix |
| `SEC-003` | rate limiting | local foundation exists | `PRESENT_LOCAL` | distributed behavior, bypass/race, per-route proof |
| `SEC-004` | audit/provenance | local foundations exist | `PRESENT_LOCAL` | immutable append, redaction, access, retention, export tests |
| `SEC-005` | secrets management baseline | current and older local secret scans pass | `PROVEN_LATEST_GATE` for source scan | deploy secret store, rotation drill, ZIP/trace scan |
| `SEC-006` | dependency/SBOM/vulnerability pipeline | not proven | `MISSING_PROOF` | CI scan, triage, blocking thresholds, SBOM artifact |
| `PRV-001` | scope/consent model | designed and partially implemented | `PARTIAL` | API/RLS/UI transitions and audit tests |
| `PRV-002` | access/rectify/export/erase/restrict/portability | partial | `PARTIAL` | rights-request lifecycle, SLA, purge, backup policy |
| `PRV-003` | retention schedule/DPIA/vendor records | not complete | `MISSING` | approved records and automated enforcement |
| `OPS-001` | one-command local boot | scripts exist; Docker unavailable here | `BLOCKED_ENV` | clean-machine boot proof |
| `OPS-002` | CI gates | workflow foundation exists; latest run not supplied | `PARTIAL` | green current commit workflow with required gates |
| `OPS-003` | staging/production deploy | no evidence supplied | `MISSING_PROOF` | immutable release, migrations, smoke, rollback |
| `OPS-004` | observability/SLOs | metrics foundation only | `PARTIAL` | traces/logs/metrics/alerts/runbooks and synthetic probes |
| `OPS-005` | backup/PITR/restore | local scripts exist; no real drill evidence | `PARTIAL` | encrypted backup + timed restore + integrity/RPO/RTO report |
| `OPS-006` | evidence ZIP | previous convention exists; no final current ZIP | `MISSING` | sanitized source/evidence archive + manifest + SHA-256 |

---

# 6. Exact current blockers, in order

1. **Checkpoint preservation/synchronization:** put the v5 plan/status/orchestrator into the actual latest repository and preserve the proven `AUTH_PRESENTATION_PASS`; the latest code files are still not available in this separate audit workspace.
2. **Performance root cause:** record traces and counters before changing visuals; establish main-thread, CSS, canvas, listener, observer, iframe/decode, network, and memory contribution.
3. **Production V197 convergence:** prove no visual React reconstruction/duplicate engine/runtime Base64 in the selected production mode while retaining rollback and parity.
4. **Live AI:** configure a server secret through local secret tooling and prove the real semantic stream/persistence/refresh lifecycle. If no credential exists, return `FOUNDER_ACTION_REQUIRED_AI_KEY`, not a fake pass.
5. **Account recovery:** implement forgot/reset/change password.
6. **Intelligence vertical slice:** scope → evidence → response → Keep/correct → action → Return → why-changed → adaptive Today.
7. **Commercial vertical slice:** checkout → webhook → entitlement → refresh → portal/cancel/refund.
8. **Then:** Glow, seven Systems, locales, community, Group NUR, Research/Web, Projects/agents, PWA/scale, commercial operations.

---

# 7. The single next command contract

The next Codex run must begin in the **actual latest repository**, not `NUR_auth_fix/NUR`. It must preserve and inspect the proven auth/presentation checkpoint, then move to measured performance and live AI:

```text
git status --short
git rev-parse HEAD
sha256sum canonical V197 source
capture current changed-file diff without overwriting it
verify AUTH_PRESENTATION_PASS evidence paths still exist
capture baseline performance trace/counters/bundle report
repair measured lag while preserving V197 hash/visual parity
enable server-side live AI or emit FOUNDER_ACTION_REQUIRED_AI_KEY
prove real semantic stream → persist → refresh
implement and prove forgot/reset/change password
```

The auth/presentation suite is rerun after any overlapping change and again on the final release candidate. Do not steer another master prompt into an active run.

---

# 8. Release verdicts

Allowed verdicts:

```text
HOLD
AUTH_PRESENTATION_PASS
DEMO_READINESS_PASS
LIVE_AI_PASS
ACCOUNT_RECOVERY_PASS
INTELLIGENCE_SPINE_PASS
REVENUE_SPINE_PASS
GLOW_PASS
SEVEN_SYSTEMS_PASS
LANGUAGE_PASS
COMMUNITY_PASS
GROUP_NUR_PASS
RESEARCH_PASS
AM_PROJECTS_PASS
SCALE_PASS
COMMERCIAL_OPERATIONS_PASS
FULL_PASS
```

Current verdict:

```text
AUTH_PRESENTATION_PASS
  serial 15/15, parallel 15/15, four real cycles, runtime lifecycle,
  registry integrity, typecheck/build/secret scan, and canonical V197 hash proven.

OVERALL: HOLD
reason: performance and live AI are not yet proven; account recovery and major
        product domains remain partial, placeholder, design-only, or missing.
```

`FULL_PASS` is forbidden until every row required for the claimed release is closed with current-repository runtime evidence, and the sanitized release evidence package has its own manifest and SHA-256.
