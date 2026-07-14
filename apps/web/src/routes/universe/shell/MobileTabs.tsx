/* Source mobile tabs: same clean-orbit-nav DOM inside nav.mobile-tabs. */
import { useLocation } from "react-router-dom";
import { useDirector } from "../../../app/TransitionDirector";
import { V197_NAV_ITEMS } from "../../../v197/contract";

export default function MobileTabs() {
  const { pathname } = useLocation();
  const director = useDirector();
  const page = pathname.replace("/", "") || "today";
  return (
    <nav className="mobile-tabs" aria-label="Mobile navigation">
      <div className="clean-orbit-nav" aria-label="Personal Orbit navigation">
        {V197_NAV_ITEMS.map(n => (
          <button key={n.page} type="button" data-page={n.page} data-testid={`mobile-tab-${n.page}`}
                  className={`clean-nav-button${page === n.page ? " active" : ""}`}
                  onClick={() => director.go(n.path)}>
            <span className="clean-nav-glyph">{n.glyph}</span>
            <span className="clean-nav-title">{n.title}</span>
            <span className="clean-nav-note">{n.note}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
