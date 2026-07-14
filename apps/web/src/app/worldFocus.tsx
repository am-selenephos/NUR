/* Shared WorldFocus state (mandate B10): topbar tabs, rail tools, Systems
   commands and Deep Research converge here. Research opening announces and
   focuses the real saved-question field — no fake web search exists. */
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useDirector } from "./TransitionDirector";

export type WorldFocus =
  | "universe" | "map" | "orbits" | "timeline" | "insights"
  | "consult" | "research" | "community" | "web";

type Ctx = {
  focus: WorldFocus;
  setFocus: (f: WorldFocus) => void;
  openDeepResearch: () => void;
  announce: (msg: string) => void;
};
const C = createContext<Ctx | null>(null);

export function WorldFocusProvider({ children }: { children: ReactNode }) {
  const [focus, setFocus] = useState<WorldFocus>("universe");
  const director = useDirector();
  const loc = useLocation();

  const announce = useCallback((msg: string) => {
    const el = document.getElementById("nur-live-region");
    if (el) { el.textContent = ""; requestAnimationFrame(() => { el.textContent = msg; }); }
  }, []);

  const openDeepResearch = useCallback(() => {
    const after = () => {
      setFocus("research");
      requestAnimationFrame(() => {
        document.getElementById("page-universe-research")?.scrollIntoView({ block: "start", behavior: "smooth" });
        (document.getElementById("research-query") as HTMLInputElement | null)?.focus();
        announce("Research field opened. Outside context is saved as a private question, not treated as truth.");
      });
    };
    if (loc.pathname !== "/universe/research") { director.go("/universe/research"); setTimeout(after, 420); }
    else after();
  }, [loc.pathname, director, announce]);

  return <C.Provider value={{ focus, setFocus, openDeepResearch, announce }}>{children}</C.Provider>;
}
export function useWorldFocus(): Ctx {
  const v = useContext(C);
  if (!v) throw new Error("useWorldFocus outside provider");
  return v;
}
