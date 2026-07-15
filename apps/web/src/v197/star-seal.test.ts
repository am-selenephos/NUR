import {
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
});
