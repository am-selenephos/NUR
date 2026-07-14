# Map, Timeline, and Prediction Specification

## Graph Map

Owner graph nodes cover NUR, seven Systems, goals, objectives, Plans, people/groups, Projects, Insights, blockers, predictions, Timeline events, and Glow milestones. Edges retain typed source/target relationships. Existing V197 seven-node geometry remains the first ring; detail/future paths live in the native panel rather than colliding with the star.

Map APIs aggregate current records, rebuild typed edges idempotently, and create/predict paths from System/goal/Plan/Insight. Predictions are labelled hypotheses with evidence, horizon, confidence, and invalidation conditions.

## Timeline

Timeline combines immutable past evidence, current state, scheduled future actions, predictions, and returned Outcomes. Future actions support complete, miss, reschedule, make easier, and Outcome. Each mutation updates Today, System progress, Map, Insights, and Glow.

## Prediction paths

For a target, return: continue path, ignore path, easier path, ambitious path, likely blocker, and best next move. Deterministic baseline predictions use persisted progress/missed/blocker data; provider enrichment is schema-validated and cannot overwrite observed facts.

## Acceptance

- seven real Systems and their progress appear;
- node click opens persisted detail and action;
- Plan/System action creates future Timeline state;
- complete/miss/reschedule changes persisted state and Today;
- prediction cites owner-visible evidence and can later be confirmed/wrong;
- map/star/Creation labels remain collision-free on desktop/mobile/WebKit.
