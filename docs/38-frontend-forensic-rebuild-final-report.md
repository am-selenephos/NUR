# NUR Frontend Forensic Rebuild Final Report

Generated: 2026-07-16

Scope: `apps/web` presentation, bridge, geometry, lifecycle, and frontend tests.

Acceptance status: implementation and static verification are complete. Final
browser acceptance is pending because this execution sandbox rejects every
localhost bind with `listen EPERM`; therefore E2E execution and post-rebuild
screenshots are not claimed as passed.

## 1. Current HEAD And Working Branch

- Working branch: `frontend/nur-forensic-rebuild`
- Recorded implementation HEAD before this report-only commit: `af6873c`
- Starting branch: `main`
- Working copy: `/home/nur/Downloads/AM -Clean/NUR_FORENSIC_REBUILD`
- Remote: `https://github.com/am-selenephos/NUR.git`
- Phase commits were kept coherent from audit through final legacy-control
  cleanup.

The source workspace contained substantial unrelated dirty work before this
rebuild. That work remains in the worktree and was not included in the rebuild
commits.

## 2. Executive Summary

The active frontend is the canonical V197 host composed through Vite and bridge
modules, not the dormant React route tree. The rebuild therefore changed the
actual runtime presentation layer: the late broad CSS skin was dismantled,
semantic materials and controls were installed, an authentic reusable star
seal replaced fake mini-stars, responsive shell and map geometry were rebuilt,
all Universe lenses and adjunct surfaces were brought into the same system,
and the exact star-brain gained lifecycle ownership without changing its
protected source bytes.

The committed delta contains 30 files, 4,720 insertions, and 894 deletions
before this report. It contains no backend file.

## 3. Full Frontend Audit Summary

The Phase 1 audit is recorded in
`docs/37-frontend-forensic-rebuild-audit.md`. It traces Vite direct-host
composition, canonical Entry and Universe frames, bridge ownership, hydration,
polish, star-brain mounting, performance profiling, adjunct mounting, and final
cascade ownership.

The audited route inventory covers Entry, auth and onboarding; Today, Talk,
Journal, Plan, Systems, Universe and Life; Map, Orbits, Timeline, Insights,
Research, Community and Web Signals; Settings, Capsule, Consultations,
Projects, Glow, Notifications and Omega. Shared auth, navigation, rail,
composer, search, menu, modal, language, empty, error, loading, disabled,
focus, reduced-motion, RTL and long-label states are included in the audit and
test contracts.

Confirmed root causes were one broad dotted-control selector, competing glass
rules, fixed Systems dimensions and offsets, duplicate stellar dialects, fake
mini-star replacement, artificial frame delays, missing runtime cleanup, and a
separate embedded adjunct visual system.

## 4. Files Changed

Runtime and behavior integration:

- `apps/web/src/bridge/v197Accessibility.ts`
- `apps/web/src/bridge/v197Adjuncts.ts`
- `apps/web/src/bridge/v197Bindings.ts`
- `apps/web/src/bridge/v197Bridge.ts`
- `apps/web/src/bridge/v197PerformanceProfile.ts`
- `apps/web/src/bridge/v197Polish.ts`
- `apps/web/src/bridge/v197StarBrain.ts`
- `apps/web/src/bridge/v43StarBrainRuntime.js`
- `apps/web/src/bridge/v197StarSeal.ts`
- `apps/web/src/main.tsx`
- `apps/web/src/routes/universe/UniverseLenses.tsx`

Presentation:

- `apps/web/src/styles/v197-cosmic-skin.css`
- `apps/web/src/styles/v197-star-seal.css`
- `apps/web/src/styles/v197-lenses-forensic.css`
- `apps/web/src/styles/v197-adjunct-forensic.css`

Tests and evidence:

- Seven new or expanded Playwright geometry, route, adjunct, lifecycle and
  responsive specifications under `apps/web/e2e`
- Seven focused unit/static contract files under `apps/web/src/v197`
- `docs/37-frontend-forensic-rebuild-audit.md`
- This final report

