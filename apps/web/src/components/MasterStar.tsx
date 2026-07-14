/* ONE reusable MasterStar. Exact V197 DOM: spark-glow/halo/h2/core, 12-ray
   rayset (g/h/p pattern), three orbiters — with the v33/v34 exact-symbol
   classes that carry the frozen geometry. Variants map to the source hosts. */
type Variant = "hero" | "brand" | "success" | "mini" | "intro";
const RAYS: Array<"g" | "h" | "p"> = ["g","h","g","p","g","h","g","p","g","h","g","p"];

export default function MasterStar({ variant = "hero", id, className = "" }:
  { variant?: Variant; id?: string; className?: string }) {
  const base = "spark nur-v33-master nur-v34-exact-symbol f4-master-star nur-star-module";
  const byVariant: Record<Variant, string> = {
    hero: "f4-master-star--hero nur-v136-v89-exact-star",
    brand: "f4-master-star--brand",
    success: "f4-master-star--success",
    mini: "f4-master-star--brand nur-mini-star",
    intro: "i-spark",
  };
  return (
    <div id={id} className={`${base} ${byVariant[variant]} ${className}`.trim()} aria-hidden="true">
      <div className="spark-glow nur-halo-glow" />
      <div className="spark-halo nur-halo-primary" />
      <div className="spark-h2 nur-halo-secondary" />
      <div className="spark-core nur-star-core" />
      <div className="rayset nur-star-rays">
        {RAYS.map((k, i) => (
          <div key={i} className={`ray ${k} r${i + 1}`}>
            <div className="ray-glow" /><div className="ray-core" />
          </div>
        ))}
      </div>
      <div className="ob ob1 nur-star-orb" />
      <div className="ob ob2 nur-star-orb" />
      <div className="ob ob3 nur-star-orb" />
    </div>
  );
}
