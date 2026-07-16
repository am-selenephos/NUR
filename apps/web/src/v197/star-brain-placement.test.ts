import { placeV197StarBrainHost } from "../bridge/v197StarBrain";

describe("V197 star brain placement", () => {
  beforeEach(() => {
    document.body.className = "universe-edition";
    document.body.replaceChildren();
  });

  it("replaces the Map MasterStar fallback with the one exact brain host", () => {
    document.body.innerHTML = `
      <main id="nur-front-v61">
        <section id="page-universe-map" class="active">
          <div class="lens-map-master"><div class="spark f4-master-star nur-star-module"></div></div>
        </section>
      </main>
    `;

    placeV197StarBrainHost(document);
    const mapHost = document.querySelector<HTMLElement>(".lens-map-master");
    const brain = mapHost?.querySelector<HTMLElement>("#front-nur-star");
    expect(brain?.dataset.nurSurface).toBe("map");
    expect(mapHost?.dataset.nurLegacyMasterStar).toBe("removed");
    expect(mapHost?.querySelector(".spark, .f4-master-star, .nur-star-module")).toBeNull();
    expect(document.querySelectorAll("#front-nur-star")).toHaveLength(1);
  });
});