## 5. Broad CSS Rules Removed

- Removed the late blanket rule that treated nearly every V197 button as the
  same dotted, rounded, glowing control.
- Replaced broad panel and button material ownership with scoped classes for
  primary, secondary, navigation, icon, chip, input, selected and destructive
  roles.
- Localized unavoidable canonical-host overrides to the final V197 layers.
- Removed final owner-menu, auth-wait and mobile-tab remnants that still used
  legacy glass or near-maximum z-index values.
- A final source sweep found no rejected old brown/purple fills, nuclear
  z-index signatures, tiled star-dot sizing or fake radial-dot signatures in
  the active rebuild files.

## 6. Fake Star Techniques Removed

- Removed repeating radial-gradient dots from control backgrounds.
- Disabled the whole-interface fake CSS sparkfield.
- Removed the simplified polygon/radial-gradient mini-star outcome.
- Prevented legacy MasterStar fragments from remaining as control icons.
- Restricted the product to three stellar roles: background galaxy, exact
  star-brain particles, and reusable NUR star seals/glints.

No generic star text glyph is used as the canonical seal.

## 7. Real NUR Star-Seal Implementation

`v197StarSeal.ts` creates one reusable inline SVG sprite and symbol. Its anatomy
contains a pearl crystalline core, four primary rays, secondary shards, gold
energy, pink and cyan refraction, a violet edge and a controlled halo.

The primitive supports 12, 16, 20, 24 and 32 pixel sizes. It is static by
default, uses a single lightweight twinkle only for selected or emphasized
states, and respects reduced motion. Existing mini-host dimensions, data
contracts and ARIA behavior remain intact while their expensive source
subtrees are compacted into the authentic symbol. Primary and selected
controls receive actual positioned seal elements, not background wallpaper.

## 8. Glass Material Architecture

The final token layer uses pure black as the world, Cosmic Ink for lifted
depth, Pearl Ivory for primary text, Champagne and Stellar Gold for emphasis,
and thin pink/cyan refraction at selected edges. Violet remains an accent and
is not used as a panel flood.

Named material roles cover shell, panel, elevated panel, input, primary
control, secondary control, destructive control and selected navigation.
Backdrop blur, border strength, opacity and shadow are deterministic per role.
Nested full-screen blur and animated large filters were removed or avoided.

Layer roles are bounded as galaxy, atmosphere, content, sticky shell,
dropdown, popover, backdrop, modal, toast and critical overlay. The remaining
numeric values are small and intentional rather than near-maximum integers.

## 9. Control Hierarchy

- Primary actions use transparent black glass, a Champagne inner line,
  spectral edge, Pearl label, authentic leading seal and controlled glow.
- Secondary actions are quieter and do not compete with the primary action.
- Navigation selected state uses a symmetric frame and state seal.
- Icon controls retain compact geometry and a 44px mobile target where they
  are critical.
- Chips remain compact and do not receive button-scale glow.
- Destructive actions use Coral Flame and Radiant Rose rather than gold.
- Inputs retain stable dimensions and visible focus without layout movement.
- Rest, hover, focus-visible, pressed, selected, disabled, busy and error
  contracts are scoped by semantic role.

## 10. Geometry Architecture

The shared shell and route surfaces now use CSS Grid, local flex groups,
`clamp()`, bounded tracks, aspect ratios, logical properties, safe-area insets
and mobile alternate compositions. Fixed desktop assumptions no longer govern
the entire viewport range.

Systems uses a bounded responsive field and proportional safe regions. Desktop
nodes live around the exact center chamber; narrow screens switch to a
deliberate vertical list instead of compressing manually positioned desktop
nodes. The title, subtitle, NUR lockup, brain chamber, stats, legend, controls
and mantra have distinct regions.

The reusable Playwright helper measures document overflow, escaped controls,
touch targets, visible rectangles, pairwise overlap and center-axis deltas.
Its required center tolerance is 1 CSS pixel on desktop and 1.5 CSS pixels on
mobile.

