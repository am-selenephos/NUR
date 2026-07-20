# Remaining Gaps

Date: 2026-07-13 · Updated: 2026-07-20 (Fable final-readiness pass on
`build-week-submission` @ `c823512`)

## Honest gaps after the V197 adjunct, Consultation, Projects and notification gates

1. Thirty-five locale choices exist, but most remain explicitly
   draft/machine-translated; only core interface slots are reviewed in
   selected beta locales. New community strings are English-first hydration
   copy, consistent with the other lenses.
2. Dynamic translation is a persisted foundation, not a production
   translation provider.
3. Research is local question staging only; no web source is fetched or
   invented.
4. Bounded Community rooms, messages, members, posts, nested comments,
   reactions and Council positions/decisions are persisted and visible in
   V197-native surfaces. Public SSR, follows/saves, ranking, production
   moderation operations and public discovery remain Track B.
5. Capsule, Settings, Omega, Consultation, AM Projects, Glow and Notifications
   have V197-native adjunct surfaces. React visual fallbacks are intentionally
   not used. AM Project file storage, collaborator grants and real external
   agent execution adapters remain incomplete.
6. Quests, levels beyond thresholds, variable reward policy, and richer
   anti-abuse operations remain Track B. Glow idempotency stays key-based;
   caps and spam windows bound repeat-award abuse, not a per-source unique
   constraint.
7. Owner-scoped in-app notifications and quiet-hour preferences are real.
   External push/email delivery, notification scheduling workers,
   monetization and paid retention are not implemented or claimed.
8. Real WebKit mobile proof runs in the official Playwright container; it is
   not relabelled Chromium. Fresh reruns remain part of the final gate after
   each visible-surface change.
9. (Superseded 2026-07-20: this workspace is a Git clone of
   `am-selenephos/NUR` at submission SHA `c823512`; the 2026-07-12 tar/SHA
   checkpoint note applied to the earlier non-Git recovery workspace only.)
10. Capsule creation (source selection, representation choice, recipient
   grant) is owner-API-level in this beta: the React share sheet was retired
   with the frontend forensic rebuild and no V197-native creation surface
   replaced it yet. The recipient room, owner lifecycle/audit/revoke room,
   and the two-account browser lifecycle proof (`e2e/capsule.spec.ts`) all
   run against the live V197 surface.
11. A tail of pre-rebuild Playwright specs (auth, landing-auth partly,
   full-interface, omega-research, talk-persistence, universe-lenses,
   v197-host-parity) still targets the retired React routes or the
   Phase 1 404-law and fails on the current shell. They are retained
   unmodified pending a founder decision on retirement; the surfaces they
   covered are proven by the current-generation specs instead.
   `sol-live-new-surfaces` additionally requires a configured OpenAI
   runtime and is only provable in openai mode.

## Verdict boundary

The Track A owner loop and the bounded Group NUR, Consultation, Project,
Capsule, Omega, Settings, Glow and notification slices are implemented. Fresh
command counts belong in the evidence packet, not this durable gap file. The
gaps above prohibit `FULL_PASS`; they do not invalidate the proven slices.
