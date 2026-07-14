/* Exact source scope modal (#scope-modal) with focus handling. CLIENT_ONLY
   honestly: chosen boundary updates the live context rail; server-side scope
   fields land with the Gate 2 tables. */
import { useEffect, useRef } from "react";
import { useOrbit } from "../../../lib/orbitState";
import { useToast } from "./ToastLayer";

const OPTIONS = [
  { key: "Ephemeral", glyph: "◌", d: "NUR uses it only for the current response, then lets it go." },
  { key: "Private", glyph: "✦", d: "Save it only inside your Personal Orbit." },
  { key: "System Shared", glyph: "✣", d: "Share pseudonymously in one selected Star System." },
  { key: "Learning Candidate", glyph: "✧", d: "Contribute a reviewed piece of evidence toward a Candidate Insight." },
] as const;

export default function ScopeModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const orbit = useOrbit();
  const toast = useToast();
  const closeRef = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      returnFocus.current = document.activeElement as HTMLElement;
      closeRef.current?.focus();
      const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
      document.addEventListener("keydown", onKey);
      return () => { document.removeEventListener("keydown", onKey); returnFocus.current?.focus(); };
    }
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div id="scope-modal" className="modal-backdrop open show" role="dialog" aria-modal="true"
         aria-labelledby="scope-title" onClick={onClose}>
      <div className="scope-modal" onClick={e => e.stopPropagation()}>
        <button id="scope-close" ref={closeRef} className="scope-modal-close" data-testid="scope-close" aria-label="Close"
                onClick={onClose}>×</button>
        <h2 id="scope-title">Choose the boundary.</h2>
        <p>Nothing crosses a wall because an interface made it easy. You choose, visibly.</p>
        <div className="scope-options">
          {OPTIONS.map(o => (
            <button key={o.key} type="button"
                    data-testid={`scope-option-${o.key.toLowerCase().replace(/\s+/g, "-")}`}
                    className={`scope-option${orbit.boundary === o.key ? " selected" : ""}`}
                    onClick={() => { orbit.setBoundary(o.key); toast.show(`Boundary: ${o.key}.`); onClose(); }}>
              <span>{o.glyph}</span>
              <span><strong>{o.key}</strong><span>{o.d}</span></span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
