/* ONE persistent GalaxyRuntime for the whole app. The canvas mounts once at the
   root and never unmounts across routes; the engine is the verbatim V197/V183
   renderer (see engine.js). A module-level singleton guards StrictMode double
   effects. */
import { useEffect, useRef, type ReactNode } from "react";
import { createGalaxy, type Galaxy } from "./engine";

let runtime: Galaxy | null = null;

export function GalaxyProvider({ children }: { children: ReactNode }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (!runtime && canvasRef.current) runtime = createGalaxy(canvasRef.current);
  }, []);
  return (
    <>
      <canvas id="space3d" ref={canvasRef} aria-hidden="true" />
      {children}
    </>
  );
}
export function useGalaxy(): Galaxy | null { return runtime; }
export const _test_reset = () => { runtime = null; };
