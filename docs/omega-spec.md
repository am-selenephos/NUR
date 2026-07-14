# NUR-Omega Specification

Date: 2026-07-11

## Existing backend

The repo contains owner-scoped tables/services/routes for experiences, claims, evidence edges, contradictions, workspace frames, predictions, learning proposals, consolidation runs, and review queue. Scheduler/beat is included in one-file boot. APIs include dashboard, scheduler status, consolidation, claim evidence/why-changed, review actions, and export.

Safety law prevents learning proposals from modifying authentication, RLS, secrets, or other forbidden policy. Model-generated sensitive claims require confirmation. Capsule retrieval is isolated from owner Omega memory.

## Visual state

Omega is not a Track A visible route. Phase 1 authority forbids a React reconstruction; `/universe/omega*` returns an explicit V197-native-adjunct 404. The approved adjunct contract is recorded at `docs/v197-adjuncts/omega-contract.md`, but its document has not been built.

## Required V197-native adjunct

- dashboard: changed claims, open contradictions, unresolved predictions, proposals, scheduler status;
- review: sensitive inferred claim queue with approve/reject/edit;
- why changed: prior/new state, evidence/counterevidence, consolidation run, uncertainty;
- export: owner-only bounded JSON download;
- empty/error states in V197 black-holographic visual law.

## Boundaries

Owner only; no Capsule recipient, Community member, or Group member can query Personal Omega. No chain-of-thought. No autonomous policy mutation. Consolidation is replayable, locked, auditable, and proposal-first.

## Acceptance

Forced RLS and recipient denial, 100+ experience replay, messy fixture evaluation, contradiction/prediction resolution, consolidation lock, proposal governance, scheduler health, Capsule isolation, export redaction, WebKit/mobile adjunct screenshots, and no React visual ownership are required before enabling the route.
