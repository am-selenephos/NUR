import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./app/AuthProvider";
import RuntimePreferences from "./app/RuntimePreferences";
import { ProtectedRoute, PublicOnlyRoute } from "./app/guards";
import { GalaxyProvider } from "./galaxy/GalaxyProvider";
import { TransitionDirector } from "./app/TransitionDirector";
import { OrbitStateProvider } from "./lib/orbitState";
import { WorldFocusProvider } from "./app/worldFocus";
import { ToastProvider } from "./routes/universe/shell/ToastLayer";
import Landing from "./routes/Landing";
import UniverseLayout from "./routes/universe/UniverseLayout";
import Today from "./routes/universe/Today";
import Talk from "./routes/universe/Talk";
import Journal from "./routes/universe/Journal";
import Plan from "./routes/universe/Plan";
import Systems from "./routes/universe/Systems";
import Omega from "./routes/universe/Omega";
import {
  OmegaWhyChangedRoute,
  Settings,
  UniverseCommunity,
  UniverseInsights,
  UniverseMap,
  UniverseOrbits,
  UniverseResearch,
  UniverseTimeline,
  UniverseWebSignals,
} from "./routes/universe/UniverseLenses";
import CapsuleRoom from "./routes/CapsuleRoom";
import "./styles/global.css";

const OMEGA_RESEARCH_ENABLED = import.meta.env.VITE_NUR_ENABLE_OMEGA_RESEARCH === "true";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<Landing />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/capsule/:id" element={<CapsuleRoom />} />
        <Route element={<UniverseLayout />}>
          <Route path="/today" element={<Today />} />
          <Route path="/talk" element={<Talk />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/systems" element={<Systems />} />
          <Route path="/universe" element={<Systems />} />
          <Route path="/universe/map" element={<UniverseMap />} />
          <Route path="/universe/orbits" element={<UniverseOrbits />} />
          <Route path="/universe/timeline" element={<UniverseTimeline />} />
          <Route path="/universe/insights" element={<UniverseInsights />} />
          <Route path="/universe/research" element={<UniverseResearch />} />
          <Route path="/universe/community" element={<UniverseCommunity />} />
          <Route path="/universe/web-signals" element={<UniverseWebSignals />} />
          {OMEGA_RESEARCH_ENABLED && <Route path="/universe/omega" element={<Omega />} />}
          {OMEGA_RESEARCH_ENABLED && <Route path="/universe/omega/review" element={<Omega initialPanel="review" />} />}
          {OMEGA_RESEARCH_ENABLED && <Route path="/universe/omega/why-changed/:claimId" element={<OmegaWhyChangedRoute />} />}
          <Route path="/settings" element={<Settings />} />
          <Route path="/onboarding" element={<Navigate to="/today" replace />} />
        </Route>
      </Route>
      <Route path="/intro" element={<Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

/* Note: StrictMode is intentionally off — the persistent GalaxyRuntime binds
   one canvas for the app's lifetime; dev double-mounting would orphan it. */
ReactDOM.createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <AuthProvider>
      <RuntimePreferences />
      <GalaxyProvider>
        <TransitionDirector>
          <WorldFocusProvider>
            <OrbitStateProvider>
              <ToastProvider>
                <AppRoutes />
              </ToastProvider>
            </OrbitStateProvider>
          </WorldFocusProvider>
        </TransitionDirector>
      </GalaxyProvider>
    </AuthProvider>
  </BrowserRouter>,
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => undefined);
  });
}
