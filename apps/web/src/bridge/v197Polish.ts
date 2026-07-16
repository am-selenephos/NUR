import V197_COSMIC_SKIN_CSS from "../styles/v197-cosmic-skin.css?raw";
import V197_STAR_SEAL_CSS from "../styles/v197-star-seal.css?raw";
import { ensureV197BlackGalaxy, ensureV197StarBrain } from "./v197StarBrain";
import { installV197StarSeals, V197_STAR_SEAL_CLASS } from "./v197StarSeal";

export const V197_PREMIUM_POLISH_STYLE_ID = "nur-v197-track-a-premium-polish";
export const V197_STABLE_WORDMARK_CLASS = "nur-v197-stable-wordmark";
export const V197_COMPACT_MINI_STAR_CLASS = V197_STAR_SEAL_CLASS;
export const V197_INTERACTION_BUDGET_MARKER = "nurInteractionBudget";
export const V197_STATIC_STARFIELD_ID = "nur-v197-static-starfield";
export const V197_ENTRY_POLISH_STYLE_ID = "nur-v197-entry-premium-polish";

const V197_PREMIUM_POLISH_CSS = `
/* Track A corrective layer. Canonical V197 source bytes and runtime stay intact. */
.nur-v197-checkin {
  margin-block: 16px 4px;
  padding: 14px;
  border: 1px solid rgba(255, 218, 128, .2);
  border-radius: 8px;
  background: rgba(4, 2, 7, .72);
  box-shadow: inset 0 1px 0 rgba(255, 244, 208, .05);
}

.nur-v197-checkin[hidden] { display: none !important; }
.nur-v197-checkin h3 { color: var(--f-pearl); font: 600 18px/1.15 "Crimson Pro", serif; }
.nur-v197-checkin > p { margin-block: 4px 12px; color: rgba(255, 227, 169, .62); }
.nur-v197-checkin-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 14px; }
.nur-v197-checkin-field { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; color: rgba(255, 239, 203, .82); }
.nur-v197-checkin-field output { color: var(--f-yolk); font-variant-numeric: tabular-nums; }
.nur-v197-checkin-field input[type="range"] {
  grid-column: 1 / -1;
  width: 100%;
  height: 3px;
  appearance: none;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(219,119,24,.72), rgba(64,216,255,.5));
}
.nur-v197-checkin-field input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 13px;
  height: 13px;
  border: 1px solid rgba(255,237,174,.8);
  border-radius: 50%;
  background: #f3ae1f;
  box-shadow: 0 0 14px rgba(243,174,31,.5);
}
.nur-v197-checkin > input {
  width: 100%;
  margin-block: 12px 10px;
  border: 1px solid rgba(255, 218, 128, .22);
  border-radius: 7px;
  background: rgba(2, 1, 3, .8);
  color: var(--f-pearl);
  padding: 10px 12px;
  font: 16px/1.2 "Crimson Pro", serif;
}
.nur-v197-today-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.nur-v197-today-actions .soft-button:disabled { opacity: .42; cursor: not-allowed; }
.nur-v197-language-open {
  max-width: 146px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nur-v197-select-shell {
  position: relative;
  display: block;
  width: 100%;
  min-width: 0;
  margin-block: 5px 11px;
  border: 1px solid rgba(255, 218, 128, .26);
  border-radius: 8px;
  background:
    radial-gradient(circle at 12% 0%, rgba(255, 186, 72, .12), transparent 34%),
    linear-gradient(125deg, rgba(18, 10, 24, .98), rgba(4, 2, 8, .98));
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 208, .055),
    0 12px 26px rgba(0, 0, 0, .24),
    0 0 20px rgba(243, 174, 31, .035);
  transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
  overflow: hidden;
}
.nur-v197-select-shell::after {
  content: "⌄";
  position: absolute;
  inset-inline-end: 13px;
  top: 50%;
  transform: translateY(-56%);
  color: #f3ae1f;
  font: 500 18px/1 "Crimson Pro", serif;
  text-shadow: 0 0 12px rgba(243, 174, 31, .52);
  pointer-events: none;
}
.nur-v197-select-shell:hover {
  border-color: rgba(255, 218, 128, .48);
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 208, .08),
    0 14px 30px rgba(0, 0, 0, .3),
    0 0 24px rgba(243, 174, 31, .08);
}
.nur-v197-select-shell:focus-within {
  border-color: rgba(84, 234, 255, .48);
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 208, .08),
    0 0 0 2px rgba(84, 234, 255, .09),
    0 0 28px rgba(173, 124, 255, .11);
}
#scope-modal .nur-v197-select {
  appearance: none !important;
  -webkit-appearance: none !important;
  display: block !important;
  width: 100% !important;
  min-width: 0 !important;
  margin: 0 !important;
  padding: 11px 42px 11px 13px !important;
  border: 0 !important;
  border-radius: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  color: rgba(255, 241, 212, .94) !important;
  -webkit-text-fill-color: rgba(255, 241, 212, .94) !important;
  color-scheme: dark;
  font: 500 16px/1.25 "Crimson Pro", serif !important;
  letter-spacing: .01em !important;
  cursor: pointer;
}
#scope-modal .nur-v197-select option,
#scope-modal .nur-v197-select optgroup {
  background: #09060d !important;
  color: #fff0ce !important;
  font: 500 16px/1.3 "Crimson Pro", serif !important;
}
#scope-modal .nur-v197-select option:checked {
  background: #332015 !important;
  color: #ffe09a !important;
}
.nur-v197-provider-status {
  display: grid;
  gap: 3px;
  margin-block: 12px 10px;
  padding: 11px 12px;
  border: 1px solid rgba(255, 216, 126, .18);
  border-radius: 8px;
  background: linear-gradient(110deg, rgba(255, 159, 36, .08), rgba(88, 216, 255, .035));
}
.nur-v197-provider-status > span {
  color: rgba(255, 230, 181, .58);
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.nur-v197-provider-status > strong { color: #ffe09a; font-weight: 500; }
.nur-v197-provider-status > small { color: rgba(255, 239, 206, .62); line-height: 1.3; }
.nur-v197-insight-controls {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 213, 119, .15);
}
.nur-v197-insight-controls[hidden] { display: none !important; }
.nur-v197-insight-controls > input {
  width: 100%;
  border: 1px solid rgba(255, 218, 128, .22);
  border-radius: 7px;
  background: rgba(2, 1, 3, .78);
  color: var(--f-pearl);
  padding: 9px 11px;
  font: 15px/1.2 "Crimson Pro", serif;
}
.nur-v197-insight-actions { display: flex; flex-wrap: wrap; gap: 6px; }
.nur-v197-insight-actions .soft-button { padding: 7px 10px; font-size: 13px; }
.nur-v197-insight-review-state { color: rgba(255, 232, 190, .55); }
/* The scope/language chamber gained the provider-status block; the canonical
 * modal has no scroll of its own, so the save control could leave the
 * viewport. Scrolling inside the chamber keeps every control reachable at
 * every height without touching canonical bytes. */
#scope-modal .scope-modal { max-height: min(86vh, 780px); overflow-y: auto; overscroll-behavior: contain; }
.nur-v197-community-controls {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 213, 119, .15);
}
.nur-v197-community-controls > input {
  width: 100%;
  border: 1px solid rgba(255, 218, 128, .22);
  border-radius: 7px;
  background: rgba(2, 1, 3, .78);
  color: var(--f-pearl);
  padding: 9px 11px;
  font: 15px/1.2 "Crimson Pro", serif;
}
.nur-v197-community-controls > input:disabled { opacity: .42; cursor: not-allowed; }
.nur-v197-community-actions { display: flex; flex-wrap: wrap; gap: 6px; }
.nur-v197-community-controls button {
  border: 1px solid rgba(255, 218, 128, .28);
  border-radius: 7px;
  background: rgba(255, 191, 87, .12);
  color: var(--f-pearl);
  padding: 7px 11px;
  font: 500 13px/1.2 "Crimson Pro", serif;
  cursor: pointer;
}
.nur-v197-community-controls button:hover:not(:disabled) { background: rgba(255, 191, 87, .22); }
.nur-v197-community-controls button:disabled { opacity: .42; cursor: not-allowed; }
.nur-v197-community-state { color: rgba(255, 232, 190, .55); }

@keyframes nurV197MasterRayOrbit {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes nurV197MasterCorePulse {
  0%, 100% { opacity: .86; transform: translate(-50%, -50%) scale(.94); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.08); }
}

/*
 * Full-size V197 stars previously animated every halo, orb, ray, ray core and
 * pseudo-layer independently. Keep the same DOM and gradients, but use two
 * compositor-friendly motions on the interactive Map star only. Secondary
 * stars remain luminous and static instead of competing for every frame.
 */
body.universe-edition .f4-master-star--hero:not(.nur-star-module),
body.universe-edition .f4-master-star--hero:not(.nur-star-module) *,
body.universe-edition .f4-master-star--hero:not(.nur-star-module)::before,
body.universe-edition .f4-master-star--hero:not(.nur-star-module)::after,
body.universe-edition .f4-master-star--hero:not(.nur-star-module) *::before,
body.universe-edition .f4-master-star--hero:not(.nur-star-module) *::after {
  animation: none !important;
  transition: none !important;
  will-change: auto !important;
}

body.universe-edition .f4-master-star--hero:not(.nur-star-module) {
  filter: brightness(1.08) saturate(1.08) !important;
}

body.universe-edition .f4-master-star--hero:not(.nur-star-module) :is(.ray-glow, .spark-h2, .ob) {
  display: none !important;
}

body.universe-edition .f4-master-star--hero:not(.nur-star-module) :is(.spark-glow, .spark-halo) {
  animation: none !important;
  filter: blur(6px) saturate(1.06) !important;
  will-change: auto !important;
}

body.universe-edition #iSpark .rayset {
  animation: nurV197MasterRayOrbit 24s linear infinite !important;
  transform-origin: 50% 50% !important;
  will-change: transform !important;
}

body.universe-edition #iSpark .spark-core {
  animation: nurV197MasterCorePulse 4.8s ease-in-out infinite !important;
  transform-origin: 50% 50% !important;
  will-change: transform, opacity !important;
}

/* Canonical V89/V97 star rules carry an ID selector. Mirror that specificity
 * so the late corrective layer actually wins instead of merely appearing
 * later in the stylesheet order. */
body.universe-edition #nur-front-v61 #iSpark,
body.universe-edition #nur-front-v61 #iSpark *,
body.universe-edition #nur-front-v61 #iSpark::before,
body.universe-edition #nur-front-v61 #iSpark::after,
body.universe-edition #nur-front-v61 #iSpark *::before,
body.universe-edition #nur-front-v61 #iSpark *::after,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module *,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module::before,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module::after,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module *::before,
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module *::after,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module *,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module::before,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module::after,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module *::before,
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module *::after {
  animation: none !important;
  transition: none !important;
  will-change: auto !important;
}

body.universe-edition #nur-front-v61 #iSpark :is(.ray-glow, .spark-h2, .ob),
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module :is(.ray-glow, .spark-h2, .ob),
body.universe-edition #nur-front-v61 .nur-exact-mini-host .nur-star-module :is(.ray-glow, .spark-glow, .spark-halo, .spark-h2, .ob) {
  display: none !important;
}

body.universe-edition #nur-front-v61 #iSpark :is(.spark-glow, .spark-halo),
body.universe-edition #nur-front-v61 .v172-boundary-orb > .nur-star-module :is(.spark-glow, .spark-halo) {
  animation: none !important;
  filter: blur(6px) saturate(1.06) !important;
  will-change: auto !important;
}

body.universe-edition #nur-front-v61 #iSpark .rayset {
  animation: nurV197MasterRayOrbit 24s linear infinite !important;
  transform-origin: 50% 50% !important;
  will-change: transform !important;
}

body.universe-edition #nur-front-v61 #iSpark .spark-core {
  animation: nurV197MasterCorePulse 4.8s ease-in-out infinite !important;
  transform-origin: 50% 50% !important;
  will-change: transform, opacity !important;
}

/* The Map previously recomposited every decorative chip, legend glyph, fog
 * layer and scope control while the galaxy canvas was already moving below
 * them. Keep their exact V197 paint, hover and focus states, but reserve idle
 * motion for the holographic wordmark and the interactive MasterStar. */
body.universe-edition #page-systems :is(
  .world-command,
  .clean-nav-button,
  .nur-scope,
  .universe-map-fog,
  .universe-add-system,
  .universe-map-legend i,
  .universe-composer-shell,
  .universe-composer,
  .audit-scope,
  .soft-button,
  .composer-action__glint,
  .v172-footer-dot
),
body.universe-edition #page-systems :is(
  .world-command,
  .clean-nav-button,
  .nur-scope,
  .universe-map-fog,
  .universe-add-system,
  .universe-map-legend i,
  .universe-composer-shell,
  .universe-composer,
  .audit-scope,
  .soft-button,
  .composer-action__glint,
  .v172-footer-dot
)::before,
body.universe-edition #page-systems :is(
  .world-command,
  .clean-nav-button,
  .nur-scope,
  .universe-map-fog,
  .universe-add-system,
  .universe-map-legend i,
  .universe-composer-shell,
  .universe-composer,
  .audit-scope,
  .soft-button,
  .composer-action__glint,
  .v172-footer-dot
)::after {
  animation: none !important;
  will-change: auto !important;
}

body.universe-edition #nur-front-v61 :is(
  .clean-nav-button,
  .nur-scope,
  .audit-scope,
  .nur-star-prefix-row,
  .v172-footer-dot
),
body.universe-edition #nur-front-v61 :is(
  .clean-nav-button,
  .nur-scope,
  .audit-scope,
  .nur-star-prefix-row,
  .v172-footer-dot
)::before,
body.universe-edition #nur-front-v61 :is(
  .clean-nav-button,
  .nur-scope,
  .audit-scope,
  .nur-star-prefix-row,
  .v172-footer-dot
)::after {
  animation: none !important;
  will-change: auto !important;
}

@media (prefers-reduced-motion: reduce) {
  body.universe-edition #nur-front-v61 *,
  body.universe-edition #nur-front-v61 *::before,
  body.universe-edition #nur-front-v61 *::after {
    animation-duration: .001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .001ms !important;
    scroll-behavior: auto !important;
  }

  body.universe-edition #nur-front-v61 #iSpark .rayset,
  body.universe-edition #nur-front-v61 #iSpark .spark-core,
  body.universe-edition #nur-front-v61 .v172-live-mark i,
  body.universe-edition #nur-front-v61 .v172-footer-dot {
    animation: none !important;
  }
}

/* Programmatic focus/click navigation must not chase a moving scroll target.
 * V197's smooth viewport scroll is pleasant for direct navigation, but a
 * server hydration update can move the destination while the browser is still
 * interpolating. Keep the visual transition language; make the owning
 * viewport settle in one frame so controls remain genuine hit targets. */
body.universe-edition .nur-viewport {
  scroll-behavior: auto !important;
}

@keyframes nurV197StableWordmarkFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes nurV197StableWordmarkGlow {
  0%, 100% {
    filter:
      drop-shadow(0 0 8px rgba(255, 250, 229, .9))
      drop-shadow(0 0 20px rgba(255, 190, 72, .54))
      drop-shadow(0 0 42px rgba(84, 234, 255, .2));
  }
  33% {
    filter:
      drop-shadow(0 0 9px rgba(236, 245, 255, .92))
      drop-shadow(0 0 22px rgba(84, 218, 255, .5))
      drop-shadow(0 0 46px rgba(110, 148, 255, .24));
  }
  66% {
    filter:
      drop-shadow(0 0 9px rgba(255, 238, 251, .92))
      drop-shadow(0 0 22px rgba(234, 130, 255, .48))
      drop-shadow(0 0 46px rgba(255, 120, 191, .24));
  }
}

/*
 * V197's own prism loop writes a 420%-wide inline background every frame.
 * Chromium can leave that transparent glyph layer unpainted. Keep its exact
 * DOM footprint, then paint the same NUR word through this bridge-native
 * sibling so the canonical title remains visible without React ownership.
 */
body.universe-edition .universe-map-title > .nur-holo-word[data-nur-stable-source="true"] {
  visibility: hidden !important;
}

body.universe-edition .universe-map-title > .nur-v197-stable-wordmark {
  position: absolute !important;
  top: 4px !important;
  left: 50% !important;
  z-index: 2 !important;
  display: block !important;
  box-sizing: border-box !important;
  width: 280px !important;
  max-width: calc(100vw - 88px) !important;
  margin: 0 !important;
  padding-inline: 0 !important;
  transform: translateX(-50%) !important;
  text-align: center !important;
  color: transparent !important;
  -webkit-text-fill-color: transparent !important;
  background-image: linear-gradient(
    90deg,
    #fff7df 0%,
    #ffd278 9%,
    #ff9b65 18%,
    #ff70a1 27%,
    #ffdf67 36%,
    #8ef4a4 45%,
    #54eaff 54%,
    #6e94ff 63%,
    #ad7cff 72%,
    #ea82ff 81%,
    #ff78bf 90%,
    #fff7df 100%
  ) !important;
  background-position: 0% 50%;
  background-size: 240% 100% !important;
  background-repeat: no-repeat !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  font-family: "Bodoni Moda", serif !important;
  font-size: 66px !important;
  font-weight: 500 !important;
  line-height: .79 !important;
  letter-spacing: .125em !important;
  white-space: nowrap !important;
  animation:
    nurV197StableWordmarkFlow 4.2s linear infinite,
    nurV197StableWordmarkGlow 3.6s ease-in-out infinite !important;
  pointer-events: none !important;
}

body.universe-edition .universe-map-title > .nur-master-subtitle {
  position: absolute !important;
  top: 58px !important;
  left: 50% !important;
  box-sizing: border-box !important;
  width: 280px !important;
  max-width: 280px !important;
  margin: 0 !important;
  padding-inline: 0 !important;
  transform: translateX(-50%) !important;
  text-align: center !important;
  white-space: nowrap !important;
}

@media (prefers-reduced-motion: reduce) {
  body.universe-edition .universe-map-title > .nur-v197-stable-wordmark {
    animation: none !important;
    background-position: 50% 50% !important;
  }
}

@media (max-width: 1180px) {
  body.universe-edition .universe-map-title > .nur-v197-stable-wordmark {
    top: 3px !important;
    font-size: 62px !important;
    line-height: .82 !important;
  }

  body.universe-edition .universe-map-title > .nur-master-subtitle {
    top: 53px !important;
  }
}

@media (max-width: 600px) {
  .nur-v197-checkin-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (min-width: 761px) {
  body.universe-edition #page-systems .universe-map-panel {
    /* overflow:hidden still permits programmatic horizontal scrolling. A
     * prior focused control could leave the whole constellation shifted and
     * clipped after a resize. overflow:clip keeps the canonical viewport fixed. */
    overflow: clip !important;
  }

  body.universe-edition #page-systems .universe-map-panel > .universe-map-title {
    left: 50% !important;
    /* System Field and Add System sit at opposite edges. The centre is the
     * intended title chamber: keep both title lines above the MasterStar halo
     * instead of letting either line paint over the star. */
    top: 10px !important;
    width: 170px !important;
    min-width: 0 !important;
    max-width: 170px !important;
  }

  body.universe-edition .universe-map-title .nur-holo-word {
    font-size: 48px !important;
    line-height: .86 !important;
    letter-spacing: .08em !important;
  }

  body.universe-edition .universe-map-title small {
    display: block !important;
    width: 170px !important;
    font-size: 8px !important;
    line-height: 1.1 !important;
    letter-spacing: .1em !important;
    text-align: center !important;
    text-wrap: balance !important;
    white-space: normal !important;
  }

  body.universe-edition .universe-system-node.neural {
    left: 49% !important;
    right: auto !important;
    bottom: 10% !important;
    max-width: 210px !important;
    transform: translateX(-50%) !important;
  }

  body.universe-edition .universe-system-node.wealth {
    left: 0 !important;
    bottom: 18% !important;
  }

  body.universe-edition #page-systems .universe-system-node.quiet {
    left: 1% !important;
    top: 31% !important;
  }

  body.universe-edition #page-systems .universe-system-node.embodied {
    right: 1.5% !important;
    top: 31% !important;
  }

  body.universe-edition .universe-system-node.social {
    right: 1.5% !important;
    bottom: 18% !important;
  }

  body.universe-edition .universe-map-mantra {
    bottom: 6px !important;
  }

  body.universe-edition .universe-map-legend {
    bottom: 12px !important;
    width: 210px !important;
    max-width: 210px !important;
    flex-wrap: wrap !important;
  }
}

@media (min-width: 761px) and (max-width: 1519px) {
  body.universe-edition #page-systems .universe-field-readout {
    width: 220px !important;
    max-width: 220px !important;
  }

  body.universe-edition #page-systems .universe-system-node.quiet,
  body.universe-edition #page-systems .universe-system-node.embodied {
    top: 31% !important;
  }

  body.universe-edition #page-systems .universe-system-node.public,
  body.universe-edition #page-systems .universe-system-node.relational {
    top: 46% !important;
  }

  body.universe-edition #page-systems .universe-system-node.wealth,
  body.universe-edition #page-systems .universe-system-node.social {
    bottom: 24% !important;
  }

  body.universe-edition #page-systems .universe-hero-copy .page-title {
    font-size: 48px !important;
    line-height: .96 !important;
  }

  body.universe-edition #page-systems .universe-hero-stats {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    flex: 0 0 282px !important;
    width: 282px !important;
    gap: 0 !important;
  }

  body.universe-edition #page-systems .universe-hero-stats > span {
    min-width: 0 !important;
    padding-inline: 10px !important;
  }

  body.universe-edition #page-systems .universe-map-panel {
    min-height: 520px !important;
  }

  body.universe-edition #page-systems .universe-map-panel > .universe-map-title > .nur-master-subtitle {
    display: block !important;
    width: 170px !important;
    max-width: 170px !important;
    font-size: 8px !important;
    line-height: 1.12 !important;
    letter-spacing: .09em !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    text-align: center !important;
  }

  body.universe-edition #page-systems .universe-map-panel > .universe-map-title > .nur-v197-stable-wordmark {
    width: 170px !important;
    max-width: 170px !important;
  }

  body.universe-edition .universe-main-grid {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  body.universe-edition .universe-insight-panel {
    min-height: 0 !important;
  }

  body.universe-edition .universe-top-tools > .universe-search,
  body.universe-edition .universe-top-tools > .universe-deep {
    display: none !important;
  }

  body.universe-edition .nur-v197-language-open {
    max-width: 112px !important;
    padding-inline: 9px !important;
  }

  body.universe-edition .universe-top-left {
    flex: 1 1 auto !important;
    min-width: 0 !important;
  }

  body.universe-edition .universe-top-tools {
    width: auto !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
  }

  body.universe-edition .universe-nav-tabs {
    width: auto !important;
    max-width: none !important;
    overflow: visible !important;
  }

  body.universe-edition .universe-nav-tabs button {
    padding-inline: 5px !important;
    gap: 5px !important;
    font-size: 15px !important;
  }

  body.universe-edition .universe-nav-tabs button > span:not(.nur-exact-mini-host) {
    font-size: 15px !important;
  }
}

@media (max-width: 760px) {
  body.universe-edition .mobile-tabs {
    z-index: 2147483000 !important;
    isolation: isolate !important;
    pointer-events: auto !important;
    transform: translateZ(0) !important;
  }

  body.universe-edition .mobile-tabs > button {
    position: relative !important;
    z-index: 1 !important;
    pointer-events: auto !important;
  }

  body.universe-edition .nur-viewport {
    padding-bottom: calc(96px + env(safe-area-inset-bottom)) !important;
  }

  body.universe-edition .universe-map-title > .nur-master-subtitle {
    top: 46px !important;
    max-width: min(280px, calc(100vw - 88px)) !important;
    white-space: normal !important;
  }

  body.universe-edition .universe-map-title > .nur-v197-stable-wordmark {
    top: 2px !important;
    font-size: 50px !important;
    line-height: .85 !important;
    letter-spacing: .11em !important;
  }

  body.universe-edition .nur-topbar {
    height: 96px !important;
    min-height: 96px !important;
    padding: 7px 12px 8px !important;
    display: grid !important;
    grid-template: 38px 38px / minmax(0, 1fr) !important;
    align-content: center !important;
    gap: 4px !important;
    overflow: hidden !important;
  }

  body.universe-edition .universe-top-tools {
    grid-area: 1 / 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    justify-content: flex-end !important;
  }

  body.universe-edition .universe-top-tools > .universe-search {
    display: none !important;
  }

  body.universe-edition .universe-top-tools > .universe-deep {
    width: auto !important;
    min-width: 132px !important;
    max-width: none !important;
    padding-inline: 11px !important;
  }

  body.universe-edition .universe-top-left {
    grid-area: 2 / 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    overflow: hidden !important;
  }

  body.universe-edition .universe-nav-tabs {
    width: 100% !important;
    max-width: none !important;
    display: flex !important;
    justify-content: flex-start !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    overscroll-behavior-inline: contain !important;
    scroll-snap-type: x proximity !important;
    scrollbar-width: none !important;
  }

  body.universe-edition .universe-nav-tabs::-webkit-scrollbar,
  body.universe-edition .universe-command-row::-webkit-scrollbar {
    display: none !important;
  }

  body.universe-edition .universe-nav-tabs button {
    width: auto !important;
    min-width: max-content !important;
    gap: 6px !important;
    padding-inline: 8px !important;
    flex: 0 0 auto !important;
    scroll-snap-align: start !important;
  }

  body.universe-edition .universe-nav-tabs button > span:not(.nur-exact-mini-host) {
    display: inline !important;
  }

  body.universe-edition .universe-command-row {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    overscroll-behavior-inline: contain !important;
    scroll-snap-type: x proximity !important;
    scrollbar-width: none !important;
  }

  body.universe-edition .universe-command-row .world-command {
    flex: 0 0 auto !important;
    scroll-snap-align: start !important;
  }

  body.universe-edition .universe-map-mantra {
    left: 10% !important;
    right: 10% !important;
    bottom: 52px !important;
    width: auto !important;
    transform: none !important;
    white-space: normal !important;
  }

  body.universe-edition .universe-map-legend {
    bottom: 10px !important;
    overflow-x: auto !important;
    justify-content: flex-start !important;
    scrollbar-width: none !important;
  }
}
`;

