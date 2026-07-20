# NUR — Build Week Submission Brief

## Submission title

**NUR: Evidence-Bound Context Capsules**

## One-line description

NUR is a private AI workspace that turns messy personal or project context into structured, source-traceable decisions, then lets the owner share only explicitly approved context through revocable Context Capsules.

## The problem

People use AI inside long, sensitive conversations, but ordinary assistants blur three different operations:

1. reasoning over private context;
2. deciding what should become durable memory;
3. sharing context with another person.

That creates predictable failures: invented certainty, hidden context leakage, unreviewed memory, and all-or-nothing sharing.

## The NUR approach

NUR separates those operations.

- **Private Talk** reasons over owner-scoped evidence.
- **Structured output** distinguishes observed facts, inference, hypotheses, uncertainty, and one next move.
- **Verification** checks that model source references actually exist in the retrieved packet.
- **Owner-controlled persistence** keeps decisions, references, journal entries, plans, corrections, outcomes, and model-run traces.
- **Context Capsules** include only owner-approved sources and representations.
- **Recipient rooms** expose the boundary, the included sources, the withheld-source summary, the answer mode, and the source references.
- **Revocation** closes access immediately and records the event in the audit trail.

## Competition demo scope

The submission deliberately demonstrates one complete vertical slice rather than pretending the entire NUR vision is finished.

### Owner flow

1. Sign in to the local NUR workspace.
2. Open **Talk** inside a private Project Orbit.
3. Ask NUR to help resolve a real decision.
4. Show the OpenAI-backed structured response:
   - Observed
   - Inferred
   - Hypotheses
   - Uncertainty
   - One next move
5. Open the retrieved evidence and verification state.
6. Convert the next move into a persisted Plan.
7. Save one explicit Decision and one Reference.
8. Approve only the Decision as a Capsule source, leave the Reference
   withheld, choose the representation (full, owner-approved summary, or
   metadata only), and create a named recipient grant with a capability and
   optional expiry. In this beta the selection itself is owner-API-level
   (the demo seed provides a ready capsule; the React share sheet was
   retired with the frontend rebuild), and the browser lifecycle proof
   (`apps/web/e2e/capsule.spec.ts`) exercises it end to end.
9. Open the owner capsule room (`/capsule/<id>`) to show the lifecycle
   state, the access audit, and the live **Revoke now** control.

### Recipient flow

1. Sign in as the invited recipient.
2. Open the Context Capsule room.
3. See the capsule purpose, active state, capability, expiry, safety statement, included source, and withheld-source summary.
4. Ask a scoped question.
5. See an answer with an explicit answer mode and source references.

### Revocation flow

1. Return to the owner account.
2. Revoke the capsule.
3. Refresh the recipient room.
4. Show the distinct **REVOKED** state and the disappearance of the question interface.

## OpenAI use

NUR uses the OpenAI Responses API on the server only.

- The API key never enters browser code, screenshots, source packages, or logs.
- The model must return the `NURTalkOutput` structured schema.
- Model output is persisted with provider, model-run, evidence, verification, and usage metadata.
- Authentication or provider errors fail closed rather than generating fake AI text.
- Disabled-provider mode is explicit and never impersonates a successful model response.

## Architecture

```text
V197-inspired React interface
        |
        v
FastAPI owner-scoped API
        |
        +--> Postgres + forced RLS
        +--> Redis / worker / scheduler
        +--> lexical owner-memory retrieval
        +--> OpenAI Responses API
        +--> structured output verifier
        +--> model-run and evidence ledger
        |
        v
Context Capsule source snapshot
        |
        +--> recipient grant
        +--> representation boundary
        +--> audit trail
        +--> immediate revoke / expiry
```

## Truth-locked claims

The demo may claim only what the current runtime proves.

### Proven and demoable

- server-side OpenAI Responses API integration;
- structured model output validation;
- persisted model runs and Talk threads;
- owner-scoped lexical retrieval;
- source-reference verification;
- corrections, decisions, references, plans, and outcomes;
- named recipient Context Capsule grants;
- full / owner-approved summary / metadata-only representations;
- explicit included and withheld context;
- capsule audit events;
- immediate revoke and distinct expired/revoked states;
- secret-safe packaging and local boot scripts.

### Do not claim without new runtime evidence

- AGI, sentience, consciousness, soul, or autonomous selfhood;
- autonomous external action;
- vector retrieval when embeddings are not populated;
- web research when external research remains disabled;
- recipient-side model inference if the current answer path is operating in deterministic extractive mode;
- production authorization certification;
- successful tests that have not been run on the exact submission commit.

## Submission repository policy

- Canonical source repository: `am-selenephos/NUR`.
- Competition work happens on `build-week-submission` until verified.
- `NUR-public` is a release mirror, not a second project.
- AM internal doctrine, private operating memory, secrets, local databases, logs, screenshots, and generated proof artifacts are excluded.
- No merge to `main` until static gates, runtime gates, secret scan, and the complete demo path pass on the exact head commit.

## Final acceptance gates

A submission candidate is green only when all of the following are true:

1. V197 integrity check passes.
2. API tests pass.
3. Web typecheck, unit tests, and production build pass.
4. Talk and Capsule browser tests pass without force-click workarounds.
5. OpenAI health, structured output, persistence, and source-reference smoke pass.
6. Owner → recipient → revoke lifecycle passes on two accounts.
7. Secret scan passes on source and packaged artifact.
8. Demo video is recorded from the same verified commit.
9. README and submission copy contain no unproved claims.

## Demo closing line

> NUR does not ask people to choose between useful AI and control over their context. It makes reasoning, memory, sharing, and revocation separate, inspectable decisions.
