# NUR Data Flow Map

Date: 2026-07-09

## Owner Capture To Intelligence

1. Owner writes Talk, Journal, Plan, Research, Community, or Web Signal input.
2. Backend persists an owner-scoped row and emits an owner-scoped `cognitive_events` timeline record with a provenance label.
3. Outcomes create `OUTCOME_REPORTED` events and are the only path that can increase visible Glows.
4. Omega consumes evidence from owner-scoped events through consolidation/review services and records claims, contradictions, predictions, proposals, and review queue entries.
5. Insights and Timeline read the owner ledger back through `/api/v1/universe/*` endpoints.

## Talk Provider Path

1. Frontend sends user message plus locale and writing preference to `/api/v1/cognition/talk`.
2. Backend chooses provider from server env only.
3. Disabled mode persists the user turn and returns an honest provider-disabled response.
4. OpenAI mode uses the server-only provider, validates strict schema output, records `model_runs`, records `MODEL_RESPONSE`, and returns only schema fields.
5. Frontend renders direct response, observed/inferred/hypothesis/uncertainty, next move, memory candidates, and source refs.

## Research / Community / Web Signals

1. Research briefs, source notes, consultation notes, web signal questions, and web signal notes are owner-owned.
2. Each object emits a matching timeline event:
   `RESEARCH_BRIEF_CREATED`, `RESEARCH_SOURCE_NOTE_ADDED`, `COMMUNITY_NOTE_CREATED`, `WEB_SIGNAL_QUESTION_STAGED`, or `WEB_SIGNAL_NOTE_ADDED`.
3. These surfaces never invent live web/community data. If a live provider is not connected, the UI says so and saves local notes/questions only.

## Context Capsule

1. Owner creates an Orbit, decisions/references/sources, then opens Share Orbit.
2. Owner chooses purpose, recipient, expiry/capability, and included sources.
3. Backend creates a capsule and grant bound to selected sources only.
4. Recipient opens `/capsule/:id`, sees approved sources/excluded summary, and can ask only scoped questions.
5. Revoked/expired grants block reads and questions; recipient never receives owner Talk, Journal, Timeline, Omega, or general memory.

## Language

1. Settings persists `profile.locale` and `profile.writing_preference` owner-only.
2. Frontend applies `dir=rtl` for `ur`, `ar`, and `fa`.
3. Roman Urdu is `locale=ur` plus `writing_preference=roman`, not a fake locale.
4. Talk passes locale and writing preference to the backend provider prompt metadata.
