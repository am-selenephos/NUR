# Presentation Auth Recovery

Date: 2026-07-13

Source artifacts reviewed:

- `NUR_PRESENTATION_AUTH_PATCH_ONLY_20260713.zip`
- `NUR_PRESENTATION_AUTH_RECOVERY_20260713.zip`
- `PRESENTATION_RECOVERY_README.md`

The supplied patch targeted the older React `api.ts`, `AuthProvider.tsx` and
`Landing.tsx` path. The production presentation is now the canonical V197
runtime plus `v197ApiClient.ts` and `v197Bridge.ts`; applying those React files
would not fix the visible product and could reintroduce visual ownership.

The recovery law was therefore ported to the actual production path:

- all V197 bridge API requests fail visibly after 12 seconds;
- malformed JSON is reported as an invalid API response;
- non-401 session errors remain errors;
- signup verifies `/auth/me` and the created identity before Universe entry;
- login already verifies `/auth/me` and keeps that law;
- owner snapshot hydration succeeds before the canonical Universe is revealed;
- an initial session-check failure leaves Entry usable and displays a concrete
  diagnostic instead of silently abandoning auth binding;
- `infra/scripts/presentation-recovery.sh` performs a non-destructive disabled
  boot and verifies health, readiness, login cookie and `/auth/me`.

Canonical V197 remains byte-unchanged. React visual files from the recovery ZIP
were not copied into the production path.
