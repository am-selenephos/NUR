# Engagement Loop Specification

Date: 2026-07-11  
Founder requirement: NUR must create a compelling return loop, with Glow Points, streaks, quests, levels, variable rewards, and social loops. Track A may only claim the parts that persist today.

## Implemented Track A loop

1. **Orient:** owner enters the exact V197 universe and sees current persisted state.
2. **Express:** Today or Talk stores a private owner event.
3. **Shape:** the owner moves a real line into Journal or Plan.
4. **Act:** a Plan step is completed or made smaller.
5. **Return:** the owner records what changed in the real world.
6. **Reward:** server verifies the owned source, enforces idempotency/daily cap, persists a Glow transaction, and updates balance/streak.
7. **Recall:** Today, Systems, Timeline, and Glow surfaces hydrate the persisted result after refresh.

This loop uses no fabricated counters. A button click alone cannot mint Glow.

## Track B loops

| Loop | Required implementation | Guardrail |
|---|---|---|
| streak rescue | repair token and missed-day recovery | opt-in, no shame copy |
| quests | daily/weekly evidence-backed tasks | no reward for empty clicks |
| levels | capability unlocks from verified cumulative Glow | publish thresholds and reversals |
| variable rewards | bounded reward envelopes for high-value returns | auditable RNG/rule record; no pay-to-win |
| Signal Feed | ranked owner/group/community returns | privacy labels, diversity and recency constraints |
| social return | Group NUR response, consultation, collaboration outcome | explicit membership and recipient scope |
| notifications | re-entry prompt based on unfinished owner work | quiet hours, caps, disable control |

## Metrics without private-content leakage

Record only event IDs, surface, action class, latency, completion state, experiment assignment, and coarse locale. Do not send raw Talk, Journal, Capsule, source, or Group content to analytics. Primary measures are activation to first persisted outcome, seven-day return, outcome-to-Glow integrity, useful-plan completion, and notification opt-out/harm signals.

## Acceptance

- Track A: `Talk -> Journal -> Plan -> Outcome -> Glow` survives refresh and duplicate reward calls do not double mint.
- Track B: each claimed loop needs server state, permission tests, opt-out behavior, and longitudinal retention/harm evaluation before release.
