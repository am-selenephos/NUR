# Analytics and Experiment Plan

Date: 2026-07-11

## Current state

FastAPI exposes aggregate operational counters through `/metrics` and request correlation IDs through structured logs. There is no claim of a production product-analytics pipeline or live retention dashboard in Track A.

## Event envelope

Allowed fields: random event ID, owner pseudonymous ID, session ID, surface, action class, outcome state, experiment/variant, locale, writing mode, latency bucket, provider status, and coarse device class. Forbidden fields: raw Talk/Journal/Plan/Capsule/Group text, API keys, source excerpts, email, model prompts, and generated private responses.

## Funnel

`landing -> account -> first check-in -> first Talk -> first Journal/Plan -> first Outcome -> first verified Glow -> day-2/day-7 return`. Integrity metrics include duplicate-reward denial, disabled-provider honesty, failed writes, RLS denials, and notification opt-outs.

## Experiment candidates

- reward timing after persisted outcome;
- Today re-entry copy;
- quest mix and streak rescue;
- lens navigation density;
- selected-language onboarding;
- notification timing/frequency;
- Group NUR intervention frequency;
- pricing/upgrade framing.

## Governance

Assignment is server-side, stable, versioned, and auditable. Pre-register primary metric, guardrail, sample window, stopping rule, and excluded cohorts. Required guardrails include distress/complaint signals, opt-outs, deletion, excessive session length, privacy errors, and reward abuse. No dark-pattern test may remove consent or make account/data exit harder.

## Acceptance

Schema validation, content-redaction tests, deterministic assignment, exposure dedupe, deletion/retention, locale segmentation, metric reproducibility, and experiment rollback are required before product decisions rely on these events.
