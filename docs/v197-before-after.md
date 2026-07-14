# V197 Runtime Before And After

Date: 2026-07-13

This delta preserves the canonical V197 face and removes work that was visually redundant at rendered size.

| Contract | Before | After |
| --- | --- | --- |
| Canonical source | SHA `252eee...33c3` | same SHA, unchanged bytes |
| Presentation owner | V197 document | V197 document |
| Entry cadence | 4.66 FPS | 76.81 FPS headed reference |
| Map cadence | 7.34 FPS | 77.02 FPS headed reference |
| Locked mobile Map | below usable target | 102.27 FPS headed reference |
| Map DOM | about 6,212 elements | 1,473 elements |
| Tiny star implementation | full 100px MasterStar per icon | canonical host plus one lightweight prism node |
| Tiny star rays | 1,296+ | 0 |
| Full master star | present | preserved, 12 rays |
| Map animations | about 2,777 | 4 to 5 |
| Canvas count | 1 | 1 |
| Centring | collision-prone historical state | 0.00 to 0.01px delta, zero collisions |
| Reduced motion | residual engine work | canvas hidden, no meaningful computed-duration animation |
| 10-minute growth | unproven | zero DOM/canvas/style/listener/observer/heap growth |

Screenshots:

- Before: `proof/v5/performance/baseline/systems-map.png`
- After desktop: `proof/v5/performance/g04-acceptance/chromium-desktop-g04/systems-map.png`
- After mobile: `proof/v5/performance/g04-acceptance/chromium-mobile-g04/systems-map.png`
- Real WebKit mobile: `proof/v5/performance/g04-acceptance/webkit-mobile-g04/systems-map.png`

The approved founder signup/logo concept remains a separate visual checkpoint. The runtime repair does not silently promote that preview into production.
