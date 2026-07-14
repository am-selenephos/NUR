/* Exact V197 topbar (mandate B6): source classes, real tab semantics. */
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { useLocation } from "react-router-dom";
import ExactMiniStar from "../../../components/ExactMiniStar";
import { useAuth } from "../../../app/AuthProvider";
import { useDirector } from "../../../app/TransitionDirector";
import { useGalaxy } from "../../../galaxy/GalaxyProvider";
import { useWorldFocus, type WorldFocus } from "../../../app/worldFocus";
import { api } from "../../../lib/api";
import { nur } from "../../../lib/api";
import { V197_WORLD_TABS } from "../../../v197/contract";

type SearchHit = { kind: string; label: string; route: string };

export default function UniverseTopbar({ onScopeOpen }: { onScopeOpen: () => void }) {
  const { user, refresh } = useAuth();
  const director = useDirector();
  const galaxy = useGalaxy();
  const wf = useWorldFocus();
  const { pathname } = useLocation();
  const [menu, setMenu] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const activePath = useMemo(() => {
    if (pathname === "/systems") return "/universe";
    return V197_WORLD_TABS.find(t => pathname === t.path || pathname.startsWith(`${t.path}/`))?.path ?? "";
  }, [pathname]);

  useEffect(() => {
    if (!menu) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenu(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [menu]);

  async function search() {
    const q = query.trim();
    if (!q) { setHits([]); setSearchOpen(false); return; }
    const next = (await nur.universeSearch(q, 8)).map(hit => ({
      kind: hit.kind,
      label: hit.label,
      route: hit.route,
    }));
    setHits(next);
    setSearchOpen(true);
  }

  async function leaveTheSky() {
    await api.logout();
    await refresh();
    director.go("/", { burst: true });
  }

  return (
    <header className="nur-topbar">
      <div className="universe-top-left">
        <div className="universe-nav-tabs" role="tablist" aria-label="Universe view">
          {V197_WORLD_TABS.map(t => (
            <button key={t.focus} type="button" role="tab" data-world-tab={t.focus} aria-selected={activePath === t.path}
                    className={activePath === t.path ? "active" : ""}
                    onClick={() => { wf.setFocus(t.focus as WorldFocus); director.go(t.path); }}>
              <span aria-hidden="true" className="universe-tab-glyph">{t.glyph}</span><span>{t.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="universe-top-tools">
        <label className="universe-search" aria-label="Search owned NUR rows">
          <span>⌕</span>
          <input id="universe-search" placeholder="Search NUR, system"
                 value={query}
                 onChange={e => setQuery(e.target.value)}
                 onFocus={() => hits.length > 0 && setSearchOpen(true)}
                 onKeyDown={e => e.key === "Enter" && search()} />
        </label>
        <button id="deep-research-button" className="universe-deep" type="button"
                onClick={wf.openDeepResearch}>✧ Deep research <span>⌄</span></button>
        <button id="scope-open" className="nur-scope" type="button" onClick={onScopeOpen}>✦ Private</button>
        <button id="burst-btn" className="nur-iconbtn" type="button" aria-label="Wake the sky"
                onClick={() => galaxy?.burst(innerWidth / 2, innerHeight * 0.4, 0.8)}>wake sky</button>
        <button className="nur-user nur-v136-v89-mini-host nur-exact-icon-shell" type="button" data-testid="user-star"
                aria-label={user ? `${user.profile.chosen_name} — your orbit` : "Your orbit"}
                aria-expanded={menu} onClick={() => setMenu(v => !v)}>
          <ExactMiniStar size="nur-mini-18" />
        </button>
        {menu && createPortal(
          <div className="nur-user-menu clean-audit-card" role="menu"
               style={{ position: "fixed", top: 70, right: 18, width: 250, zIndex: 320, padding: 18 }}>
            <p className="v172-eyebrow">{user?.profile.chosen_name}</p>
            <button className="v172-inline-action" type="button" role="menuitem"
                    onClick={() => { setMenu(false); director.go("/settings"); }}>Settings <span>→</span></button>
            <button className="v172-inline-action" data-testid="logout" type="button" role="menuitem"
                    onClick={leaveTheSky}>Leave the sky <span>→</span></button>
          </div>,
          document.body,
        )}
        {searchOpen && createPortal(
          <div className="nur-search-results clean-audit-card" role="dialog" aria-label="Scoped search results">
            <p className="v172-eyebrow">Scoped search</p>
            {hits.length === 0 && <p>No owned rows matched. Nothing external was fetched.</p>}
            {hits.map((hit, index) => (
              <button key={`${hit.kind}-${index}`} type="button" onClick={() => { setSearchOpen(false); director.go(hit.route); }}>
                <span>{hit.kind}</span><b>{hit.label}</b>
              </button>
            ))}
          </div>,
          document.body,
        )}
      </div>
    </header>
  );
}
