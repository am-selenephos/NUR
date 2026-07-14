# Missing Backend Build Map

Date: 2026-07-13

## P0 gaps closed in Track A

- server-owned Glow rules, balance, transactions, streak row, reward events;
- idempotent source/action rewards;
- founder-seven provisioning for new accounts and demo seed;
- translation record foundation with owner RLS;
- V197 write bridge for Auth, Talk, Journal, Plan, Outcome, Research, preferences;
- owner snapshot hydration for Systems and primary lenses.

## Track B backend/product gaps

| Gap | Required build | Dependency/gate |
|---|---|---|
| Full quest/level economy | quest definitions, progress ledger, level rules, anti-abuse, repair economy | outcome integrity and reward analytics |
| Public Community SSR | public/private page split, follows/saves, ranking, reports and moderation operations | abuse controls and explicit publication scope |
| Group NUR depth | translated room summaries, sparse interventions, richer decision/tension maps | explicit consent and per-room context policy |
| Consultation depth | scheduling, verified Expert Voice and optional payment hooks | moderation and commercial policy |
| Live Research/Web | provider connectors, source ingestion, citation verifier, budgets | external-provider consent and provenance |
| AM Projects depth | file storage, deliverable workflow, collaborator grants and approved execution adapters | owner control and tool permission model |
| Full translation | locale catalogs, review workflow, dynamic translation provider, cache/invalidation | human review for polished locales |
| Notification delivery | scheduler plus opt-in push/email adapters, deep links and delivery receipts | permission prompts, quiet hours and harm-aware caps |
| PWA proof depth | install/offline/update matrix and safe queued drafts | browser/device test matrix |
| Production scaling | queue partitioning, backups, dashboards, SLOs, deployment hardening | environment-specific operations |

The V197 interface labels external Community feeds, live web research, push delivery and unimplemented Project execution adapters honestly; no missing Track B module is presented as live.
