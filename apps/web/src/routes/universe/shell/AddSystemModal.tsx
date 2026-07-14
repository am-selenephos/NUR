/* Add System (mandate B11): V197-styled sheet, focus trap, Escape, overlay
   close, return-focus. Gate 1 truth: staged in session until Gate 2's real
   POST /v1/orbits replaces the staging line — no fake POST, no false claim. */
import { useEffect, useRef, useState } from "react";
import { useOrbit } from "../../../lib/orbitState";
import { useToast } from "./ToastLayer";

export default function AddSystemModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const orbit = useOrbit();
  const toast = useToast();
  const nameRef = useRef<HTMLInputElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  useEffect(() => {
    if (open) {
      returnFocus.current = document.activeElement as HTMLElement;
      nameRef.current?.focus();
      const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
      document.addEventListener("keydown", onKey);
      return () => { document.removeEventListener("keydown", onKey); returnFocus.current?.focus(); };
    }
  }, [open, onClose]);

  if (!open) return null;
  async function stage() {
    if (!name.trim()) return;
    try {
      await orbit.addSystem(name.trim(), desc.trim());
      toast.show("System saved to your private Orbit.");
      setName(""); setDesc(""); onClose();
    } catch {
      toast.show("The sky did not take it — try again.");
    }
  }
  return (
    <div className="modal-backdrop open show" role="dialog" aria-modal="true" aria-hidden="false"
         aria-labelledby="addsys-title" onClick={onClose}>
      <div className="scope-modal" onClick={e => e.stopPropagation()}>
        <button className="scope-modal-close" data-testid="add-system-close" aria-label="Close" onClick={onClose}>×</button>
        <h2 id="addsys-title">Name the sky it needs.</h2>
        <p>A System is a life problem given its own constellation.</p>
        <div className="f4-form">
          <div className="f4-field"><label htmlFor="addsys-name">system name</label>
            <input id="addsys-name" data-testid="add-system-name" ref={nameRef} value={name} onChange={e => setName(e.target.value)}
                   placeholder="e.g. Deep Work Winter" /></div>
          <div className="f4-field"><label htmlFor="addsys-desc">what it holds</label>
            <input id="addsys-desc" data-testid="add-system-desc" value={desc} onChange={e => setDesc(e.target.value)}
                   placeholder="one honest sentence" /></div>
          <button className="f4-primary f4-submit" type="button" data-testid="add-system-create" onClick={stage}>
            Save this System <span aria-hidden="true">→</span>
          </button>
          <p className="f4-privacy"><i>✦</i><span>Saved privately. It can travel only through a Capsule you create.</span></p>
        </div>
      </div>
    </div>
  );
}
