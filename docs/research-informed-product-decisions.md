# Research-Informed Product Decisions

Date: 2026-07-13

This file separates founder requirements from researcher suggestions. Research
does not silently replace founder intent, and a cited mechanism is not evidence
that every implementation of it is beneficial.

## Founder requirements that remain controlling

- Glow Points, streaks, quests, levels, variable rewards, social loops and
  persuasive retention are founder requirements in
  `NUR_ULTIMATE_FOUNDER_MASTER_PROMPT_SOL_ULTRA.md` sections 12-15.
- V197 remains the presentation law; React does not visually reconstruct it.
- Privacy boundaries, truthful activity, owner control and no fabricated human
  messages remain hard exclusions.

## Decisions supported by external evidence

1. **Collective intelligence needs interaction design, not merely smart
   individuals.** Woolley et al. found group performance was associated with a
   collective-intelligence factor and social sensitivity/equal conversational
   turn-taking. NUR therefore preserves minority positions and bounded
   contributions in Group NUR and Consultation instead of reducing discussion
   to a popularity count. Source: [Science/PubMed](https://pubmed.ncbi.nlm.nih.gov/20929725/).

2. **Variable schedules can sustain responding, so rewards must be auditable
   and bounded.** Experimental work demonstrates persistent behavior under
   variable-interval schedules. NUR may use variable rewards as requested, but
   eligibility, odds, caps, provenance and reversals belong on the server; paid
   chance mechanics and fabricated scarcity remain excluded. Source:
   [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC1333500/).

3. **Community retention is relationship-specific.** Research on community
   loyalty motivates relationship strength, reply return and meaningful
   contribution as ranking signals rather than raw clicks alone. NUR does not
   fabricate activity to create an empty-network illusion. Source:
   [Stanford NLP](https://web.stanford.edu/~jurafsky/pubs/paper-loyalty.pdf).

4. **Offline behavior is a security boundary, not only a visual feature.** The
   service worker controls requests within its scope and has a lifecycle that
   must be tested. NUR therefore caches only an explicit shell, excludes
   `/api/`, and treats safe draft queuing as future work rather than claiming
   offline data mutation. Source: [W3C Service Workers](https://www.w3.org/TR/service-workers/).

5. **Notification permission and purpose must remain understandable.** NUR's
   current notification slice is owner-written and in-app only. Push remains
   unclaimed until permission, quiet hours and delivery receipts are real.
   Sources: [W3C Permissions](https://www.w3.org/TR/permissions/) and
   [W3C Privacy Principles](https://www.w3.org/TR/privacy-principles/).

6. **RLS must be enforced even when table owners normally bypass it.** Every
   new owner-scoped table uses `ENABLE ROW LEVEL SECURITY` plus
   `FORCE ROW LEVEL SECURITY`, with recipient/cross-owner denial tests. Source:
   [PostgreSQL row security](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).

7. **RTL is a text algorithm plus layout concern.** Locale direction, writing
   preference and bidi isolation must be explicit; the NUR wordmark and galaxy
   are not mirrored. Source: [Unicode Bidirectional Algorithm](https://www.unicode.org/reports/tr9/).

8. **Model structure is a verification contract.** Talk uses server-side
   schema-validated output and validates source references before persistence;
   structured output does not make an unsupported claim true. Source:
   [OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/).

## Proposed, not yet implemented

- Server-audited variable-reward eligibility and reversal policy.
- Feed ranking evaluation against long-term meaningful return, not time-on-app.
- Opt-in push delivery with per-category quiet hours and recovery-safe caps.
- Production multilingual translation provider evaluation and human review
  workflow.

These are researcher suggestions constrained by the founder prompt. They must
not be labelled existing implementation until persistence, permission tests and
rendered proof exist.