## 11. Route-By-Route Work

- Entry/auth/onboarding: retained canonical words and spacing, installed black
  spectral glass actions and authentic seals, and kept the NUR lockup centered.
- Today: integrated one exact brain owner, canonical check-in controls and
  clear next-move hierarchy.
- Talk: normalized cognitive panels and composer controls without generic chat
  wallpaper.
- Journal: preserved the writing-first layout with stable glass form controls.
- Plan: separated directional actions, completion state and outcome state.
- Systems: rebuilt map proportions, node treatment, brain chamber, stats,
  legend and mobile alternate composition.
- Universe/Map: shares the Systems visual center, exact brain and seven
  authentic node seals.
- Orbits, Timeline, Insights, Research, Community and Web Signals: use the same
  material and control laws while preserving route-specific information
  hierarchy.

No route copy, API contract, authentication rule or persisted action was
deliberately changed by this rebuild.

## 12. Adjunct Surface Migration

The large embedded style system was extracted from `v197Adjuncts.ts` into
`v197-adjunct-forensic.css`. Settings, Capsule, Consultations, Projects, Glow,
Notifications and Omega now share the canonical black glass, type, spacing,
form, control, seal and layer contracts.

The migration removes the adjunct-only brown-purple buttons, old-gold flood,
tiled pseudo-stars, generic unrelated cards, duplicate wordmark treatment and
nuclear z-index values. Dense adjunct content remains structurally dense; it
was not converted into decorative landing-page cards.

## 13. Brain Renderer Changes

The current renderer is `v43StarBrainRuntime.js`, derived directly from the
founder-supplied V43 V7 front-page star-brain source. Its cortex, cerebellum,
synapses, neural pulses, rotation, shatter and reform behavior remain intact.
The approved sparkle-and-stem extension raises the anatomy to 854 desktop
points and 576 mobile points, including a curved 84/56-star brainstem and
independent galaxy-style glints rendered with the same lightweight particle paint as both V197 sky rigs.

The old V197 enhanced runtime and its visual/lifecycle source transforms were
removed. The bridge only gives the direct renderer the canonical host,
clears an already-mounted legacy canvas, and preserves the host click/keyboard
ritual. A radial CSS mask is intentionally external to the source: it fades
stardust in a circular field so a square canvas boundary cannot be seen.

## 14. Protected Source Before/After Hashes

| Source | Before SHA-256 | After SHA-256 | Result |
| --- | --- | --- | --- |
| Canonical V197 host | `d4f7f2d3e4c8e36dfc0c6edd51a028f28a04afbc2afa434a319009cb2f122bc6` | `d4f7f2d3e4c8e36dfc0c6edd51a028f28a04afbc2afa434a319009cb2f122bc6` | Identical |
| Entry reference | `cdeac0c8574333c7261be2bc410357ecc5407ee0dd5b1b8089630f3914026030` | `cdeac0c8574333c7261be2bc410357ecc5407ee0dd5b1b8089630f3914026030` | Identical |
| Universe reference | `3cff07b31e8360e5ce793287298d66127c4f278705dc0f8e6abdfbe7e874dc40` | `3cff07b31e8360e5ce793287298d66127c4f278705dc0f8e6abdfbe7e874dc40` | Identical |
| V43 V7-derived brain runtime | `d83705cc9cca27c42dd89fdea1f1b9fc057200351f67eda995d0ee2e4683c4e6` | `eb7948724ca0463db263d11c8e9991a877991d89bded06303adc524d9258b099` | Intentional exact-galaxy paint, sparkle, anatomical stem extension, lower-DPR raster work, cached camera transforms, and allocation-light frame pacing |

The current cleaned build was hashed. The three protected V197/reference files
remain identical; the brain runtime hash records the approved visual extension.

## 15. Performance Defects Found

- Fixed 25ms ambient and approximately 72ms interaction timer pacing made
  pointer interaction visibly starved.
