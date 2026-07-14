/* ONE route-transition director — the V197 stage router reborn without iframes.
   Veil + galaxy burst + body-class choreography (nur-3d-entering) around
   navigation; exposes reveal() for the auth→universe cinematic. */
import { createContext, useCallback, useContext, useRef, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useGalaxy } from "../galaxy/GalaxyProvider";

type Director = {
  go: (to: string, opts?: { burst?: boolean }) => void;
  reveal: (to: string) => void; // entry → universe cinematic
};
const Ctx = createContext<Director | null>(null);

export function TransitionDirector({ children }: { children: ReactNode }) {
  const nav = useNavigate();
  const galaxy = useGalaxy();
  const veilRef = useRef<HTMLDivElement>(null);
  const busy = useRef(false);
  const queued = useRef<{ to: string; opts?: { burst?: boolean } } | null>(null);

  const go = useCallback((to: string, opts?: { burst?: boolean }) => {
    if (busy.current) { queued.current = { to, opts }; return; }
    busy.current = true;
    const veil = veilRef.current;
    veil?.classList.add("is-active");
    if (opts?.burst) galaxy?.burst(innerWidth / 2, innerHeight / 2, 0.35);
    setTimeout(() => {
      nav(to);
      requestAnimationFrame(() => {
        veil?.classList.remove("is-active");
        busy.current = false;
        const q = queued.current;
        queued.current = null;
        if (q) go(q.to, q.opts);
      });
    }, 240);
  }, [nav, galaxy]);

  const reveal = useCallback((to: string) => {
    document.body.classList.add("nur-3d-entering");
    galaxy?.burst(innerWidth / 2, innerHeight / 2, 1);
    setTimeout(() => {
      nav(to);
      setTimeout(() => document.body.classList.remove("nur-3d-entering"), 750);
    }, 620);
  }, [nav, galaxy]);

  return (
    <Ctx.Provider value={{ go, reveal }}>
      {children}
      <div id="nur-route-veil" ref={veilRef} aria-hidden="true" />
    </Ctx.Provider>
  );
}
export function useDirector(): Director {
  const d = useContext(Ctx);
  if (!d) throw new Error("useDirector outside TransitionDirector");
  return d;
}
