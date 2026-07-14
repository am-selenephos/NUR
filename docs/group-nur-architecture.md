# Group NUR Architecture

Date: 2026-07-11

## Product boundary

Group NUR is a deliberate shared context system, not an automatic merge of Personal Orbits. A person joins a group, chooses what enters it, and can inspect the provenance of every group memory. Personal Talk, Journal, Omega, and unshared Orbit data remain unreachable.

## Track B domains

| Domain | Core records | Boundary |
|---|---|---|
| group identity | groups, memberships, roles, invitations | membership + role RLS |
| shared memory | group sources, claims, decisions, corrections | explicit contribution only |
| group Talk | threads, turns, model runs, citations | group-approved sources only |
| translation | source text, target locale, review/provenance | member-visible content only |
| coordination | quests, plans, outcomes, consultation returns | role and assignment scoped |
| governance | moderation, consent, export, removal audit | admin action never rewrites origin history |

## Intelligence path

`group event -> permission filter -> evidence retrieval -> multilingual context frame -> structured provider response -> source verifier -> persisted group response`. Group NUR may summarize disagreement and unresolved questions; it may not infer or expose a member's private memory.

## Roles

Owner/admin manage membership and policy; facilitator can open consultation/quests; member contributes and corrects; observer reads approved material. Every privilege is server-checked. Removing a member invalidates sessions/grants and re-evaluates cached group answers.

## Track A state

No Group NUR visual or backend claim is live. Community/Consultation controls are honestly disabled. Existing Capsule grants are the tested bounded-sharing primitive to reuse when Group NUR is built.

## Acceptance

Two-group and cross-user RLS tests, invite/revoke races, source inclusion/exclusion, role escalation denial, multilingual turn integrity, member deletion, export, audit, and model citation verification are mandatory.
