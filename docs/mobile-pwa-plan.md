# Mobile and PWA Plan

Date: 2026-07-11

## Track A browser state

The exact V197 runtime remains the presentation on mobile. `v197Polish.ts` adds bridge-scoped mobile geometry: two-row command bar, horizontally safe top lenses, named mobile tabs, unclipped Deep research control, and first-viewport map containment. Chromium mobile and real Playwright WebKit tests run against the same canonical host.

Known WebKit evidence includes a canonical top-left compositing strip inherited from V197; disabling its backdrop filter caused a black paint regression and was rejected. It is documented rather than hidden.

## Track B PWA

- manifest with NUR identity, icons, theme/background, standalone display;
- service worker for immutable shell/font/static assets only;
- authenticated/private API responses are network-first and never placed in shared cache;
- offline shell clearly says data/AI is unavailable and queues no sensitive write silently;
- update prompt and cache migration are explicit;
- install and notification prompts follow user intent.

## Native companion boundary

A future native shell may provide secure keychain session storage, voice, notifications, camera/file intake, and background delivery. It must not fork V197 visual law or bypass server RLS/provider boundaries.

## Acceptance

393px and representative tablet/desktop no-overflow checks, touch targets, keyboard/IME, safe-area insets, RTL, reduced motion, WebKit screenshots, service-worker install/update/offline behavior, cache inspection proving no private response storage, Lighthouse/accessibility budget, and notification consent tests.
