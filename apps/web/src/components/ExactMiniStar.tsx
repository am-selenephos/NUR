/* The v136/v89 runtime's makeStar(), ported verbatim as a component: the
   source script replaced every .nur-v136-v89-mini-host's content with this
   exact span tree and added .nur-exact-icon-shell to the host. Hosts in React
   must carry that shell class and render this as their only child. */
type Size = "nur-mini-18" | "nur-mini-16" | "nur-mini-14" | "nur-mini-12";
const RAYS: Array<"g" | "h" | "p"> = ["g","h","g","p","g","h","g","p","g","h","g","p"];

export default function ExactMiniStar({ size = "nur-mini-16" }: { size?: Size }) {
  return (
    <span className={`nur-exact-mini-host ${size}`} aria-hidden="true">
      <span className="f4-master-star nur-v136-v89-exact-star spark f4-master-star--hero nur-star-module" aria-hidden="true">
        <span className="spark-glow nur-halo-glow" data-nur-layer="halo-glow" />
        <span className="spark-halo nur-halo-primary" data-nur-layer="halo-primary" />
        <span className="spark-h2 nur-halo-secondary" data-nur-layer="halo-secondary" />
        <span className="spark-core nur-star-core" data-nur-layer="star-core" />
        <span className="rayset nur-star-rays" data-nur-layer="star-rays">
          {RAYS.map((k, i) => (
            <span key={i} className={`ray ${k} r${i + 1}`}>
              <span className="ray-glow" /><span className="ray-core" />
            </span>
          ))}
        </span>
        <span className="ob ob1 nur-star-orb" data-nur-layer="star-orb" />
        <span className="ob ob2 nur-star-orb" data-nur-layer="star-orb" />
        <span className="ob ob3 nur-star-orb" data-nur-layer="star-orb" />
      </span>
    </span>
  );
}
