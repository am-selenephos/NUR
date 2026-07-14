# Context Capsule Specification

Date: 2026-07-11

## Existing backend

The Capsule domain already supports owner creation, source selection, recipient grants, read-only/scoped-question capabilities, expiry, recipient view, scoped questions, audit, revoke, and collaboration outcome. PostgreSQL RLS and service checks keep recipient access inside explicit grants. Revoked/expired asks fail closed and race tests cover ask/revoke behavior.

## Retrieval law

The answer service receives only included Capsule sources. Owner Talk, Journal, Timeline, Omega, general memory, and excluded Orbit sources are not retrieval candidates. Cache keys/state must include Capsule/grant version and active state; revoke invalidates answerability immediately.

## Visual state

No Track A Capsule UI is claimed. `/capsule/:id` returns the explicit V197-native-adjunct 404 because Phase 1 forbids a React replacement. The approved design contract remains in `docs/v197-adjuncts/capsule-contract.md`.

## V197-native owner surface

Purpose, recipient, capability, expiry, included/excluded source controls, capture-decision/reference section, create/copy/revoke actions, existing Capsule list, and audit. Controls must use native V197 styling with no white browser controls.

## V197-native recipient room

Purpose and boundary, included/excluded summary, scoped question composer, source-bound answer, active/revoked/expired state, and no owner-navigation leakage.

## Acceptance

Owner create -> recipient view -> included answer -> excluded denial -> owner revoke -> recipient blocked, plus cross-user API denial, expiry, 25+ revoke/ask races, no cached post-revoke answer, RLS proof, mobile/RTL/WebKit screenshots, and no visible React root.
