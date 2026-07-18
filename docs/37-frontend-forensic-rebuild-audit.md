# NUR Frontend Forensic Rebuild Audit

Branch: `frontend/nur-forensic-rebuild`

Baseline commit: `49ae3bc21a5f4e8a9b0e012bd4793a64d32ae49a`

This audit records the presentation ownership and failure modes observed before
the forensic rebuild. Product behavior, API contracts, authentication,
persistence, and backend code are outside the rebuild boundary.

## Protected Sources

| Source | SHA-256 in current cleaned build | Policy |
| --- | --- | --- |
| `apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html` | `d4f7f2d3e4c8e36dfc0c6edd51a028f28a04afbc2afa434a319009cb2f122bc6` | Preserve byte-for-byte |
| `docs/reference/entry_decoded_v197.html` | `cdeac0c8574333c7261be2bc410357ecc5407ee0dd5b1b8089630f3914026030` | Reference only |
| `docs/reference/universe_decoded_v197.html` | `3cff07b31e8360e5ce793287298d66127c4f278705dc0f8e6abdfbe7e874dc40` | Reference only |
| `apps/web/src/bridge/v43StarBrainRuntime.js` | `eb7948724ca0463db263d11c8e9991a877991d89bded06303adc524d9258b099` | V43 V7 founder anatomy with the approved star-brainstem extension, exact lightweight V197 galaxy-rig particle paint, lower-DPR raster work, cached camera transforms, and allocation-light 30fps rendering; host placement and circular CSS dispersal remain outside it |

## Runtime Ownership

The live product is the canonical V197 document composed by
`apps/web/vite.config.ts`, not the React route tree. Vite keeps the canonical
HTML on disk and adds the performance bootstrap and `v197-bridge.js` at
request time.

Presentation order inside the universe frame is:

1. Canonical V197 styles and scripts.
2. Hydrated owner-ledger markup from `v197Hydration.ts`.
3. Native route and interaction wiring from `v197Bridge.ts` and
   `v197Bindings.ts`.
4. Premium polish from `v197Polish.ts`.
5. Intelligence spine CSS.
6. The final cosmic skin from `v197-cosmic-skin.css`.
7. Adjunct routes mounted by `v197Adjuncts.ts` in a fixed overlay.

The final injected style is therefore the effective visual owner wherever it
uses broad selectors or `!important`.

## Route Audit

| Surface | Route family | DOM owner | Presentation owner before rebuild | Geometry owner | Primary defects |
| --- | --- | --- | --- | --- | --- |
| Entry and auth sheet | `/`, `/auth`, `/onboarding` | Canonical entry srcdoc | Canonical patches plus `v197Polish.ts` and cosmic skin | Canonical `.f4-*` plus cosmic overrides | Dotted CTA material, weak hierarchy, inconsistent seal treatment, competing glow layers |
| Password recovery | `/auth/reset` | Canonical entry plus `v197Recovery.ts` | Recovery CSS plus cosmic skin | Recovery renderer | Visually detached from final control system |
| Today | `/today` | Canonical universe plus hydration | Canonical styles plus premium polish and cosmic skin | Canonical page grid | Blanket control treatment and duplicated stellar canvases |
| Talk | `/talk`, `/talk/*` | Canonical universe plus hydration | Canonical styles plus premium polish and cosmic skin | Canonical page grid | Blanket control treatment and inconsistent composer material |
| Journal | `/journal`, `/journal/*` | Canonical universe plus hydration | Canonical styles plus premium polish and cosmic skin | Canonical journal layout | Form controls and actions lack semantic hierarchy |
| Plan | `/plan`, `/plan/*` | Canonical universe plus hydration | Canonical styles plus premium polish and cosmic skin | Canonical page grid | Actions, chips, and cards collapse into one material |
| Systems field | `/systems`, `/systems/:slug` | Canonical Systems DOM plus hydration | Canonical styles, `v197Polish.ts`, cosmic skin | Hard-coded map offsets and fixed heights in `v197Polish.ts` | Endless stack, oversized fixed map, node collisions, tiny text, repeated dotted buttons, excessive empty space |
| System workspace | `/systems/:slug/work` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic 12-column adjunct grid | Separate brown-orange product, generic cards and pills, tiled pseudo-stars |
| Universe lenses | `/universe`, `/universe/map`, `/universe/orbits`, `/universe/timeline`, `/universe/insights` | Canonical Systems DOM plus `v197Hydration.ts` lens markup | Premium polish, universe-scoped CSS, cosmic skin | Lens-specific hydration and shared shell | Shared shell treatment is noisy; lens geometry inherits fixed assumptions |
| Universe focus surfaces | `/universe/research`, `/universe/community`, `/universe/web-signals` | Canonical Systems lower cards plus hydration | Premium polish and cosmic skin | Systems lower grid | Dense stacked cards and undifferentiated actions |
| Settings | `/settings` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Same separate visual island; destructive and primary actions look alike |
| Capsules | `/capsule/:id` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Boundary state is clear semantically but visually generic |
| Consultations | `/consultations`, `/consultations/:id` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Stage path is rendered as ordinary chips; hierarchy is flat |
| Community | `/community/*` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Feed, moderation, people, and room tools share one card/pill language |
| Projects | `/projects/*` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Project navigation and high-risk approvals lack distinct variants |
| Glow | `/glow` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Economy and ledger surfaces do not share the universe visual grammar |
| Notifications | `/notifications` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Inbox, delivery state, and settings are visually undifferentiated |
| Omega | `/universe/omega/*` | `v197Adjuncts.ts` | Embedded adjunct CSS | Generic adjunct grid | Review gates and evidence states use the same generic panel treatment |