function ensureStableMapWordmark(document: Document): HTMLElement | null {
  const title = document.querySelector<HTMLElement>(".universe-map-title");
  const source = title?.querySelector<HTMLElement>(":scope > .nur-holo-word");
  if (!title || !source) return null;

  source.dataset.nurStableSource = "true";
  let stable = title.querySelector<HTMLElement>(`:scope > .${V197_STABLE_WORDMARK_CLASS}`);
  if (!stable) {
    stable = document.createElement("span");
    stable.className = V197_STABLE_WORDMARK_CLASS;
    stable.setAttribute("aria-hidden", "true");
    stable.textContent = "NUR";
    source.insertAdjacentElement("afterend", stable);
  }
  stable.style.setProperty("font-family", '"Bodoni Moda", serif', "important");
  stable.style.setProperty("font-weight", "500", "important");
  return stable;
}

/**
 * V197's source runtime expands every tiny icon into a complete MasterStar.
 * Keep the canonical host as the layout/selector contract, then remove only
 * the sub-pixel internals that cannot be perceived at the rendered size.
 */
export function compactV197MiniStars(document: Document): number {
  return installV197StarSeals(document);
}

/**
 * Tell the profiled V197 galaxy renderer when foreground input needs the main
 * thread. The galaxy alone slows briefly; native controls, scrolling, typing,
 * wordmark motion, and every other V197 animation keep their browser cadence.
 */
