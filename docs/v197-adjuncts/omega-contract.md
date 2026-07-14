# Omega V197-Native Adjunct Contract

Status: implemented as a plain-DOM bridge adjunct in `apps/web/src/bridge/v197Adjuncts.ts`; canonical V197 bytes remain unchanged.

1. Routes: `/universe/omega`, `/universe/omega/review`, and `/universe/omega/why-changed/:claimId`.
2. Source file path: `apps/web/src/bridge/v197Adjuncts.ts` (dashboard, review and why-changed renderers; no React visual component).
3. Visual relationship: plain-DOM V197 research chambers, not React cards. The evidence graph, contradiction ledger, and review surfaces inherit V197's private-system visual language and never claim consciousness or expose chain-of-thought.
4. DOM sections: owner research masthead; evidence graph; claim ledger; contradiction/prediction columns; learning proposal queue; review actions; why-changed provenance chain; export status.
5. Controls: consolidate; approve/reject/retire/mark-wrong claim; resolve contradiction; approve/reject/rollback proposal; open why-changed; owner export.
6. Backend endpoints: existing `/api/v1/omega/*` dashboard, claims, contradictions, predictions, review queue, consolidation, export, and scheduler status routes.
7. Security boundaries: owner-only Omega RLS; recipients cannot read, mutate, export, or infer owner Omega state; no automatic changes to RLS, auth, secrets, or policies.
8. Empty states: no evidence, no claims, no contradiction, no prediction, scheduler unavailable, and review-needed states are factual and non-anthropomorphic.
9. Tests: owner dashboard/review/why-changed; recipient API denial; claim confirmation policy; export ownership; scheduler status; WebKit/mobile no overflow; no React root.
10. Screenshots: dashboard; evidence graph; review queue; why-changed; empty evidence; RTL Urdu; mobile WebKit dashboard/review.
