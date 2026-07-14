# Glow Points Economy

Date: 2026-07-11  
Implementation: migration `0011_track_a_glow_translation.py`, `services/glow_service.py`, `/api/v1/glow/*`, and `v197Rewards.ts`.

## Implemented ledger

| Verified event | Points | Daily cap | Streak key |
|---|---:|---:|---|
| persisted private daily check-in | 2 | 2 | `daily_orbit` |
| persisted meaningful Talk turn | 2 | 10 | `talk` |
| persisted Journal entry | 4 | 12 | `journal` |
| persisted Plan | 4 | 8 | `plan_movement` |
| completed owned Plan step | 8 | 32 | `plan_movement` |
| made an owned step smaller | 3 | 12 | `plan_movement` |
| persisted real-world Outcome | 15 | 45 | `outcome_return` |

Rules live in `glow_rules`. Balances, transactions, reward events, and streaks are separate owner-scoped tables with forced RLS from migration 0011.

## Integrity law

- Client submits event type, source kind/id, orbit, and idempotency key.
- Server reloads the source under the authenticated owner.
- Event/source pairs are allowlisted; a completed-step reward requires `done=true`.
- Orbit mismatch, unsupported source, missing owner record, inactive rule, or cap overflow fails closed.
- Idempotency replay returns the original transaction and never increments balance twice.
- V197 renders only `/glow/summary` and verified award responses.

## Economy state

Track A implements earning, balance, lifetime total, recent transactions, and basic daily streak rows. Spending, repair pricing, gifts, purchases, transfer, marketplace, quest multipliers, level thresholds, and social reputation are **not implemented** and must not be shown as live.

## Acceptance evidence

`test_track_a_vertical_slice.py` proves owner source validation, idempotency, caps, outcome gating, and persisted summary. `track-a-sellable.spec.ts` proves a returned Outcome moves the visible balance and survives refresh.
