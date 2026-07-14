/* Source #toast surface + a11y live region (mandate B4). */
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type T = { show: (msg: string) => void };
const C = createContext<T | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const timer = useRef<number>();
  const show = useCallback((m: string) => {
    setMsg(m);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setMsg(null), 2600);
  }, []);
  return (
    <C.Provider value={{ show }}>
      {children}
      <div id="toast" className={`toast${msg ? " show" : ""}`} role="status">{msg}</div>
      <p id="nur-live-region" className="sr-only" aria-live="polite" />
    </C.Provider>
  );
}
export function useToast(): T {
  const v = useContext(C);
  if (!v) throw new Error("useToast outside provider");
  return v;
}
