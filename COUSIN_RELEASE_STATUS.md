# NUR Cousin Demo Release Status

Release date: 2026-07-14

## What this package proves

- Canonical V197 presentation remains the visible interface; React does not own the visible DOM.
- Fresh signup establishes the normal secure session, enters Today automatically, and survives refresh.
- Real Talk uses the server-side OpenAI provider when a local key is configured.
- Model runs and model responses persist and remain visible after refresh.
- Today, Talk, Journal, Plan, outcome return, Glow, Systems, Map, Orbits, Timeline, and Insights are wired for the Track A demo.
- The NUR wordmark keeps its Bodoni Moda face and animated holographic rainbow treatment.
- The Systems wordmark and subtitle are centered above the MasterStar with measured clearance.
- Entry and Universe receive a deterministic static star layer with no new animation loop.
- One launcher starts Postgres, Redis, FastAPI, worker, scheduler, V197 web, demo seed, health checks, and browser open.

## One-click launch

Linux: double-click `START_NUR.desktop`.

Terminal fallback:

```bash
bash START_NUR.sh
```

The first interactive launch asks for the receiver's own OpenAI API key using hidden input. The key stays only in ignored `.env.local` with mode 600. It is not included in this package.

## Current measured checks

- Frontend unit tests: 63 passed.
- Fresh signup auto-entry focused browser proof: passed.
- Track A browser proof: 2 passed at 1280 and 1440 with pixel clearance assertions.
- Backend tests: 82 passed in the latest unchanged-backend run.
- Real OpenAI smoke: provider, schema, persistence, refresh, Settings status, and browser secret isolation passed in the latest provider run.
- Headed Chromium Systems cadence improved from 21 FPS / 112 ms p95 to 50.3 FPS / 41.6 ms p95 on this host.
- Static Universe stars at 1440x900: 191, painted once and on debounced resize only.

## Honest scope

This is a working Track A cousin demo, not the completed V5 global platform. Full Community, Group NUR, Consultation, AM Projects, billing, full engagement economy, and human-reviewed coverage for all 35 locales remain later product work. Disabled provider mode is an honest structural demo and is not chatbot proof.
