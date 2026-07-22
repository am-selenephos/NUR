import type { V197BridgeSnapshot } from "./v197ApiClient";
import { V197_SELECTORS } from "./v197Selectors";

function text(node: Element | null, value: string): void {
  if (node) node.textContent = value;
}

function humanBoundary(value: string | undefined): string | null {
  const labels: Record<string, string> = {
    EPHEMERAL: "Ephemeral",
    PRIVATE_ORBIT: "Private Orbit",
    SYSTEM_SHARED: "System Shared",
    LEARNING_CANDIDATE: "Learning Candidate",
  };
  return value ? labels[value] ?? null : null;
}

/**
 * Read-only Phase 1 hydration. This intentionally changes text only inside
 * slots that already exist in canonical V197. It never inserts nodes, classes,
 * inline style, or geometry CSS.
 */
export function hydrateReadOnlyV197(document: Document, snapshot: V197BridgeSnapshot): void {
  const state = snapshot.ownerState;
  const stats = [...document.querySelectorAll<HTMLElement>(V197_SELECTORS.heroStats)];
  if (state) {
    text(stats[0]?.querySelector("b") ?? null, String(state.active_systems ?? 0).padStart(2, "0"));
    text(stats[1]?.querySelector("b") ?? null, String(state.outcomes_returned ?? 0).padStart(2, "0"));
    text(stats[2]?.querySelector("b") ?? null, String(state.insights_evolving ?? 0).padStart(2, "0"));
    text(
      document.querySelector(V197_SELECTORS.fieldReadout),
      `${state.active_systems ?? 0} active systems · ${state.outcomes_returned ?? 0} returned outcomes`,
    );
  }

  const name = snapshot.session.profile.chosen_name?.trim();
  if (name) text(document.querySelector(V197_SELECTORS.contextTitle), `${name}'s Orbit, held gently.`);
  // The canonical owner star ships a placeholder identity; announce the real
  // session owner instead of a person who does not exist.
  if (name) {
    document.querySelector(V197_SELECTORS.ownerStar)
      ?.setAttribute("aria-label", `${name} — owner session`);
  }

  const boundary = humanBoundary(snapshot.preferences?.default_boundary ?? snapshot.session.profile.default_boundary);
  if (boundary) text(document.querySelector(V197_SELECTORS.boundaryName), boundary);

  const kicker = document.querySelector(V197_SELECTORS.liveFeed);
  if (kicker?.textContent?.includes("live feed")) {
    kicker.textContent = kicker.textContent.replace(/live feed/i, "owner ledger");
  }
}
