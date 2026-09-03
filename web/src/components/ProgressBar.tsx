interface Props {
  ratio: number;
  label?: string;
}

export function ProgressBar({ ratio, label }: Props) {
  const pct = Math.round(Math.min(1, Math.max(0, ratio)) * 100);
  return (
    <div
      className="bar"
      role="progressbar"
      aria-label={label ?? "Прогресс"}
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="bar__fill" style={{ width: `${pct}%` }} />
    </div>
  );
}
