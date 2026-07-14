# AM Projects Product Specification

Date: 2026-07-11  
Founder requirement: AM Projects is a first-class operating system for real work, not a decorative project card.

## Track A state

No AM Projects visual or project-agent claim is live. Existing Orbits, Plans, Outcomes, references, evidence provenance, cognition events, worker/Redis, Omega review, and owner RLS are reusable primitives. They must be extended, not duplicated.

## Track B domain

| Domain | Records/capability |
|---|---|
| project | objective, owner, Orbit, state, deadline, budget, permissions |
| work graph | milestones, tasks, dependencies, blockers, acceptance gates |
| agents | role, model/tool policy, run state, budget, approval requirement |
| artifacts | source, generated file, version, checksum, provenance, review state |
| evidence | commands, tests, screenshots, citations, runtime proof |
| decisions | proposal, alternatives, owner approval/rejection/correction |
| delivery | package, checksum, manifest, exclusions, runbook, final verdict |

## Execution law

`objective -> bounded plan -> owner/tool permission -> run -> artifact/evidence -> verifier -> owner review -> next move`. Agents cannot weaken auth/RLS, reveal secrets, spend money, publish, message, deploy, or take external action without an explicit permission gate. No chain-of-thought is stored; store concise rationale, inputs, outputs, tool receipts, and verification.

## NUR integration

- Today shows the next approved move and blocker;
- Talk can discuss project evidence and propose actions;
- Journal can capture a private decision/reference;
- Plan can receive an approved task;
- Systems/Map show Projects as Orbits, not generic cards;
- Timeline records runs, decisions, outcomes, corrections, and packages;
- Omega can propose learning from project evidence but cannot auto-change policy;
- Glow rewards verified returns, not agent token consumption.

## Acceptance

Owner-only project RLS, tool permission denial, cancellation, retries/idempotency, budget cap, artifact checksum, secret redaction, malicious artifact handling, verifier failure, human approval, package reproduction, worker restart recovery, and full Project-to-deliverable E2E are mandatory.
