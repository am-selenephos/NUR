/* Source-faithful authenticated shell (mandate B4): #nur-front-v61.nur-interior
   > .nur-shell > rail / main(topbar+viewport+composer+mobiletabs) / context.
   Body class lifecycle per B3. Galaxy mode uses REAL names per B9. */
import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import UniverseRail from "./shell/UniverseRail";
import UniverseTopbar from "./shell/UniverseTopbar";
import UniverseContextRail from "./shell/UniverseContextRail";
import GlobalComposer from "./shell/GlobalComposer";
import MobileTabs from "./shell/MobileTabs";
import ScopeModal from "./shell/ScopeModal";
import AddSystemModal from "./shell/AddSystemModal";
import { useGalaxy } from "../../galaxy/GalaxyProvider";
import { useWorldFocus } from "../../app/worldFocus";
import { useOrbit } from "../../lib/orbitState";
import { V197_GLOBAL_COMPOSER_ROUTES } from "../../v197/contract";

export default function UniverseLayout() {
  const galaxy = useGalaxy();
  const wf = useWorldFocus();
  const orbit = useOrbit();
  const { pathname } = useLocation();
  const page = pathname.replace("/", "") || "today";
  const showGlobalComposer = (V197_GLOBAL_COMPOSER_ROUTES as readonly string[]).includes(pathname);
  const [scopeOpen, setScopeOpen] = useState(false);

  useEffect(() => { orbit.hydrate(); }, [orbit]);

  useEffect(() => {
    document.body.classList.remove("front-v61-active");
    document.body.classList.add("universe-edition", "nur-universe-active");
    return () => document.body.classList.remove("universe-edition", "nur-universe-active");
  }, []);

  useEffect(() => {
    galaxy?.setMode(wf.focus !== "universe" ? wf.focus : page);
  }, [page, wf.focus, galaxy]);

  useEffect(() => {
    document.querySelector<HTMLElement>(".nur-viewport")?.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div id="nur-front-v61" className="nur-interior" data-testid="universe-root">
      <div className="nur-shell">
        <aside className="nur-rail clean-left-rail" aria-label="NUR primary navigation">
          <UniverseRail />
        </aside>

        <main className="nur-main">
          <UniverseTopbar onScopeOpen={() => setScopeOpen(true)} />
          <section className="nur-viewport" aria-live="polite">
            <Outlet />
          </section>
          {showGlobalComposer ? <GlobalComposer /> : null}
          <MobileTabs />
        </main>

        <aside className="nur-context clean-right-rail v172-context-rail" aria-label="NUR context">
          <UniverseContextRail onScopeOpen={() => setScopeOpen(true)} />
        </aside>
      </div>

      <ScopeModal open={scopeOpen} onClose={() => setScopeOpen(false)} />
      <AddSystemModal open={orbit.addSystemOpen} onClose={() => orbit.setAddSystemOpen(false)} />
    </div>
  );
}
