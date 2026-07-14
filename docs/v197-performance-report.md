# V197 Performance And Runtime Report

Date: 2026-07-13

Status: `G04_RUNTIME_PASS`, pending the mandatory post-bridge auth regression.

## Source And Presentation Law

- Canonical V197 SHA-256: `252eee806ece31ef829a2dc5cd45aa8d8f8e855db1bde98b6f87193d786633c3`.
- Canonical source bytes were not edited.
- The V197 document remains the visible presentation owner. React does not render the interface.
- The performance profile is a deterministic `srcdoc` runtime transform which fails closed to canonical source if a known signature drifts.
- Full `#iSpark` MasterStar, Bodoni/Crimson typography, galaxy canvas, holographic wordmark, geometry, and one persistent canvas are preserved.

## Measured Root Cause

The baseline was not blocked on memory or GPU capacity. It was dominated by avoidable presentation work:

| Metric | Baseline |
| --- | ---: |
| Entry cadence | 4.66 FPS |
| Map cadence | 7.34 FPS |
| Entry particles | 2,256 |
| Map visible CSS animations | about 2,777 |
| Map DOM elements | about 6,212 |
| Full star modules used as tiny icons | 108+ |
| Rays created by tiny icons | 1,296+ |

Each tiny icon expanded into a complete 100px MasterStar subtree. The Map also created more full modules lazily after route hydration.

## Applied Repair

- Deterministic Entry/Universe canvas quality profile lowers DPR and expensive particle/path work while preserving the visual field.
- Every `.nur-exact-mini-host` keeps its canonical host geometry but replaces imperceptible full MasterStar internals with one lightweight prism node.
- Lazy Map nodes are compacted immediately and once more on the next frame after hydration.
- Expensive mini-star blur, ray, pseudo-element, and transition work is removed.
- Normal-mode full MasterStar and wordmark animations remain.
- Reduced-motion mode hides the galaxy canvas and collapses residual animations/transitions to zero practical duration.
- Hidden-document canvas scheduling remains paused by the canonical visibility gate.

## Named Reference Results

GPU-backed headed Chromium, 1600x900:

| Surface | FPS | p95 frame delta |
| --- | ---: | ---: |
| Entry | 76.81 | 16.7 ms |
| Today | 90.86 | 20.9 ms |
| Map | 77.02 | 25.0 ms |

Locked mobile viewport, 393x852:

| Surface | FPS | p95 frame delta |
| --- | ---: | ---: |
| Entry | 90.26 | 12.6 ms |
| Today | 113.72 | 20.8 ms |
| Map | 102.27 | 20.8 ms |

The display can refresh above 60Hz, so cadence may exceed 60. Acceptance is based on meeting the minimum, not capping the browser.

Runtime after Map hydration:

- 1,473 elements.
- one canvas.
- 111 of 111 mini-star hosts compacted.
- zero mini-star rays.
- full `#iSpark` retains its 12 rays.
- 4 to 5 active visual animations.
- 165 steady-state canvas particles.
- critical interactions: 16.0 to 52.6ms.
- contractual centring delta: 0.00 to 0.01px.
- zero critical label collisions.
- zero horizontal overflow.
- no recurring warm-idle long task in the valid headed reference samples.

Evidence:

- `proof/v5/performance/g04-acceptance/chromium-desktop-g04/acceptance.json`
- `proof/v5/performance/g04-acceptance/chromium-mobile-g04/acceptance.json`
- `proof/v5/performance/g04-acceptance/chromium-desktop-g04/systems-map.png`
- `proof/v5/performance/g04-acceptance/chromium-mobile-g04/systems-map.png`

## Cross-Engine And Reduced Motion

- Firefox desktop: warm runtime and reduced-motion tests pass.
- Real Playwright WebKit in `mcr.microsoft.com/playwright:v1.61.1-jammy`: mobile runtime and reduced-motion tests pass.
- WebKit was not substituted with Chromium.
- WebKit retains stale source duration in `getComputedTiming()` after a CSS override; the proof records both that metadata and the actual computed effective duration (`0.001ms`).
- Canvas display is `none` under reduced motion, and no animation with computed effective duration above 16ms remains.

Evidence:

- `proof/v5/performance/g04-acceptance/firefox-desktop-g04/acceptance.json`
- `proof/v5/performance/g04-acceptance/firefox-desktop-g04/reduced-motion.json`
- `proof/v5/performance/g04-acceptance/webkit-mobile-g04/acceptance.json`
- `proof/v5/performance/g04-acceptance/webkit-mobile-g04/reduced-motion.json`

## Ten-Minute Soak

The explicit 600,000ms soak passed:

| Resource | Start | End | Growth |
| --- | ---: | ---: | ---: |
| DOM elements | 1,473 | 1,473 | 0 |
| Canvas elements | 1 | 1 | 0 |
| Style elements | 33 | 33 | 0 |
| Running animations | 5 | 5 | 0 |
| Listener balance | 154 | 154 | 0 |
| Mutation observers | 1 | 1 | 0 |
| Resize observers | 0 | 0 | 0 |
| Reported heap | 10,000,000 | 10,000,000 | 0 |

All 21 samples remained structurally constant. Evidence: `proof/v5/performance/g04-acceptance/chromium-desktop-g04/ten-minute-soak.json`.

## Test Environment Notes

- Headless browsers throttle compositor/rAF cadence and are not used as FPS proof.
- An Xvfb wrapper in the official image failed to launch its child command and was terminated; it was not counted as product evidence.
- One host sample ran while an existing personal Chromium session consumed roughly half of the shared Intel GPU and failed the FPS threshold. A fresh GPU-backed headed run passed all hard thresholds. Both conditions are recorded; no threshold or timeout was weakened.
- Browser matrix timing assertions are hard on the headed Chromium reference. Firefox/WebKit prove engine parity, routing, geometry, controls, and reduced work.

## Verification

- `npm run typecheck`: pass.
- focused Vitest: 11/11 pass.
- production build: pass, `189.85 kB`, `52.90 kB` gzip.
- Chromium desktop hard FPS gate: pass.
- Chromium mobile hard FPS gate: pass.
- Firefox matrix: 2 passed, soak test separately skipped by design.
- real WebKit matrix: 2 passed, soak test separately skipped by design.
- ten-minute Chromium soak: pass.

