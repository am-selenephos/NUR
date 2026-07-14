import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  as?: "bdi" | "span";
};

export default function BidiText({ children, className, as = "bdi" }: Props) {
  const cls = ["bidi-isolate", className].filter(Boolean).join(" ");
  return as === "span"
    ? <span dir="auto" className={cls}>{children}</span>
    : <bdi dir="auto" className={cls}>{children}</bdi>;
}
