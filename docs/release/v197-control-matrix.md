# Canonical V197 Control Matrix

Generated from `33a5dab8692612b6324830f1ad3f583a65dbeb9c` — canonical V197 shell + nonvisual TS bridge + adjunct surfaces.

Every visible interactive control across the canonical V197 shell and its
bridge adjunct surfaces, classified against the release contract. `LIVE_REAL`
requires a real bridge event, the intended API contract (or an intentional
local action), a persisted/hydrated result, and visible loading/error states.

## Totals

| Classification | Count |
|---|---|
| LIVE_REAL | 73 |
| BLOCKED_BY_EXTERNAL_PROVIDER | 2 |
| INTENTIONAL_LOCAL_ONLY | 8 |
| NOT_IMPLEMENTED_VISIBLE | 7 |
| DEAD | 0 |
| DUPLICATE | 0 |
| MISLEADING | 0 |
| **Total** | **90** |

## Notes

- LIVE_REAL requires a real bridge event, real API contract or intentional local action, persisted/hydrated result, and visible loading/error states — enforced by the listed specs plus button-registry.spec.ts coverage (no visible uncovered control).
- Browser specs use contract-faithful mocks; the real backend contract for Talk and Projects/G14 is separately proven by the API pytest suite and the live Celery worker smoke.
- Two MISLEADING/DEAD findings were fixed in this mission and are annotated on project.tabs and project.file-choose.
- AI-agent provider execution has no visible control by design; the backend capability catalog reports it BLOCKED_BY_EXTERNAL_PROVIDER.

## Controls

