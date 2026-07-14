# Streaks, Quests, Levels, and Achievements

Date: 2026-07-11

## Current state

Only the server-owned streak primitive is live. `glow_streaks` tracks `current_count`, `best_count`, `last_event_date`, and `repairs_remaining` per owner/streak key. Same-day events do not increase the count; consecutive UTC dates do; a gap resets to one. No quest, level, achievement, or repair-spend claim is live.

## Track B design

### Quests

- definitions are versioned and localized;
- progress is event-sourced from verified Glow reward events;
- daily quests expire predictably; weekly quests retain partial progress;
- completion is idempotent and owner-scoped;
- examples: return one Outcome, reduce one blocked step, resolve one contradiction.

### Levels

- levels derive from lifetime verified Glow, never purchased balance;
- thresholds and unlocked capabilities are explicit;
- reversals do not remove already-earned accessibility or data rights;
- level labels describe practice depth, not human worth.

### Achievements

- evidence-backed milestones such as first Outcome, seven returned Outcomes, first corrected claim, and successful Capsule collaboration;
- private by default; sharing requires a deliberate boundary choice.

### Streak repair

- limited repair inventory can be earned, not coercively sold;
- missed days do not erase lifetime progress;
- copy avoids threat, shame, or fabricated urgency;
- timezone and daylight-saving behavior must be deterministic.

## Required data/tests before claiming live

Add versioned quest definitions, assignments, progress events, level ledger, achievements, repair transactions, localization, owner RLS, anti-replay constraints, timezone tests, cross-user denial, reward reversal tests, and Playwright proof. Until then V197 must show only persisted current/best streak data from Track A.
