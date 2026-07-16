import type { Locator } from "@playwright/test";

export const V197_REQUIRED_VIEWPORTS = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 844, height: 390 },
  { width: 768, height: 1024 },
  { width: 1024, height: 768 },
  { width: 1280, height: 720 },
  { width: 1366, height: 768 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1080 },
  { width: 2560, height: 1440 },
] as const;

export type V197Rect = {
  selector: string;
  left: number;
  right: number;
  top: number;
  bottom: number;
  width: number;
  height: number;
};

export type V197ViewportAudit = {
  documentWidth: number;
  viewportWidth: number;
  escapedControls: V197Rect[];
  undersizedTouchTargets: V197Rect[];
};

export async function settleV197Layout(root: Locator): Promise<void> {
  await root.evaluate(() => new Promise<void>(resolve => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  }));
}

export async function auditV197Viewport(root: Locator): Promise<V197ViewportAudit> {
  return root.evaluate(element => {
    const document = element.ownerDocument;
    const frameWindow = document.defaultView;
    if (!frameWindow) throw new Error("V197 frame has no window");

    const visible = (target: HTMLElement) => {
      const style = getComputedStyle(target);
      const bounds = target.getBoundingClientRect();
      return style.display !== "none"
        && style.visibility !== "hidden"
        && Number(style.opacity) > 0
        && bounds.width > 0
        && bounds.height > 0
        && !target.closest("[hidden], [aria-hidden='true']");
    };
    const describe = (target: HTMLElement): V197Rect => {
      const bounds = target.getBoundingClientRect();
      const identity = target.id
        ? `#${target.id}`
        : `${target.tagName.toLowerCase()}.${String(target.className).trim().replace(/\s+/g, ".")}`;
      return {
        selector: identity,
        left: bounds.left,
        right: bounds.right,
        top: bounds.top,
        bottom: bounds.bottom,
        width: bounds.width,
        height: bounds.height,
      };
    };

    const controls = Array.from(document.querySelectorAll<HTMLElement>(
      "a[href], button, input, textarea, select, summary, [role='button'], [tabindex]:not([tabindex='-1'])",
    )).filter(visible);
    const touchControls = controls.filter(target => target.matches([
      ".mobile-tabs button",
      ".global-composer button",
      ".nur-topbar button",
      ".f4-actions button",
      ".f4-sheet button",
      ".nur-adjunct-back",
      ".nur-adjunct-button",
    ].join(",")));

    return {
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: frameWindow.innerWidth,
      escapedControls: controls
        .filter(target => {
          const bounds = target.getBoundingClientRect();
          return bounds.left < -1 || bounds.right > frameWindow.innerWidth + 1;
        })
        .map(describe),
      undersizedTouchTargets: frameWindow.innerWidth <= 900
        ? touchControls.filter(target => {
            const bounds = target.getBoundingClientRect();
            return bounds.width < 43.5 || bounds.height < 43.5;
          }).map(describe)
        : [],
    };
  });
}

export async function visibleV197Rects(root: Locator, selector: string): Promise<V197Rect[]> {
  return root.evaluate((element, targetSelector) => Array.from(
    element.ownerDocument.querySelectorAll<HTMLElement>(targetSelector),
  ).flatMap(target => {
    const style = getComputedStyle(target);
    const bounds = target.getBoundingClientRect();
    if (style.display === "none" || style.visibility === "hidden" || bounds.width <= 0 || bounds.height <= 0) {
      return [];
    }
    return [{
      selector: target.id ? `#${target.id}` : `${target.tagName.toLowerCase()}.${String(target.className)}`,
      left: bounds.left,
      right: bounds.right,
      top: bounds.top,
      bottom: bounds.bottom,
      width: bounds.width,
      height: bounds.height,
    }];
  }), selector);
}

export function overlappingV197Pairs(rects: readonly V197Rect[], tolerance = 1): string[] {
  const overlaps: string[] = [];
  for (let left = 0; left < rects.length; left += 1) {
    for (let right = left + 1; right < rects.length; right += 1) {
      const a = rects[left]!;
      const b = rects[right]!;
      if (
        a.left < b.right - tolerance
        && a.right > b.left + tolerance
        && a.top < b.bottom - tolerance
        && a.bottom > b.top + tolerance
      ) {
        overlaps.push(`${a.selector} <> ${b.selector}`);
      }
    }
  }
  return overlaps;
}

export async function v197CenterDelta(
  root: Locator,
  firstSelector: string,
  secondSelector: string,
): Promise<number> {
  return root.evaluate((element, selectors) => {
    const center = (selector: string) => {
      const target = element.ownerDocument.querySelector<HTMLElement>(selector);
      if (!target) throw new Error(`Missing center target: ${selector}`);
      const bounds = target.getBoundingClientRect();
      return bounds.left + bounds.width / 2;
    };
    return Math.abs(center(selectors.firstSelector) - center(selectors.secondSelector));
  }, { firstSelector, secondSelector });
}