| ID | Surface | Control | API / action | Classification | Proof |
|---|---|---|---|---|---|
| `entry.navigation` | Entry | front nav (Begin/Sign in/What) (canonical source navigation) | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts, fresh-signup.spec.ts |
| `entry.signup` | Entry | Begin / signup form (429 + duplicate-email honest paths proven) | `POST /api/v1/auth/register` | LIVE_REAL | fresh-signup.spec.ts, button-registry.spec.ts |
| `entry.signin` | Entry | Sign in form | `POST /api/v1/auth/login` | LIVE_REAL | fresh-signup.spec.ts, button-registry.spec.ts, full-interface.spec.ts |
| `auth.logout` | Topbar | Log out | `POST /api/v1/auth/logout` | LIVE_REAL | button-registry.spec.ts |
| `nav.personal` | Nav | personal pages | `—` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts |
| `nav.lenses` | Nav | universe lenses | `—` | LIVE_REAL | full-interface.spec.ts, universe-lenses.spec.ts |
| `nav.world` | Nav | world focus | `—` | LIVE_REAL | full-interface.spec.ts |
| `nav.local-tabs` | Nav | context/research local tabs | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts |
| `mobile.nav` | Mobile nav | mobile page nav (chromium-mobile projects) | `—` | LIVE_REAL | talk.spec.ts, visual-readiness.spec.ts |
| `mobile.composer` | Mobile Talk | mobile composer | `POST /api/v1/cognition/talk/stream` | LIVE_REAL | talk.spec.ts |
| `today.composer` | Today | Today composer | `POST /api/v1/cognition/events` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts |
| `today.actions` | Today | check-in / show glows | `POST /api/v1/today/*` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts, sol-live-new-surfaces.spec.ts |
| `talk.composer` | Talk | Talk send (success stream + reload hydration + dedup proven) | `POST /api/v1/cognition/talk/stream` | LIVE_REAL | talk.spec.ts, talk-persistence.spec.ts |
| `talk.provider-disabled` | Talk | disabled-provider state (fail-closed; no fabricated reply; exactly one error bubble) | `talk.error code provider_disabled` | BLOCKED_BY_EXTERNAL_PROVIDER | talk.spec.ts |
| `talk.cancel` | Talk | Cancel turn | `POST /cognition/talk-runs/:id/cancel` | LIVE_REAL | talk.spec.ts |
| `talk.modes` | Talk | mode prompts | `—` | LIVE_REAL | talk.spec.ts, button-registry.spec.ts |
| `talk.thread` | Talk | thread actions (plan/correct) | `POST /plans etc.` | LIVE_REAL | talk.spec.ts |
| `journal.save` | Journal | Save entry | `POST /api/v1/journal` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts, v197-control-matrix.spec.ts |
| `journal.prompts` | Journal | prompt chips | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts |
| `plan.step` | Plan | step check | `PATCH /api/v1/plan-steps/:id` | LIVE_REAL | talk.spec.ts, full-interface.spec.ts, button-registry.spec.ts |
| `plan.actions` | Plan | make-easier / outcome | `PATCH /plan-steps + POST /outcomes` | LIVE_REAL | talk.spec.ts, talk-persistence.spec.ts, full-interface.spec.ts |
| `plan.direction` | Plan | edit direction | `—` | NOT_IMPLEMENTED_VISIBLE | button-registry.spec.ts |
| `systems.select` | Systems | system node select | `PATCH /api/v1/profile/preferences` | LIVE_REAL | full-interface.spec.ts, track-a-sellable.spec.ts, button-registry.spec.ts |
| `systems.add` | Systems | add system | `POST /api/v1/orbits` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts |
| `top.search` | Topbar | universe search | `GET /api/v1/universe/search` | LIVE_REAL | button-registry.spec.ts, full-interface.spec.ts |
| `top.deep` | Topbar | deep/web-search opener | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts |
| `top.scope` | Topbar | scope opener | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts |
| `context.actions` | Context | context panel actions | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts |
| `top.star` | Topbar | star/brand interactions | `—` | INTENTIONAL_LOCAL_ONLY | button-registry.spec.ts, v197-star-brain.spec.ts |
| `universe.composer` | Universe | universe composer | `—` | LIVE_REAL | button-registry.spec.ts, full-interface.spec.ts |
| `research.stage` | Research | stage question | `POST /api/v1/research/briefs` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts, sol-live-new-surfaces.spec.ts |
| `research.live-fetch` | Research | live web retrieval (honest NOT_CONNECTED; nothing fabricated) | `none (provider absent)` | BLOCKED_BY_EXTERNAL_PROVIDER | sol-live-new-surfaces.spec.ts |
| `scope.choice` | Scope | privacy scope options | `PATCH /api/v1/profile/preferences` | LIVE_REAL | full-interface.spec.ts, button-registry.spec.ts, v197-control-matrix.spec.ts |
| `scope.language` | Language | locale switch | `PATCH /api/v1/profile/preferences` | LIVE_REAL | visual-readiness.spec.ts, v197-language-wordmark.spec.ts, button-registry.spec.ts |
| `insights.review` | Insights | accept/reject/correct | `POST /api/v1/insights/:id/*` | LIVE_REAL | talk.spec.ts, button-registry.spec.ts |
| `community.rooms.shell` | Community shell | room title/message | `POST /api/v1/community/rooms` | LIVE_REAL | community-group-nur.spec.ts, button-registry.spec.ts |
| `community.members` | Community shell | add member | `POST /rooms/:id/members` | LIVE_REAL | community-group-nur.spec.ts, button-registry.spec.ts |
| `council.flow` | Council | council position/flow | `POST /rooms/:id/positions` | LIVE_REAL | community-group-nur.spec.ts, button-registry.spec.ts |
| `community.legacy-tabs` | Community shell | legacy staged tabs | `—` | NOT_IMPLEMENTED_VISIBLE | button-registry.spec.ts |
| `ritual.control` | Shell | ritual action | `—` | NOT_IMPLEMENTED_VISIBLE | button-registry.spec.ts |
| `voice.composer` | Composer | voice input | `—` | NOT_IMPLEMENTED_VISIBLE | button-registry.spec.ts |
| `capsule.ask` | Capsule | Ask from approved context | `POST /capsules/:id/ask` | LIVE_REAL | capsule.spec.ts |
| `capsule.copy` | Capsule | Copy room address | `—` | INTENTIONAL_LOCAL_ONLY | capsule.spec.ts |
| `capsule.audit` | Capsule | Open access audit | `GET /capsules/:id/audit` | LIVE_REAL | capsule.spec.ts |
| `capsule.revoke` | Capsule | Revoke now | `POST /capsules/:id/revoke` | LIVE_REAL | capsule.spec.ts |
| `settings.toggles` | Settings | sound/motion/omega toggles | `—` | LIVE_REAL | sol-live-new-surfaces.spec.ts, v197-control-matrix.spec.ts |
| `settings.save` | Settings | Save preferences | `PATCH /api/v1/profile/preferences` | LIVE_REAL | sol-live-new-surfaces.spec.ts, v197-control-matrix.spec.ts |
| `settings.export` | Settings | Export my NUR (visibly disabled with stated reason) | `—` | NOT_IMPLEMENTED_VISIBLE | sol-live-new-surfaces.spec.ts |
| `settings.delete` | Settings | Delete account | `—` | NOT_IMPLEMENTED_VISIBLE | sol-live-new-surfaces.spec.ts |
| `omega.consolidate` | Omega | Consolidate owner evidence | `POST /api/v1/omega/consolidate` | LIVE_REAL | omega-research.spec.ts |
| `omega.export` | Omega | Export owner Omega | `GET /api/v1/omega/export` | LIVE_REAL | omega-research.spec.ts |
| `omega.why` | Omega | Why changed? | `—` | LIVE_REAL | omega-research.spec.ts |
| `omega.claim-confirm` | Omega | Confirm claim | `POST /omega/claims/:id/confirm` | LIVE_REAL | omega-research.spec.ts |
| `omega.claim-retire` | Omega | Retire claim | `POST /omega/claims/:id/retire` | LIVE_REAL | omega-research.spec.ts |
| `omega.review-approve` | Omega review | Approve as reviewed | `POST /omega/review/:id/approve` | LIVE_REAL | omega-research.spec.ts |
| `omega.review-reject` | Omega review | Reject | `POST /omega/review/:id/reject` | LIVE_REAL | omega-research.spec.ts |
| `consultation.create` | Consultations | Open Consultation | `POST /api/v1/consultations` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `consultation.open` | Consultations | Enter Consultation | `GET /consultations/:id` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `consultation.contribute` | Consultation detail | Add contribution | `POST /consultations/:id/contributions` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `consultation.stage` | Consultation detail | Persist next stage (RETURN outcome never fabricated) | `POST /consultations/:id/stages/:stage` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `community.return` | Community | Open bounded Community | `—` | LIVE_REAL | sol-live-new-surfaces.spec.ts, community-group-nur.spec.ts |
| `community.room-create` | Community | Create Group NUR room | `POST /community/rooms` | LIVE_REAL | community-group-nur.spec.ts, sol-live-new-surfaces.spec.ts |
| `community.start-consultation` | Community | Start Consultation | `POST /consultations` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `community.room-open` | Community | Enter bounded room | `GET room detail` | LIVE_REAL | community-group-nur.spec.ts, sol-live-new-surfaces.spec.ts |
| `community.message-send` | Room | Send to room | `POST /rooms/:id/messages` | LIVE_REAL | community-group-nur.spec.ts |
| `community.post-create` | Room | Publish in room | `POST /rooms/:id/posts` | LIVE_REAL | community-group-nur.spec.ts |
| `community.post-open` | Room | Open thread | `GET post detail` | LIVE_REAL | community-group-nur.spec.ts |
| `community.react-useful` | Thread | ✦ Useful | `POST reactions` | LIVE_REAL | community-group-nur.spec.ts |
| `community.react-witness` | Thread | Witness | `POST reactions` | LIVE_REAL | community-group-nur.spec.ts |
| `community.comment-create` | Thread | Reply | `POST comments` | LIVE_REAL | community-group-nur.spec.ts |
| `community.future-tabs` | Community | future surfaces | `—` | NOT_IMPLEMENTED_VISIBLE | sol-live-new-surfaces.spec.ts |
| `project.create` | Projects | Create Project Orbit | `POST /api/v1/projects` | LIVE_REAL | sol-live-new-surfaces.spec.ts, project-deliverables.spec.ts |
| `project.open` | Projects | Open Project Orbit | `GET project bundle` | LIVE_REAL | sol-live-new-surfaces.spec.ts, project-deliverables.spec.ts |
| `project.tabs` | Project Orbit | surface tabs (was MISLEADING: all 9 tabs rendered identical content) | `—` | LIVE_REAL | v197-control-matrix.spec.ts |
| `project.task-create` | Project Orbit | Add task | `POST /projects/:id/tasks` | LIVE_REAL | project-deliverables.spec.ts, sol-live-new-surfaces.spec.ts |
| `project.task-done` | Project Orbit | Close with passed evidence | `PATCH /projects/tasks/:id` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.evidence-create` | Project Orbit | Record passed evidence | `POST /projects/:id/evidence` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.run-propose` | Project Orbit | Propose agent run | `POST /projects/:id/runs` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.run-approve` | Project Orbit | Approve bounded run | `POST /projects/runs/:id/approve` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.run-cancel` | Project Orbit | Cancel run | `POST /projects/runs/:id/cancel` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.review-create` | Project Orbit | Record owner approval | `POST /projects/:id/reviews` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `project.file-choose` | Deliverables | file picker (was native browser-default control) | `—` | LIVE_REAL | project-deliverables.spec.ts |
| `project.file-upload` | Deliverables | Upload file | `POST /projects/:id/files (multipart)` | LIVE_REAL | project-deliverables.spec.ts |
| `project.file-download` | Deliverables | Download | `GET /projects/files/:id/download` | LIVE_REAL | project-deliverables.spec.ts |
| `project.run-evidence-package` | Deliverables | Generate evidence package (real backend path proven by API suite + live Celery worker smoke) | `propose→approve→queue run` | LIVE_REAL | project-deliverables.spec.ts |
| `glow.view` | Glow | glow ledger view | `GET /glow/summary+scoreboard` | LIVE_REAL | sol-live-new-surfaces.spec.ts, visual-readiness.spec.ts |
| `notification.open` | Notifications | Open | `—` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `notification.read` | Notifications | Mark read | `POST /notifications/:id/read` | LIVE_REAL | sol-live-new-surfaces.spec.ts |
| `notification.preferences-save` | Notifications | Save notification boundary | `PATCH /notifications/preferences` | LIVE_REAL | sol-live-new-surfaces.spec.ts, v197-control-matrix.spec.ts |
| `notification.reminder-create` | Notifications | Create in-app reminder | `POST /notifications/reminders` | LIVE_REAL | sol-live-new-surfaces.spec.ts |

## Fixed in this mission

- `project.tabs` — **was MISLEADING**: all nine Project Orbit tabs rendered the
  same six panels. Each tab now shows its own real surface; tabs without a
  dedicated surface state that honestly instead of repeating identical content.
- `project.file-choose` — **was a visual defect**: the deliverables file picker
  rendered the browser's native light-gray control inside the void-black
  adjunct. It now uses the NUR control language via `::file-selector-button`.

## Truthful blockers

- `talk.provider-disabled` and `research.live-fetch` remain
  `BLOCKED_BY_EXTERNAL_PROVIDER` until a real credential exists; both show
  honest visible states and never fabricate results.
