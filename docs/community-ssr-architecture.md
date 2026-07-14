# Community SSR Architecture

Date: 2026-07-11  
Founder source: Ultimate Master sections 15-17 and Track B sequence.

## Track A truth

V197 contains Community-shaped presentation, but `v197Hydration.ts` removes fabricated people/reply/feed data and disables Community controls with an honest Track B state. The existing `community_consultation_notes` table is an owner-private staging surface, not a social network.

## Track B service boundary

- public/discoverable SSR pages render only records explicitly published to Community;
- private owner memory, Talk, Journal, Omega, Capsule sources, and Group memory are separate domains and never become post context implicitly;
- posts, nested comments, reactions, follows, rooms, moderation cases, reports, blocks, reputation, translation records, and notification preferences have explicit owner/visibility columns;
- ranking runs as a read service over publishable metadata and bounded embeddings, not raw private context;
- locale-specific canonical URLs and metadata support all 35 locale slots without pretending draft translations are reviewed.

## Ranking contract

Candidate generation uses membership/visibility, language, follows, topic/system affinity, recency, and quality signals. Ranking may combine predicted useful return, diversity, freshness, relationship, and moderation confidence. It must cap repetition, expose `why shown`, allow chronological mode, and exclude rage/harassment amplification signals.

## Moderation and privacy

- author can edit/delete and see moderation state;
- blocks apply before candidate generation;
- reports create immutable audit events;
- group-only content cannot leak into public SSR caches;
- cache keys include visibility, locale, and viewer cohort;
- raw private text is excluded from analytics and recommender training by default.

## Required proof

RLS/membership tests, SSR locale snapshots, post/comment persistence, moderation flows, block/filter behavior, ranking determinism, no private-source ingestion, cache isolation, translation provenance, abuse rate limits, WebKit/mobile screenshots, and notification opt-out. No Community claim is live in Track A.
