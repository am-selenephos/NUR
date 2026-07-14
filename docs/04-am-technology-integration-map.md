# AM Technology Integration Map

## Source discipline

This pass reuses the curated `/home/nur/AM_FULL_MACHINE_REVIEW/AM_CORE_REVIEW_PACK_V1` instead of rescanning the machine. The pack identifies 4,997 preserved raw sources and names `MADDY_HUNT/AM_LIQUID_CORE/am_liquid_core.py` as the canonical AM Liquid candidate. Candidate classification is evidence, not permission to import an entire experimental runtime into NUR.

## Concepts to reuse

| AM lineage concept | NUR integration | Existing NUR primitive |
|---|---|---|
| chronology ledger | Timeline event stream with provenance | cognition/audit/Timeline |
| state snapshots | Today and live Universe aggregates | owner snapshot bridge |
| memory vault | owner-scoped event/source retrieval | memory service, Orbits, Capsule |
| task transition graph | Project/Plan task states and future Timeline | Plans/steps/outcomes |
| evidence graph | Insights/Omega/Project evidence | claims/evidence edges |
| planner/verifier split | proposal then schema/source/permission verifier | intelligence kernel/verifier |
| outcome ledger | real-world return and correction | Outcomes/Glow/Omega |
| orchestration | bounded worker jobs with owner approval | Celery/Redis/Omega scheduler |
| review loop | owner approve/reject/correct | Omega review/corrections |
| project cockpit | AM Projects native chamber | Orbit + Plan + artifacts |

## What is not imported

- broken/duplicate AM Liquid variants;
- claims of sentience, soul, consciousness, or unrestricted autonomy;
- self-modifying security policy;
- arbitrary machine access or secret ingestion;
- model weights, caches, datasets, browser profiles, or vendor trees;
- raw personal corpus in product packages.

AM Projects will use NUR's tested Auth/RLS/provider/worker boundaries and only adopt the useful architecture patterns above.
