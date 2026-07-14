import { describe, expect, it } from "vitest";
import { CORE_COPY, CRITICAL_COPY, LOCALE_META, POLISHED_BETA_LOCALES, SUPPORTED_LOCALES, dirForLocale, resolveLocale, writingPreferenceForLocale } from "./i18n";

function collectLeaves(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (typeof value === "function") return [String(value(2))];
  if (!value || typeof value !== "object") return [];
  return Object.values(value).flatMap(collectLeaves);
}

describe("i18n readiness", () => {
  it("keeps critical UI copy for every declared locale", () => {
    expect(SUPPORTED_LOCALES).toEqual([
      "en", "ur", "hi", "bn", "pa", "ar", "fa", "tr", "id", "ms",
      "zh-Hans", "zh-Hant", "ja", "ko", "vi", "th", "fil", "ta", "te",
      "mr", "gu", "kn", "ml", "ru", "uk", "pl", "de", "fr", "es", "pt",
      "it", "nl", "sv", "ro", "sw",
    ]);
    for (const locale of SUPPORTED_LOCALES) {
      expect(CORE_COPY[locale].askPlaceholder.length).toBeGreaterThan(0);
      expect(CORE_COPY[locale].privateBoundary.length).toBeGreaterThan(0);
      expect(collectLeaves(CRITICAL_COPY[locale]).every(text => text.trim().length > 0)).toBe(true);
      expect(CRITICAL_COPY[locale].talk.title).toBeTruthy();
      expect(CRITICAL_COPY[locale].systems.mapSubtitle).toBeTruthy();
      expect(CRITICAL_COPY[locale].capsule.shareTitle).toBeTruthy();
      expect(CRITICAL_COPY[locale].capsule.createContextCapsule).toBeTruthy();
    }
  });

  it("resolves fallback, RTL, and Roman Urdu preference honestly", () => {
    expect(resolveLocale("zh-CN")).toBe("zh-Hans");
    expect(resolveLocale("pt-BR")).toBe("pt");
    expect(dirForLocale("ar")).toBe("rtl");
    expect(dirForLocale("fa")).toBe("rtl");
    expect(dirForLocale("ur")).toBe("rtl");
    expect(dirForLocale("en")).toBe("ltr");
    expect(writingPreferenceForLocale("ur-PK")).toBe("roman");
    expect(writingPreferenceForLocale("ar")).toBe("script");
  });

  it("labels polished beta locales separately from draft locales", () => {
    expect(POLISHED_BETA_LOCALES).toEqual(["en", "ur", "hi", "fa", "ar", "es", "fr", "zh-Hans"]);
    const polished = LOCALE_META.filter(row => row.status === "polished_beta").map(row => row.locale);
    expect(polished).toEqual(Array.from(POLISHED_BETA_LOCALES));
    expect(LOCALE_META.find(row => row.locale === "bn")?.status).toBe("draft_unreviewed");
  });
});