- The exact brain could keep RAF, pulse timers, observers and wheel behavior
  alive while hidden or after its host left the document.
- Several stellar dialects and duplicate full-screen fields increased paint
  and DOM work without improving identity.
- Fake mini-star DOM replacement discarded identity while still causing
  repeated mutation work.
- Broad animated shadows, filters and nested glass amplified repaint cost.

No synthetic frame-time or long-task number is reported as a measured result.

## 16. Performance Fixes Made

- Replaced fixed timer pacing with requestAnimationFrame scheduling and the
  renderer's measured-frame adaptive quality path.
- Suspended the brain when hidden, disconnected or outside the viewport.
- Added gradual activity restart and reduced-motion single-frame behavior.
- Tracked and cleared deferred pulse timers and the ambient pulse timer.
- Disconnected ResizeObserver, IntersectionObserver and MutationObserver
  instances on disposal.
- Changed wheel zoom to require Ctrl or Meta so ordinary page scrolling is not
  trapped.
- Removed the extra CSS sparkfield and consolidated mini-stars into one SVG
  symbol per document.

## 17. Active Canvases And Runtime Ownership

The intended active ownership contract is:

- At most one background galaxy canvas in a frame where the canonical host
  requires it.
- At most one exact star-brain canvas on an active brain surface.
- One lifecycle controller for that brain host.
- No whole-interface CSS sparkfield canvas or span field.
- One shared hidden SVG star-seal sprite per document, referenced by all
  visible seals.

Unit contracts verify lifecycle installation and cleanup source. Playwright
specifications verify duplicate brain/canvas ownership after navigation, but
their browser execution remains pending in this sandbox.

## 18. Responsive Viewport Results

The reusable matrix includes all mandated sizes:

`360x800`, `390x844`, `430x932`, `844x390`, `768x1024`, `1024x768`,
`1280x720`, `1366x768`, `1440x900`, `1920x1080`, `2560x1080`, and
`2560x1440`.

For every size, the new specification checks document width, escaped controls,
critical touch targets, shell composition, Systems geometry and center
contracts. RTL, long labels, modal fit and reduced motion are covered in
separate states.

Result: matrix implementation and test discovery pass. Browser execution is
not directly validated here because Playwright cannot start its configured
Vite server under the sandbox's socket policy. No viewport is marked visually
passed in this report.

## 19. Overlap Test Results

The helper performs bounding-rectangle pair checks for node-to-node and
protected-region intersections. Route specs cover topbar groups, title and
brain, brain and Systems nodes, map controls, rails, composer/mobile tabs,
modal/viewport and adjunct topbar/hero relationships.

Result: helper and static contracts pass unit/type validation and all related
Playwright tests are discovered. Rendered overlap assertions could not execute
because the local web server cannot bind, so the final overlap result is
pending an unrestricted browser runner.

## 20. Centering Measurement Results

`v197CenterDelta()` computes real bounding-box center deltas between the NUR
wordmark, subtitle, brain host/canvas and Systems center. The specifications
enforce <= 1px desktop and <= 1.5px mobile tolerance.

Result: the lockup and chamber implementation use one geometric axis, and the
measurement suite is present and discoverable. Fresh post-rebuild numerical
measurements were not produced because browser execution was blocked; this
criterion remains pending direct validation.

## 21. Accessibility Changes

- Added a consistent, visible gold/cyan `:focus-visible` contract.
- Preserved logical focus order and restored focus after modal close.
- Added modal focus trapping and Escape behavior coverage.
- Added 44px critical mobile touch targets and safe-area modal bounds.
- Restored browser zoom behavior and avoided global scroll prevention.
- Added reduced-motion laws for seals, ambient effects and exact-brain
  scheduling.
- Added RTL and deliberately long-label geometry coverage.
- Preserved ARIA state while replacing mini-star visual subtrees.
- Kept destructive, disabled, busy and selected states distinguishable without
  relying only on color.

