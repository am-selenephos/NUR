# NUR Total System Architecture

```text
Exact V197 host/runtime
  -> idempotent nonvisual bridge
  -> FastAPI owner/shared APIs
  -> service layer and provenance verifier
  -> PostgreSQL + forced RLS
  -> Redis/Celery/Omega beat
  -> disabled/OpenAI server provider
```

## Domain layers

1. **Identity and boundary:** users, sessions, profiles, consent, CSRF, RLS.
2. **Personal evidence:** cognition events, Journal, decisions, references, corrections, outcomes.
3. **Action:** goals, objectives, Plans, steps, schedules, Today actions.
4. **Living model:** seven Systems, diagnostics/actions/progress, Body/Mind/Life, predictions.
5. **Reward:** Glow rules, transactions, streaks, achievements, levels, leaderboards.
6. **Intelligence:** retrieval, task router, structured provider, verifier, memory candidates, Omega.
7. **Universe:** live aggregate, graph Map, Timeline, Orbits, Insights, feasibility.
8. **Outside/shared:** Research, Web Signals, Community, Group NUR, Council, Capsule.
9. **Work:** AM Projects, tasks, evidence, runs, reviews, deliverables.
10. **Language/experience:** 35-locale metadata/catalogs, translation provenance, RTL, V197 motion/performance.

## Data flow law

Meaningful action persists first. Services then emit provenance/audit/Timeline state and request an eligible idempotent Glow award. Universe read models aggregate only committed owner-visible records. Model output never becomes observed truth without provenance and confirmation gates.

## Visual law

No React visible renderer. Existing V197 slots are mutated narrowly. Missing surfaces are plain DOM/CSS/runtime adjuncts with V197 tokens, focus management, mobile geometry, and bridge/API bindings.
