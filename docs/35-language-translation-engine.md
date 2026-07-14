# 35-Language Translation Engine

Date: 2026-07-11  
Implementation roots: `apps/web/src/lib/i18n.ts`, `bridge/v197I18n.ts`, `/api/v1/profile/preferences`, `/api/v1/translations`, and migration 0011.

## Catalog contract

Exactly 35 locale slots are registered: `en, ur, hi, bn, pa, ar, fa, tr, id, ms, zh-Hans, zh-Hant, ja, ko, vi, th, fil, ta, te, mr, gu, kn, ml, ru, uk, pl, de, fr, es, pt, it, nl, sv, ro, sw`.

Current `polished_beta` metadata is `en, ur, hi, fa, ar, es, fr, zh-Hans`; every other slot is visibly `draft_unreviewed`. Korean is present as `ko` with native label `한국어` and Hangul navigation copy, but remains draft in this Track A checkpoint. It is not falsely marked human-reviewed.

## Track A bridge

- the existing V197 scope chamber receives a native-styled language and writing selector;
- preference persists owner-only and survives refresh;
- known navigation/copy slots mutate without rebuilding V197 geometry;
- `ur/ar/fa` are RTL; `locale=ur + writing_preference=roman` forces LTR;
- Talk sends `locale` and `writing_preference` to the server-side intelligence kernel;
- provider prompts explicitly require Roman Urdu for the Roman preference;
- translation rows persist source/target locale, source kind/id, text, provider, quality, and review status under owner RLS.

## Track B completion

- namespace catalogs for every critical V197 string and each adjunct surface;
- reviewed core copy and terminology governance;
- dynamic content translation with hash cache, invalidation, provenance, and edit history;
- Group NUR per-member translation while retaining canonical source text;
- localized SSR Community pages/metadata;
- notification templates, speech style, voice input/output, and locale-specific moderation;
- plural, number, date, collation, line-breaking, font fallback, and long-copy layout QA.

## Truth and safety

Machine translation must be labelled, source text remains available, corrections do not rewrite another user's original, and private text is sent only to an explicitly configured server-side provider. Translation records never widen source visibility.

## Acceptance

Track A E2E proves Korean selection, Roman Urdu direction, preference refresh, and selected-language Talk metadata. Track B requires coverage reports, RTL/mobile/WebKit screenshots, Chinese variants, Indic scripts, Korean speech-style tests, long German, translation cache isolation, and recipient/group boundary tests.
