# Source Authority Report

Date: 2026-07-11

## Canonical presentation

| Artifact | SHA-256 | Status |
|---|---|---|
| `apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html` | `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3` | canonical host, unchanged |
| `docs/reference/entry_decoded_v197.html` | `49e2e72fb3adea405428789d9235dfc5ecb122f8dc1e17205d4fa05de64ecd97` | byte-verified decoded Entry |
| `docs/reference/universe_decoded_v197.html` | `b80eb5198d6fd9088e999020bd1cf85e95af9a20fd4ab172cfb7d5726dbd5a3c` | byte-verified decoded Universe |

`infra/scripts/check-v197-integrity.sh` recalculates all three hashes and passed on 2026-07-11.

## Production presentation path

`apps/web/vite.config.ts` serves the canonical host document for V197-native routes and adds exactly one nonvisual module loader before `</body>`. `apps/web/src/main.ts` starts the bridge. The visible Entry and Universe remain isolated full-viewport documents owned by canonical V197.

## Non-authoritative visual code

Legacy React routes/components and old V197-extracted CSS remain source history only. They are not loaded into the visible canonical iframe documents. No React `#root`, `ReactDOM`, `global.css`, or React geometry sheet is accepted as presentation evidence.

## Allowed Track A mutation

The bridge may:

- update established copy/data slots;
- add controls required for a persisted action inside an existing V197 chamber;
- bind canonical controls to owner-scoped APIs;
- add the single `nur-v197-track-a-premium-polish` corrective stylesheet at runtime.

The corrective layer does not alter the canonical file on disk and does not replace V197 DOM, star geometry, wordmark, palette, or typography.

