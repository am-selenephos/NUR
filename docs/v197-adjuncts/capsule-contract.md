# Capsule V197-Native Adjunct Contract

Status: implemented as a plain-DOM bridge adjunct in `apps/web/src/bridge/v197Adjuncts.ts`; canonical V197 bytes remain unchanged.

1. Route: `/capsule/:id`.
2. Source file path: `apps/web/src/bridge/v197Adjuncts.ts` (recipient and owner lifecycle renderers; no React visual component).
3. Visual relationship: a standalone plain-DOM V197 sibling, using the canonical void, Bodoni Moda, Crimson Pro, warm glass, star language, and bounded-room privacy hierarchy. It cannot import React or React CSS.
4. DOM sections: approved-room masthead; capsule state strip; purpose/access/expiry card; included-source ledger; excluded-source boundary; scoped-question composer; answer ledger; revoke/expiry terminal state.
5. Controls: ask scoped question; copy room address; owner revoke; owner access audit; source filters. Recipient controls never expose owner-global navigation.
6. Backend endpoints: `GET /api/v1/capsules/:id/view`, `POST /api/v1/capsules/:id/questions`, owner capsule/audit/revoke endpoints already exposed under `/api/v1/capsules` and `/api/v1/orbits/:orbitId/capsules`.
7. Security boundaries: recipient is limited to active grant, current capsule version, and included `capsule_sources`; no owner Talk, Journal, Timeline, Omega, preference, or general-memory request is allowed. Revocation and expiry must block cached reads and asks.
8. Empty states: no active grant, no included source, read-only capability, revoked, expired, and provider-disabled each have an honest V197-native state with no invented answer.
9. Tests: owner-create; recipient-read; excluded-source denial; scoped answer grounding; revoke/ask race loop; expiry; direct owner-API recipient denial; no React root; no white native controls.
10. Screenshots: owner share sheet trigger; active room; read-only room; scoped-answer room; revoked room; expired room; mobile WebKit active/revoked.
