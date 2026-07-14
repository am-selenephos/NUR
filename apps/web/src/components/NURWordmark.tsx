/* ONE reusable holographic NUR wordmark. The gradient/animation live in the
   frozen CSS; variants select the exact source class stacks. */
type Variant = "intro" | "header" | "hero" | "map" | "inline";
export default function NURWordmark({ variant = "inline", text = "NUR", className = "" }:
  { variant?: Variant; text?: string; className?: string }) {
  const cls: Record<Variant, string> = {
    intro: "i-nur",
    header: "h-n holo-wordmark nur-wordmark",
    hero: "nur-wordmark holo-wordmark nur-wordmark--hero",
    map: "nur-holo-word",
    inline: "nur-wordmark holo-wordmark",
  };
  return <span className={`${cls[variant]} ${className}`.trim()}>{text}</span>;
}
