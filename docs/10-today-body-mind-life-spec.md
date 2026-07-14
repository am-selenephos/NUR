# Today and Body/Mind/Life Specification

## Response contract

`GET /api/v1/today` returns current owner-local date, day label, daypart, Body/Mind/Life scores with contributing/lowering sources, active Systems/goals/Plans, completed/missed actions, Glow today/weekly, streak, quest, next move, latest Insight, and Timeline items.

## Score derivation

- **Body:** Body System activity, body diagnostics/actions, physical Rebuild actions, returned body outcomes.
- **Mind:** Quiet Ambition, Study, Journal, corrections/Insights, mental Rebuild actions.
- **Life:** Money, Connection, Creation, nonphysical Rebuild, project and relationship outcomes.

Each dimension begins from a neutral evidence floor and changes only from persisted recent evidence. The response includes components, timestamps, and a recommended action. No random percentage or hidden model score.

## Mutations

- check-in persists structured Body/Mind/Life input;
- complete/miss/make-easier update a scheduled/System action;
- plan-day creates owner actions from selected goals/Plans;
- every mutation emits Timeline provenance and eligible Glow after commit.

## V197 UI

Reuse `#page-today`: date/daypart header, three explainable meters, next move, daily quest/streak/Glow, completed/missed list, and canonical buttons for talk, plan, complete, miss, and make easier.
