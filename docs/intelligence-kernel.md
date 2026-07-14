# NUR Actual Intelligence Kernel

Date: 2026-07-11  
Current implementation: `apps/api/app/cognition/intelligence_kernel.py` and supporting cognition/AI/Omega modules.

## Implemented request path

1. authenticated owner sends a line, Orbit, locale, writing preference, and mode;
2. `task_router.py` selects a bounded task mode;
3. cognition event is persisted as owner-written provenance;
4. `memory_service.py` retrieves owner-scoped evidence;
5. Omega workspace frame provides bounded contradictions/predictions when enabled;
6. disabled or OpenAI provider is selected server-side;
7. structured output schema is validated;
8. source references are checked against allowed evidence;
9. model run and `MODEL_RESPONSE` event persist;
10. V197 Talk hydrates the saved response after refresh.

Disabled mode stores the owner turn and returns an honest not-connected state. OpenAI mode requires ignored local `.env.local`; no provider secret enters V197, browser storage, source package, screenshots, or logs.

## Intelligence representation

- provenance: owner-written, model-generated, observed outcome, measured, correction;
- epistemic state: observed, inferred, hypothesis, uncertain/contradicted;
- memory: events, Orbit sources, decisions, references, outcomes, corrections;
- workspace: active question, evidence set, contradictions, predictions, proposed next move;
- learning: owner-governed Omega claims/proposals rather than hidden prompt mutation.

## Not implemented as a claim

NUR is not represented as sentient, conscious, AGI, or independently sovereign. It has no uncontrolled self-modification and no autonomous real-world action. Persistent agents/tool orchestration for AM Projects is Track B.

## Required hardening

Real-provider smoke in the final deployment environment, budget enforcement, provider failover policy, retrieval quality evaluation, multilingual schema evaluation, adversarial source-reference tests, long-term memory compaction evaluation, model drift monitoring, and project-tool permission proof remain release gates.
