# Settings V197-Native Adjunct Contract

Status: implemented as a plain-DOM bridge adjunct in `apps/web/src/bridge/v197Adjuncts.ts`; canonical V197 bytes remain unchanged.

1. Route: `/settings`.
2. Source file path: `apps/web/src/bridge/v197Adjuncts.ts` (semantic DOM mutation only; no React visual component).
3. Visual relationship: a plain-DOM V197 sibling shaped as an owner-only private ledger, never a generic settings dashboard. It uses the same rail rhythm, scope language, star accents, and black-holographic materials.
4. DOM sections: provider status; safe local OpenAI instructions; language/writing preference; sound/reduced-effects; Omega preference; export placeholder; deletion placeholder; dev-only reset confirmation.
5. Controls: refresh provider status; open local setup instructions; locale select; writing preference select; save preferences; sound toggle; Omega toggle; dev reset; honest export/delete placeholders.
6. Backend endpoints: `GET/PATCH /api/v1/profile/preferences`, health/ready/metrics reads, provider-capability reads, and only local scripts for OpenAI configuration.
7. Security boundaries: owner-only preferences; never render or transmit API keys; no provider credentials in DOM/storage/logs; recipient has no Settings route access.
8. Empty states: disabled provider, OpenAI not configured, OpenAI configured, draft locale warning, unsupported writing preference, and unavailable export/delete are all explicit.
9. Tests: owner preference persistence; recipient denial; Roman Urdu maps to `locale=ur` and `writing_preference=roman`; RTL layout; no key disclosure; no React root.
10. Screenshots: provider-disabled; provider-configured; language selector; Roman Urdu; Urdu RTL; Arabic RTL; mobile WebKit settings.