## 22. Exact Test Commands And Results

| Command | Result |
| --- | --- |
| `npm --workspace apps/web run test -- --run` | PASS: 21 files, 91 tests |
| `npm --workspace apps/web run typecheck` | PASS: `tsc --noEmit` |
| `npm --workspace apps/web run build` | PASS: 26 modules, bridge 396.92 kB, gzip 105.70 kB |
| `VITE_NUR_ENABLE_OMEGA_RESEARCH=true npm --workspace apps/web run build` | PASS: 26 modules, bridge 396.92 kB, gzip 105.70 kB |
| `npm --workspace apps/web run e2e -- --list` | PASS: 270 tests discovered in 39 files across Chromium desktop, Chromium mobile and WebKit mobile |
| `npm --workspace apps/web run e2e` | BLOCKED: Playwright webServer exited before tests |
| `npm --workspace apps/web run preview -- --host 127.0.0.1 --port 4173` | BLOCKED: `listen EPERM: operation not permitted 127.0.0.1:4173` |
| `git diff main..HEAD --check` | PASS |
| Protected-source `sha256sum` checks | PASS: all four unchanged |

Targeted forensic and Omega Playwright execution was attempted separately and
hit the same webServer bind restriction. Test discovery succeeded.

## 23. Screenshot Locations

Baseline and intermediate proof captured before the final restricted pass:

- `/tmp/nur-forensic-baseline/entry-1440x900.png`
- `/tmp/nur-forensic-baseline/settings-1440x900.png`
- `/tmp/nur-forensic-baseline/systems-1440x900.png`
- `/tmp/nur-forensic-core-before-today-1440x900.png`
- `/tmp/nur-forensic-core-before-talk-1440x900.png`
- `/tmp/nur-forensic-core-before-journal-1440x900.png`
- `/tmp/nur-forensic-core-before-plan-1440x900.png`
- `/tmp/nur-forensic-core-before-systems-1440x900.png`
- `/tmp/nur-star-seal-proof.png`
- `/tmp/nur-forensic-phase4-seals.png`

Existing historical project proof also remains under `apps/web/proof` in the
user's dirty worktree, but it was not added to these rebuild commits.

No image above is represented as a final post-Phase-10 screenshot. The
required final screenshot matrix remains blocked with browser execution.

## 24. Remaining Known Defects

1. Full Playwright execution, rendered overlap assertions, numerical center
   measurements and final screenshots require an environment that permits a
   localhost Vite server and browser sockets.
2. Acceptance criteria 30 and 31 are therefore pending, and criteria 12, 13,
   19, 20, 23, 24, 25 and 26 have automated contracts but still require the
   final browser run for direct confirmation.
3. The copied worktree contains substantial pre-existing dirty frontend and
   backend work. The rebuild commits intentionally exclude it, but anyone
   running the entire repository must account for that local state.
4. No honest before/after frame-time or long-task comparison was available in
   the restricted browser environment.

## 25. Deliberately Deferred Work

- Backend, API, database, authentication, persistence and owner-data changes
  were out of scope and were deliberately not made.
- Protected canonical V197 and exact renderer byte edits were unnecessary and
  deliberately avoided.
- Screenshot baseline acceptance was deferred until the browser matrix can run
  without socket restrictions; baselines will not be blindly updated.
- Public GitHub delivery was attempted with
  `git push -u origin frontend/nur-forensic-rebuild`. The sandbox could not
  resolve `github.com`, so no public-push success is claimed. A complete-history
  Git bundle is produced at
  `/home/nur/Downloads/AM -Clean/NUR_FORENSIC_REBUILD.bundle` and verified with
  `git bundle verify`; its final checksum is recorded in the delivery response.

## Delivery Verdict

All twelve development phases have an implementation or evidence artifact.
The frontend reconstruction itself is complete, code gates pass, protected
sources are intact, and the branch contains no backend delta. Final rendered
acceptance is explicitly pending rather than falsely reported as complete.