export function ensureV197InteractionBudget(document: Document): void {
  const root = document.documentElement;
  const universeWindow = document.defaultView;
  if (!universeWindow || root.dataset[V197_INTERACTION_BUDGET_MARKER] === "bound") return;
  root.dataset[V197_INTERACTION_BUDGET_MARKER] = "bound";

  let releaseTimer: number | null = null;
  const prioritizeInput = () => {
    root.dataset.nurInteractionActive = "true";
    if (releaseTimer !== null) universeWindow.clearTimeout(releaseTimer);
    releaseTimer = universeWindow.setTimeout(() => {
      delete root.dataset.nurInteractionActive;
      releaseTimer = null;
    }, 260);
  };

  document.addEventListener("pointerdown", prioritizeInput, { capture: true, passive: true });
  document.addEventListener("wheel", prioritizeInput, { capture: true, passive: true });
  document.addEventListener("keydown", prioritizeInput, true);
  document.addEventListener("input", prioritizeInput, true);
}

/**
 * Add visual depth without another animation loop. This canvas is painted once
 * (and on a debounced resize) with deterministic pin-prick stars, while V197's
 * own moving galaxy remains the only animated space layer.
 */
export function ensureV197StaticStarfield(
  document: Document,
  kind: "entry" | "universe",
): HTMLCanvasElement | null {
  const existing = document.getElementById(V197_STATIC_STARFIELD_ID) as HTMLCanvasElement | null;
  if (existing) return existing;
  const frameWindow = document.defaultView;
  const host = document.body;
  if (!frameWindow || !host) return null;

  const canvas = document.createElement("canvas");
  canvas.id = V197_STATIC_STARFIELD_ID;
  canvas.dataset.nurLayer = `${kind}-seeded-static-stars`;
  canvas.setAttribute("aria-hidden", "true");
  canvas.style.cssText = [
    "position:fixed",
    "inset:0",
    "width:100%",
    "height:100%",
    "z-index:0",
    "pointer-events:none",
    "contain:strict",
  ].join(";");
  host.prepend(canvas);

  const paint = () => {
    const width = Math.max(1, Math.round(frameWindow.innerWidth));
    const height = Math.max(1, Math.round(frameWindow.innerHeight));
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { alpha: true });
    if (!context) return;
    context.clearRect(0, 0, width, height);
    const minimum = kind === "entry" ? 92 : 110;
    const maximum = kind === "entry" ? 250 : 290;
    const count = Math.min(maximum, Math.max(minimum, Math.round((width * height) / 6_800)));
    let seed = ((width * 73856093) ^ (height * 19349663) ^ (kind === "entry" ? 0x4e5552 : 0x564197)) >>> 0;
    const random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    const colours = [
      [255, 241, 195],
      [255, 185, 91],
      [121, 226, 255],
      [210, 154, 255],
      [255, 145, 196],
    ] as const;
    for (let index = 0; index < count; index += 1) {
      const x = Math.floor(random() * width) + .5;
      const y = Math.floor(random() * height) + .5;
      const colour = colours[Math.floor(random() * colours.length)] ?? colours[0];
      const alpha = .18 + random() * .5;
      const bright = index % 17 === 0;
      context.fillStyle = `rgba(${colour[0]},${colour[1]},${colour[2]},${alpha})`;
      context.fillRect(x, y, bright ? 1.5 : 1, bright ? 1.5 : 1);
      if (bright) {
        context.strokeStyle = `rgba(${colour[0]},${colour[1]},${colour[2]},${alpha * .52})`;
        context.lineWidth = .5;
        context.beginPath();
        context.moveTo(x - 3, y + .5);
        context.lineTo(x + 4, y + .5);
        context.moveTo(x + .5, y - 3);
        context.lineTo(x + .5, y + 4);
        context.stroke();
      }
    }
    canvas.dataset.nurStarCount = String(count);
  };

  let resizeTimer: number | null = null;
  frameWindow.addEventListener("resize", () => {
    if (resizeTimer !== null) frameWindow.clearTimeout(resizeTimer);
    resizeTimer = frameWindow.setTimeout(() => {
      resizeTimer = null;
      paint();
    }, 160);
  }, { passive: true });
  paint();
  return canvas;
}

