# Research, Web Signals, Expert Voice, and Tender Insights

Date: 2026-07-11

## Track A implementation

`research_briefs`, `research_source_notes`, `web_signal_questions`, `web_signal_notes`, and `provider_capabilities` exist with owner scoping/RLS. The V197 Research field can persist a local question through `/api/v1/research/briefs`. When no provider is connected, it says so and invents no sources. Community/Web cards do not display fake live data.

## Track B pipeline

1. owner stages a bounded question and chooses an Orbit;
2. capability service declares which connectors are available and their data terms;
3. retrieval adapter fetches at a rate/budget limit;
4. normalizer stores URL, publisher, retrieved time, locale, content hash, and excerpt;
5. source-quality and duplicate checks run;
6. NUR creates claims with citation edges and uncertainty;
7. owner can save source note, counterpoint, reference, or open question;
8. Timeline receives owner-scoped provenance events.

## Expert Voice

Experts are verified identities or owner-added sources. NUR never fabricates a quotation, credential, availability, endorsement, or recording. Contributions retain identity, consent, locale, timestamp, and source link.

## Tender Insights

Tender mode compares a decision against evidence, constraints, dissent, cost, and risk. Output is `Observed / Inferred / Hypothesis / Unknown / Next verification`, not certainty theatre. High-impact recommendations require owner confirmation and can open a Plan but cannot act externally.

## Required proof

Connector allowlist, SSRF protection, robots/terms handling, budgets/timeouts, citation verifier, content-hash dedupe, source deletion, owner RLS, recipient denial, translation provenance, model malformed-output tests, and E2E from staged question to saved cited reference. Live web remains unclaimed until these pass.
