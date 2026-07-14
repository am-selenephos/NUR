/* Orbit state: server-backed where Gate 2 mandates persistence (journal,
   plans, systems/orbits, research); session-scope only for the live Talk
   thread, boundary choice and onboarding direction. The visible glow count is
   derived from persisted outcomes, then advanced only after an outcome POST. */
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { nur, type JournalRow, type NURTalkOutput, type OmegaTalkSummary, type OrbitRow, type PlanRow, type TalkThreadRow } from "./api";

export type TalkMsg = {
  id: string;
  who: "user" | "nur";
  text: string;
  output?: NURTalkOutput;
  omega?: OmegaTalkSummary | null;
  refs?: { kind: string; excerpt: string }[];
  note?: string;
};

const SUGGESTED = [
  { title: "Quiet Ambition", description: "Build without noise" },
  { title: "Rebuild", description: "" },
  { title: "Study", description: "" },
  { title: "Connection", description: "" },
];

const ROUTE_TITLE = "Make one visible pass on the interior";
const ROUTE_STEPS = [
  { title: "Lock the front page as visual truth", body: "Use the exact wordmark, star and galaxy language everywhere." },
  { title: "Make the Personal Orbit page feel like the same place", body: "One open field, warm low-light rails, no dashboard chrome." },
  { title: "Open Systems without turning NUR into a social feed", body: "Shared thought, returned outcomes, visible learning." },
];

function useStore() {
  const [glows, setGlows] = useState(0);
  const [orbits, setOrbits] = useState<OrbitRow[]>([]);
  const [activeSystem, setActiveSystem] = useState("Quiet Ambition");
  const [boundary, setBoundary] = useState<"Private" | "Ephemeral" | "System Shared" | "Learning Candidate">("Private");
  const [addSystemOpen, setAddSystemOpen] = useState(false);
  const [plan, setPlan] = useState<PlanRow | null>(null);
  const [journal, setJournal] = useState<JournalRow[]>([]);
  const [thread, setThread] = useState<TalkMsg[]>([]);
  const [draft, setDraft] = useState("");
  const [direction, setDirection] = useState<string | null>(null);
  const hydrated = useRef(false);

  const loadOrbits = useCallback(async () => setOrbits(await nur.listOrbits()), []);
  const hydrate = useCallback(async () => {
    if (hydrated.current) return;
    hydrated.current = true;
    try {
      const [o, j, p, t, s] = await Promise.all([
        nur.listOrbits(), nur.listJournal(), nur.listPlans(), nur.talkThread(), nur.orbitState(),
      ]);
      setOrbits(o); setJournal(j); setPlan(p[0] ?? null); setThread(t.map(threadRowToMsg)); setGlows(s.outcomes_returned);
    } catch { hydrated.current = false; }
  }, []);

  const projects = orbits.filter(o => o.kind !== "PERSONAL_BRIDGE");
  const systems = projects.length
    ? projects.map(o => ({ name: o.title, description: o.description ?? "", suggested: false, id: o.id }))
    : SUGGESTED.map(s => ({ name: s.title, description: s.description, suggested: true, id: null as string | null }));
  const activeOrbit = projects.find(o => o.title === activeSystem) ?? null;

  return useMemo(() => ({
    glows,
    hydrate, loadOrbits,
    orbits, projects, systems, activeOrbit, activeSystem, setActiveSystem,
    addSystem: async (name: string, description: string) => {
      const row = await nur.createOrbit(name, description || undefined);
      setOrbits(x => [...x, row]);
      setActiveSystem(row.title);
      return row;
    },
    plan,
    beginRoute: async () => setPlan(await nur.createPlan(ROUTE_TITLE, ROUTE_STEPS)),
    addStep: async (title: string, body?: string) => {
      if (!plan) {
        const created = await nur.createPlan(ROUTE_TITLE, [{ title, body }]);
        setPlan(created);
        const step = created.steps[0];
        if (!step) throw new Error("Plan step was not persisted.");
        return step;
      }
      const step = await nur.addPlanStep(plan.id, title, body);
      setPlan(p => p ? { ...p, steps: [...p.steps, step] } : p);
      return step;
    },
    toggleStep: async (stepId: string, done: boolean) => {
      const s = await nur.patchStep(stepId, done);
      setPlan(p => p ? { ...p, steps: p.steps.map(x => x.id === s.id ? s : x) } : p);
      return s;
    },
    recordOutcome: async (stepId: string, observed: string) => {
      await nur.stepOutcome(stepId, observed);
      setGlows(g => g + 1);
    },
    journal,
    keepEntry: async (body: string) => {
      const row = await nur.keepJournal(body);
      setJournal(j => [row, ...j]);
      return row;
    },
    thread, say: (m: TalkMsg) => setThread(t => [...t, m]),
    loadThread: async (orbitId?: string) => {
      const rows = await nur.talkThread(orbitId);
      setThread(rows.map(threadRowToMsg));
    },
    draft, setDraft, direction, setDirection,
    boundary, setBoundary, addSystemOpen, setAddSystemOpen,
  }), [glows, orbits, activeSystem, boundary, addSystemOpen, plan, journal, thread, draft, direction, hydrate, loadOrbits]);
}
type Store = ReturnType<typeof useStore>;
const Ctx = createContext<Store | null>(null);
export function OrbitStateProvider({ children }: { children: ReactNode }) {
  const store = useStore();
  return <Ctx.Provider value={store}>{children}</Ctx.Provider>;
}
export function useOrbit(): Store {
  const s = useContext(Ctx);
  if (!s) throw new Error("useOrbit outside provider");
  return s;
}

function threadRowToMsg(row: TalkThreadRow): TalkMsg {
  const payload = row.structured_payload as { talk_output?: NURTalkOutput; omega?: OmegaTalkSummary; provider_reason?: string; provider_available?: boolean };
  return {
    id: row.id,
    who: row.who,
    text: payload.talk_output?.direct_response ?? row.text ?? "",
    output: payload.talk_output,
    omega: payload.omega,
    note: payload.provider_available === false ? payload.provider_reason : undefined,
  };
}
