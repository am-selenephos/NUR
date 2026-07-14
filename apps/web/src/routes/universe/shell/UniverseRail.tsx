/* Exact V197 left rail (mandate B5): source class stacks, groups, footer. */
import { useLocation } from "react-router-dom";
import { useDirector } from "../../../app/TransitionDirector";
import { useWorldFocus } from "../../../app/worldFocus";
import { useOrbit } from "../../../lib/orbitState";
import { V197_NAV_ITEMS, V197_TOOL_ITEMS } from "../../../v197/contract";

export default function UniverseRail() {
  const { pathname } = useLocation();
  const director = useDirector();
  const wf = useWorldFocus();
  const orbit = useOrbit();
  const page = pathname.replace("/", "") || "today";

  const goTool = (tool: typeof V197_TOOL_ITEMS[number]) => {
    if (tool.key === "research") { wf.openDeepResearch(); return; }
    wf.setFocus(tool.key);
    if (pathname !== tool.path) director.go(tool.path);
  };

  return (
    <>
      <section className="clean-rail-section" aria-label="Personal Orbit">
        <p className="clean-section-label">Personal Orbit</p>
        <nav className="clean-orbit-nav" aria-label="Personal Orbit navigation">
          {V197_NAV_ITEMS.map(n => (
            <button key={n.page} type="button" data-page={n.page} data-testid={`pw-rail-${n.page}`}
                    className={`clean-nav-button${page === n.page ? " active" : ""}`}
                    aria-current={page === n.page ? "page" : undefined}
                    onClick={() => director.go(n.path)}>
              <span className="clean-nav-glyph">{n.glyph}</span>
              <span className="clean-nav-title">{n.title}</span>
              <span className="clean-nav-note">{n.note}</span>
            </button>
          ))}
        </nav>
      </section>
      <div className="clean-rule" />
      <section className="clean-rail-section" aria-label="Universe tools">
        <p className="clean-section-label">Universe Tools</p>
        <div className="clean-tool-list">
          {V197_TOOL_ITEMS.map(t => (
            <button key={t.key} type="button" className="clean-tool-button" data-testid={t.testId}
                    onClick={() => goTool(t)}>
              <span className="clean-tool-glyph">{t.glyph}</span>
              <span><b>{t.title}</b><small>{t.note}</small></span>
            </button>
          ))}
        </div>
      </section>
      <div className="clean-rule" />
      <section className="clean-rail-section clean-systems-section" aria-label="Star Systems">
        <p className="clean-section-label">Star Systems</p>
        <div className="clean-system-list">
          {orbit.systems.map(s => (
            <button key={s.name} type="button" data-page="systems" data-system={s.name}
                    data-testid={`pw-rail-sys-${s.name.toLowerCase().replace(/\s+/g, "-")}`}
                    className={`clean-system-row${orbit.activeSystem === s.name ? " active" : ""}${s.suggested ? " suggested" : ""}`}
                    aria-pressed={orbit.activeSystem === s.name}
                    title={s.suggested ? "A suggested sky — select to create it in your Orbit" : undefined}
                    onClick={async () => {
                      if (s.suggested) { try { await orbit.addSystem(s.name, s.description); } catch { return; } }
                      orbit.setActiveSystem(s.name);
                      if (page !== "systems") director.go("/systems");
                    }}>
              <i>{s.suggested ? "◌" : "✦"}</i><span>{s.name}</span>
            </button>
          ))}
        </div>
      </section>
      <div className="clean-orbit-footer">
        <span>Private by default</span>
        <b>Your Orbit</b>
        <p>Nothing leaves this space without a choice you can see.</p>
      </div>
    </>
  );
}
