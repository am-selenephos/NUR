/* V197 entry stage: cinematic intro (#intro) → f4 front page → auth sheet with
   signup / signin / onboarding / about / success modes — wired to the REAL
   Phase 0 auth API (cookies + CSRF). No iframes, no mock persistence. */
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import MasterStar from "../components/MasterStar";
import NURWordmark from "../components/NURWordmark";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../app/AuthProvider";
import { useDirector } from "../app/TransitionDirector";
import { useOrbit } from "../lib/orbitState";
import { useGalaxy } from "../galaxy/GalaxyProvider";

type Mode = "signup" | "signin" | "onboarding" | "about" | "success";
const DIRECTIONS = ["my mind", "my work", "my body", "my money", "my life direction"];

export default function Landing() {
  const [params] = useSearchParams();
  const loc = useLocation();
  const { refresh } = useAuth();
  const director = useDirector();
  const orbit = useOrbit();
  const galaxy = useGalaxy();

  const [introDone, setIntroDone] = useState(() => sessionStorage.getItem("nur.introPlayed") === "1");
  const [sheetOpen, setSheetOpen] = useState(params.get("sheet") !== null || loc.pathname === "/auth");
  const [mode, setMode] = useState<Mode>(params.get("sheet") === "signin" || loc.pathname === "/auth" ? "signin" : "signup");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chosenDir, setChosenDir] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const wordmarkRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.classList.add("front-v61-active");
    document.body.classList.remove("universe-edition", "nur-universe-active");
    return () => document.body.classList.remove("front-v61-active");
  }, []);

  /* intro choreography — timings from the V115 runtime */
  useEffect(() => {
    if (introDone) return;
    const t1 = setTimeout(() => document.getElementById("iNur")?.classList.add("show"), 1400);
    const t2 = setTimeout(() => {
      galaxy?.wordmarkBurst(wordmarkRef.current?.getBoundingClientRect() ?? null);
      document.getElementById("iSpark")?.classList.add("explode");
    }, 3050);
    const t3 = setTimeout(() => document.getElementById("intro")?.classList.add("fade"), 3550);
    const t4 = setTimeout(() => { setIntroDone(true); sessionStorage.setItem("nur.introPlayed", "1"); }, 5600);
    return () => [t1, t2, t3, t4].forEach(clearTimeout);
  }, [introDone, galaxy]);

  const open = (m: Mode) => { setMode(m); setError(null); setSheetOpen(true); };

  async function submitSignup(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setPending(true); setError(null);
    const f = new FormData(e.currentTarget);
    try {
      await api.register({
        chosen_name: String(f.get("display_name") || ""),
        email: String(f.get("email") || ""),
        password: String(f.get("new_password") || ""),
        consent: f.get("privacy_consent") === "on",
      });
      setMode("onboarding");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something drifted. Try again.");
    } finally { setPending(false); }
  }

  async function submitSignin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setPending(true); setError(null);
    const f = new FormData(e.currentTarget);
    try {
      await api.login({ email: String(f.get("email") || ""), password: String(f.get("password") || "") });
      await refresh();
      director.reveal("/today");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something drifted. Try again.");
    } finally { setPending(false); }
  }

  async function finishOnboarding() {
    if (chosenDir) orbit.setDirection(chosenDir);
    setMode("success");
  }
  async function returnToSky() {
    await refresh();
    director.reveal("/today");
  }

  return (
    <>
      {!introDone && (
        <div id="intro">
          <div className="i-txt" id="iTxt">
            <div className="i-center">
              <MasterStar variant="intro" id="iSpark" />
              <div className="i-nur-wrap" id="iNur" ref={wordmarkRef}>
                <NURWordmark variant="intro" />
              </div>
            </div>
            <div className="i-sub" id="iSub" aria-hidden="true" />
          </div>
        </div>
      )}

      <section id="nur-front-v61" aria-label="NUR front page" style={{ display: "grid" }}>
        <header className="f4-head">
          <button className="f4-brand" type="button" aria-label="NUR home">
            <span className="f4-brand-star" aria-hidden="true"><MasterStar variant="brand" /></span>
            <span className="f4-brand-copy">
              <span className="f4-brand-word">NUR</span>
              <span className="f4-brand-sub">Neural Upgrade Rewiring</span>
            </span>
          </button>
          <button className="f4-signin" type="button" data-testid="tab-login" onClick={() => open("signin")}>
            I already have an Orbit
          </button>
        </header>

        <main className="f4-stage">
          <section className="f4-copy">
            <p className="f4-eyebrow">the thoughts you repeat become your destiny.</p>
            <h1 className="f4-title">There is a universe <br />inside your <em>mind.</em></h1>
            <p className="f4-lede">Every thought leaves a trace. Every spark can become a pathway. NUR helps you notice the patterns shaping your life — then move one real thing with clarity.</p>
            <div className="f4-actions">
              <button className="f4-primary" type="button" data-testid="tab-register" onClick={() => open("signup")}>
                Begin your Orbit <span aria-hidden="true">→</span>
              </button>
              <button className="f4-link" type="button" data-testid="landing-about" onClick={() => open("about")}>how does NUR work?</button>
            </div>
            <p className="f4-privacy"><i>✦</i><span><b>Your inner universe is private by default.</b> Nothing becomes shared, remembered, or used for learning unless you choose it.</span></p>
          </section>

          <aside className="f4-orbit" aria-hidden="true">
            <span className="f4-ring" /><span className="f4-ring two" /><span className="f4-ring three" />
            <div className="f4-core" id="f4-core"><MasterStar variant="hero" /></div>
            <span className="f4-neural-node n1">signal</span>
            <span className="f4-neural-node n2">memory</span>
            <span className="f4-neural-node n3">intention</span>
            <span className="f4-neural-node n4">action</span>
            <span className="f4-orbit-star a"><b>talk</b><small>turn a signal into language</small></span>
            <span className="f4-orbit-star b"><b>journal</b><small>let a thought leave a trace</small></span>
            <span className="f4-orbit-star c"><b>plan</b><small>make a pattern into movement</small></span>
            <span className="f4-orbit-star d"><b>systems</b><small>let sparks become shared knowledge</small></span>
            <p className="f4-orbit-note">A universe inside your mind. <b>Your Orbit</b> is where its signals become visible.</p>
          </aside>
        </main>

        <footer className="f4-foot">
          <span>Not a feed. Not a performance. A place to notice the patterns inside you — then move with them.</span>
          <span>Built for conscious rewiring.</span>
        </footer>

        <aside className={`f4-sheet${sheetOpen ? " open" : ""}`} id="f4-sheet" role="dialog"
               aria-modal="true" aria-label="Create or enter your Orbit" {...(sheetOpen ? {} : { inert: "" as never })}>
          <div className="f4-status" aria-live="polite">{error ?? ""}</div>
          <div className="f4-sheet-head">
            <div>
              <p className="f4-kicker">{mode === "signin" ? "welcome back" : mode === "onboarding" ? "first direction" : mode === "success" ? "held" : "first signal"}</p>
              <h2>{mode === "signin" ? "Enter your Orbit." : mode === "about" ? "How NUR works." : mode === "onboarding" ? "One honest direction." : mode === "success" ? "Your first constellation is waiting." : "Create your Orbit."}</h2>
            </div>
            <button className="f4-close" type="button" data-testid="auth-close" aria-label="Close this panel" onClick={() => setSheetOpen(false)}>×</button>
          </div>

          {error && <p className="f4-desc" role="alert" style={{ color: "#ffb3a1" }}>{error}</p>}

          <section className={`f4-mode${mode === "signup" ? " active" : ""}`} data-mode="signup">
            <p className="f4-desc">Start with one private place where thoughts can become patterns instead of noise. Choose a name that feels like yours.</p>
            <form className="f4-form" onSubmit={submitSignup} autoComplete="on">
              <div className="f4-field"><label htmlFor="f4-name">chosen name</label>
                <input id="f4-name" name="display_name" ref={nameRef} autoComplete="name" placeholder="what should NUR call you?" required type="text" /></div>
              <div className="f4-field"><label htmlFor="f4-email">email</label>
                <input id="f4-email" name="email" autoComplete="email" inputMode="email" placeholder="you@example.com" required type="email" /></div>
              <div className="f4-field"><label htmlFor="f4-password">password</label>
                <input id="f4-password" name="new_password" autoComplete="new-password" minLength={8} placeholder="at least 8 characters" required type="password" /></div>
              <label className="f4-consent">
                <input id="f4-consent-check" data-testid="consent" name="privacy_consent" required type="checkbox" />
                <span>I understand that my inner world remains private by default, and I choose what becomes shared or contributes to learning.</span>
              </label>
              <button className="f4-primary f4-submit" data-testid="auth-submit" type="submit" disabled={pending}>
                {pending ? "Igniting…" : <>Create my Orbit <span aria-hidden="true">→</span></>}
              </button>
            </form>
            <p className="f4-switch">Already began? <button type="button" data-testid="auth-switch-signin" onClick={() => open("signin")}>Enter your Orbit</button></p>
          </section>

          <section className={`f4-mode${mode === "signin" ? " active" : ""}`} data-mode="signin">
            <p className="f4-desc">Your Orbit returns exactly where you left it.</p>
            <form className="f4-form" onSubmit={submitSignin} autoComplete="on">
              <div className="f4-field"><label htmlFor="f4-signin-email">email</label>
                <input id="f4-signin-email" name="email" autoComplete="email" inputMode="email" placeholder="you@example.com" required type="email" /></div>
              <div className="f4-field"><label htmlFor="f4-signin-password">password</label>
                <input id="f4-signin-password" name="password" autoComplete="current-password" placeholder="your password" required type="password" /></div>
              <button className="f4-primary f4-submit" data-testid="auth-submit" type="submit" disabled={pending}>
                {pending ? "Returning…" : <>Enter my Orbit <span aria-hidden="true">→</span></>}
              </button>
            </form>
            <p className="f4-switch">New here? <button type="button" data-testid="auth-switch-signup" onClick={() => open("signup")}>Begin your Orbit</button></p>
          </section>

          <section className={`f4-mode${mode === "onboarding" ? " active" : ""}`} data-mode="onboarding">
            <p className="f4-desc">Begin with one honest direction. We do not need to solve your whole life; we only need to notice the first signal clearly.</p>
            <div className="f4-chips" role="group" aria-label="Choose your first direction">
              {DIRECTIONS.map(d => (
                <button key={d} type="button" aria-pressed={chosenDir === d}
                        data-testid={`direction-${d.replace(/\s+/g, "-")}`}
                        className={`f4-chip${chosenDir === d ? " sel" : ""}`}
                        onClick={() => setChosenDir(d)}>{d}</button>
              ))}
            </div>
            <button className="f4-primary f4-submit" type="button" data-testid="auth-sketch-orbit" disabled={!chosenDir}
                    aria-disabled={!chosenDir} onClick={finishOnboarding}>
              Sketch my first Orbit <span aria-hidden="true">→</span>
            </button>
          </section>

          <section className={`f4-mode f4-about${mode === "about" ? " active" : ""}`} data-mode="about">
            <p className="f4-desc">NUR is a private neural cosmos: a way to make thoughts visible without reducing you to a dashboard.</p>
            <div className="f4-about-grid">
              <div className="f4-about-line"><i>✦</i><span><b>Talk</b><br />turn a signal into language.</span></div>
              <div className="f4-about-line"><i>✧</i><span><b>Journal</b><br />let a thought leave a trace.</span></div>
              <div className="f4-about-line"><i>✦</i><span><b>Plan</b><br />make a pattern into movement.</span></div>
              <div className="f4-about-line"><i>✧</i><span><b>Systems</b><br />let lived sparks become shared knowledge.</span></div>
            </div>
            <button className="f4-primary f4-submit" type="button" data-testid="about-begin-orbit" onClick={() => open("signup")}>
              Begin your Orbit <span aria-hidden="true">→</span>
            </button>
          </section>

          <section className={`f4-success${mode === "success" ? " active" : ""}`}>
            <div className="f4-success-star" aria-hidden="true"><MasterStar variant="success" /></div>
            <h3>Your first constellation is waiting.</h3>
            <p>Your first direction is held privately.</p>
            <button className="f4-primary f4-submit" type="button" data-testid="auth-return-sky" onClick={returnToSky}>Return to the sky</button>
          </section>
        </aside>
      </section>
    </>
  );
}
