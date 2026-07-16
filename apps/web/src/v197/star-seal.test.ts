import {
  V197_CONTROL_STAR_SEAL_CLASS,
  V197_STATE_STAR_SEAL_CLASS,
  V197_STAR_SEAL_CLASS,
  V197_STAR_SEAL_SPRITE_ID,
  V197_STAR_SEAL_SYMBOL_ID,
  createV197StarSeal,
  installV197StarSeals,
} from "../bridge/v197StarSeal";

describe("V197 star seal", () => {
  beforeEach(() => {
    document.body.replaceChildren();
  });

  it("installs one shared detailed symbol and lightweight use instances", () => {
    document.body.innerHTML = `
      <button class="active"><span class="nur-exact-mini-host" data-nur-star-size="16"><span class="nur-star-module"></span></span></button>
      <button><span class="nur-exact-mini-host" data-nur-star-size="24"><span class="nur-star-module"></span></span></button>
    `;

    expect(installV197StarSeals(document)).toBe(2);
    expect(installV197StarSeals(document)).toBe(0);
    expect(document.querySelectorAll(`#${V197_STAR_SEAL_SPRITE_ID}`)).toHaveLength(1);
    expect(document.querySelectorAll(`#${V197_STAR_SEAL_SYMBOL_ID} path`).length).toBeGreaterThanOrEqual(16);
    expect(document.querySelectorAll(`.${V197_STAR_SEAL_CLASS} use`)).toHaveLength(2);
    expect(document.querySelector(".nur-v197-mini-star-lite")).toBeNull();
    expect(document.querySelector<HTMLElement>(".nur-exact-mini-host")?.dataset.nurStarSeal).toBe("authentic");
    expect(document.querySelector<SVGSVGElement>(`.${V197_STAR_SEAL_CLASS}`)?.dataset.nurStarTwinkle).toBe("true");
  });

  it("supports the canonical 12, 16, 20, 24, and 32 pixel sizes", () => {
    for (const size of [12, 16, 20, 24, 32] as const) {
      const seal = createV197StarSeal(document, size);
      expect(seal.classList.contains(`${V197_STAR_SEAL_CLASS}--${size}`)).toBe(true);
      expect(seal.getAttribute("width")).toBe(String(size));
      expect(seal.dataset.nurStarTwinkle).toBe("false");
    }
  });

  it("marks legacy icon shells and normalizes system seal sizes", () => {
    document.body.innerHTML = `
      <button class="universe-system-node active">
        <i class="nur-exact-icon-shell"><span class="nur-exact-mini-host"><span class="nur-star-module"></span></span></i>
      </button>
      <button class="clean-system-row">
        <i class="nur-exact-icon-shell nur-exact-mini-host"><span class="nur-star-module"></span></i>
      </button>
    `;

    expect(installV197StarSeals(document)).toBe(2);
    const hosts = document.querySelectorAll<HTMLElement>(".nur-exact-icon-shell");
    expect(hosts[0]?.dataset.nurAuthenticStarHost).toBe("true");
    expect(hosts[1]?.dataset.nurAuthenticStarHost).toBe("true");
    expect(hosts[0]?.querySelector(`.${V197_STAR_SEAL_CLASS}--24`)).not.toBeNull();
    expect(hosts[1]?.querySelector(`.${V197_STAR_SEAL_CLASS}--16`)).not.toBeNull();
  });

  it("uses authentic seals for primary and selected controls without duplicating them", () => {
    document.body.innerHTML = `
      <main id="nur-front-v61">
        <button class="f4-primary compact">Begin</button>
        <button class="thought-send-button">Send</button>
        <button class="clean-nav-button active"><span class="clean-nav-glyph">*</span><span>Today</span></button>
        <button class="clean-nav-button"><span class="clean-nav-glyph">*</span><span>Talk</span></button>
      </main>
    `;

    expect(installV197StarSeals(document)).toBe(3);
    expect(installV197StarSeals(document)).toBe(0);
    expect(document.querySelectorAll(`.${V197_CONTROL_STAR_SEAL_CLASS}`)).toHaveLength(2);
    expect(document.querySelectorAll(`.${V197_STATE_STAR_SEAL_CLASS}`)).toHaveLength(1);
    expect(document.querySelectorAll(`.${V197_CONTROL_STAR_SEAL_CLASS} use`)).toHaveLength(2);
    expect(document.querySelector(`.clean-nav-button.active .${V197_STATE_STAR_SEAL_CLASS}`)).not.toBeNull();

    const nav = document.querySelectorAll<HTMLElement>(".clean-nav-button");
    nav[0]?.classList.remove("active");
    nav[1]?.classList.add("active");
    expect(installV197StarSeals(document)).toBe(1);
    expect(nav[0]?.querySelector(`.${V197_STATE_STAR_SEAL_CLASS}`)).toBeNull();
    expect(nav[1]?.querySelector(`.${V197_STATE_STAR_SEAL_CLASS}`)).not.toBeNull();
  });
});