/** Keep the large canonical Entry brand inside the viewport while its auth
 * sheet is open. V197's compact-height grid otherwise lifts the header 46px,
 * clipping the Bodoni wordmark even though the auth card itself remains valid. */
export function ensureV197EntryPolish(document: Document): HTMLStyleElement {
  const existing = document.getElementById(V197_ENTRY_POLISH_STYLE_ID) as HTMLStyleElement | null;
  if (existing) {
    installV197StarSeals(document);
    ensureV197BlackGalaxy(document);
    ensureV197StarBrain(document);
    return existing;
  }
  const style = document.createElement("style");
  style.id = V197_ENTRY_POLISH_STYLE_ID;
  style.dataset.nurLayer = "v197-native-entry-polish";
  style.textContent = `
#nur-front-v61 .f4-brand-word,
#nur-front-v61 .f4-brand-sub {
  transform: none !important;
}
body.nur-v197-auth-open #nur-front-v61,
#nur-front-v61:has(#f4-sheet.open) {
  animation: none !important;
  transform: none !important;
  opacity: 1 !important;
}
body.nur-v197-auth-open #nur-front-v61 .f4-head {
  animation: none !important;
  transform: translateY(28px) !important;
}
#nur-front-v61:has(#f4-sheet.open) .f4-head {
  animation: none !important;
  transform: translateY(28px) !important;
}
@media (max-width: 600px) {
  body.nur-v197-auth-open #nur-front-v61 .f4-head,
  #nur-front-v61:has(#f4-sheet.open) .f4-head { transform: translateY(10px) !important; }
}
${V197_STAR_SEAL_CSS}
${V197_COSMIC_SKIN_CSS}
`;
  (document.body ?? document.head).append(style);
  installV197StarSeals(document);
  ensureV197BlackGalaxy(document);
  ensureV197StarBrain(document);

  const sheet = document.querySelector<HTMLElement>("#f4-sheet");
  const sync = () => document.body?.classList.toggle("nur-v197-auth-open", Boolean(sheet?.classList.contains("open")));
  const openBeforeCanonicalHandler = (event: Event) => {
    const target = event.target as Element | null;
    if (!target?.closest("#f4-begin, #f4-signin, #f4-what, #f4-about-begin, [data-switch]")) return;
    document.body?.classList.add("nur-v197-auth-open");
  };
  // Capture makes the clipping guard synchronous with the native V197 click,
  // while :has() above covers direct runtime state changes. The observer still
  // owns close/reset cleanup.
  document.addEventListener("click", openBeforeCanonicalHandler, true);
  sync();
  if (sheet && document.defaultView) {
    const observer = new document.defaultView.MutationObserver(sync);
    observer.observe(sheet, { attributes: true, attributeFilter: ["class"] });
  }
  return style;
}

export function ensureV197PremiumPolish(document: Document): HTMLStyleElement {
  const existing = document.getElementById(V197_PREMIUM_POLISH_STYLE_ID) as HTMLStyleElement | null;
  if (existing) {
    compactV197MiniStars(document);
    ensureStableMapWordmark(document);
    ensureV197InteractionBudget(document);
    ensureV197BlackGalaxy(document);
    ensureV197StarBrain(document);
    return existing;
  }
  const style = document.createElement("style");
  style.id = V197_PREMIUM_POLISH_STYLE_ID;
  style.dataset.nurLayer = "v197-native-premium-polish";
  style.textContent = `${V197_PREMIUM_POLISH_CSS}\n${V197_STAR_SEAL_CSS}\n${V197_COSMIC_SKIN_CSS}`;
  // V197 intentionally carries late style blocks inside its body. Appending
  // this corrective layer to the end of the body gives equal-specificity
  // `!important` rules deterministic precedence without modifying source.
  (document.body ?? document.head).append(style);
  compactV197MiniStars(document);
  ensureStableMapWordmark(document);
  ensureV197InteractionBudget(document);
  ensureV197BlackGalaxy(document);
  ensureV197StarBrain(document);
  return style;
}
