/* Static isolation guarantee (mandate B2): every rule in each generated sheet
   is bound to its stage class; neither stage can style the other. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function topLevelSelectors(cssRaw: string): string[] {
  const css = cssRaw.replace(/\/\*[\s\S]*?\*\//g, "");
  const out: string[] = [];
  let depth = 0, buf = "", inAt: string | null = null;
  for (let i = 0; i < css.length; i++) {
    const ch = css[i];
    if (ch === "{") {
      const sel = buf.trim();
      if (depth === 0) {
        if (sel.startsWith("@")) inAt = sel.split(/[\s(]/)[0];
        else out.push(sel);
      } else if (depth >= 1 && inAt === "@media" && !sel.startsWith("@")) {
        out.push(sel);
      }
      depth++; buf = "";
    } else if (ch === "}") { depth--; if (depth === 0) inAt = null; buf = ""; }
    else buf += ch;
  }
  return out.filter(Boolean);
}
function splitTop(sel: string): string[] {
  const parts: string[] = []; let depth = 0, buf = "";
  for (const ch of sel) {
    if (ch === "(") depth++;
    if (ch === ")") depth--;
    if (ch === "," && depth === 0) { parts.push(buf); buf = ""; } else buf += ch;
  }
  parts.push(buf);
  return parts;
}
const ok = (sel: string, scope: string) =>
  splitTop(sel).every(s => {
    const t = s.trim();
    return t.startsWith(scope) || t.startsWith("@") || t === "" ||
      /^(from|to|\d+%)/.test(t);
  });

describe("v197 stage isolation", () => {
  it("entry sheet only fires under body.front-v61-active", () => {
    const css = readFileSync(resolve(process.cwd(), "src/styles/v197-entry-scoped.css"), "utf8");
    const bad = topLevelSelectors(css).filter(s => !ok(s, "body.front-v61-active"));
    if (bad.length) console.log("ENTRY OFFENDERS:", bad.slice(0, 6));
    expect(bad).toEqual([]);
  });
  it("universe sheet only fires under body.universe-edition", () => {
    const css = readFileSync(resolve(process.cwd(), "src/styles/v197-universe-scoped.css"), "utf8");
    const bad = topLevelSelectors(css).filter(s => !ok(s, "body.universe-edition"));
    if (bad.length) console.log("UNIVERSE OFFENDERS:", bad.slice(0, 6));
    expect(bad).toEqual([]);
  });
});
