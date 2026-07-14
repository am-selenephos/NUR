# SOL Glow Economy Specification

## Existing real core

`glow_rules`, `glow_balances`, `glow_transactions`, `glow_streaks`, and `glow_reward_events` are source-linked and owner-scoped. The service verifies owner/source/event match, completion state, Orbit, daily cap, and idempotency.

## SOL expansion

- normalize rule keys to dotted action names while preserving old aliases;
- add daily and weekly earned totals, derived level, next unlock, rank, and anti-spam window;
- add achievements linked to source transaction;
- provide real personal and System leaderboards; shared leaderboards only after membership domains exist;
- add owner ledger pagination and rule/cap disclosure;
- broaden rules for corrections, goals, schedules, system actions, research, Community, Group/Council, and Projects as those persistent sources ship.

## Level curve

Initial transparent thresholds: Seed 0, Spark 50, Orbit 150, Constellation 350, Radiant 700, Architect 1,200. Levels derive from lifetime verified Glow, not purchasable balance.

## Reward law

`persist source -> validate ownership/state -> check idempotency/caps/spam -> transaction -> balance/streak/achievement -> Timeline event -> UI`. No click-only reward and no fabricated leaderboard member.

## UI

Today shows today/weekly/lifetime, level, streak, next unlock, quest/mission state. A V197-native ledger/scoreboard shows each source. Demo shared entries must carry `DEMO`; production defaults to owner-only.