## Confirmed Root Causes

### Blanket dotted controls

The late selector below matches almost every button in both entry and universe
frames:

```css
body #nur-front-v61 button:not(.f4-brand),
body.universe-edition #nur-front-v61 button
```

It adds two repeated radial-gradient dots and one generic dark gradient. On a
left-rail nav control at 1440 by 900, the computed result is a 14px-radius
button with the same dotted fill used by map nodes, tabs, chips, CTAs, scope
controls, and composer actions.

### Competing material systems

`v197-cosmic-skin.css` contains multiple successive glass definitions with
different blur, opacity, border, radius, and glow values. The broadest rules
win by source order, flattening semantic distinctions already present in the
canonical document.

### Hard-coded Systems geometry

`v197Polish.ts` fixes the Systems map to a 520px minimum height, positions map
nodes with guessed edge percentages, uses a fixed 282px statistics width,
clips overflow, and installs a fixed 96px mobile topbar. Those assumptions do
not survive the supported viewport matrix and produce the tall stacked page
shown in the supplied evidence.

### Duplicate stellar dialects

The page can own all of these simultaneously:

- canonical `#space3d`;
- `#nur-v197-static-starfield`;
- exact star-brain canvas;
- whole-interface `#v197-sparkfield` spans;
- CSS tiled radial-gradient dots on controls and adjunct backdrops.

The result is more activity but less visual depth and materially higher paint
cost.

### Fake mini-star replacement

`compactV197MiniStars()` replaces approved mini-star hosts with a simplified
gradient polygon via `replaceChildren()`. This destroys the host's authentic
star structure and makes small seals look like generic icons.

### Animation throttling and lifecycle leaks

`v197PerformanceProfile.ts` converts normal animation scheduling into fixed
25ms and 72ms timer delays. The exact star-brain runtime also leaves RAF,
interval, observer, and wheel behavior alive after route or visibility
changes. The profile reduces fidelity without establishing measurable adaptive
quality, while the leaked work remains.

## Baseline Browser Evidence

Playwright was used because the Browser plugin is unavailable in this
workspace. Baseline captures are stored outside the repository at
`/tmp/nur-forensic-baseline`.

At 1440 by 900 the live universe frame showed:

- 244 interactive controls on hydrated Systems surfaces;
- canonical `#space3d`, a second full-screen static starfield, and the
  star-brain canvas mounted together;
- the dotted radial-gradient control fill as the final computed background;
- no top-level horizontal overflow, while content was trapped inside nested
  fixed-height frame and scroll owners.

## Rebuild Boundary

The rebuild will:

- remove the blanket skin and fake dotted stars;
- establish one token, material, geometry, motion, and layer contract;
- install one authentic NUR star-seal implementation for small UI sizes;
- normalize the shared shell and Systems field with responsive geometry;
- bring adjuncts into the same product without changing their data/actions;
- preserve approved brain anatomy and point counts while fixing ownership and
  lifecycle;
- add geometry, ownership, and route-matrix tests before final approval.

It will not alter backend code, API payloads, authentication rules, database
behavior, persistence, or canonical V197 source bytes.
