import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  tone?: "good" | "wait" | "bad";
}

export function StatusPill({ children, tone = "good" }: Props) {
  return (
    <span className="pill" data-tone={tone}>
      {children}
    </span>
  );
}
