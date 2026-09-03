interface Props {
  ratio: number;
  label?: string;
}

export function ProgressBar({ ratio, label }: Props) {
  const pct = Math.round(Math.min(1, Math.max(0, ratio)) * 100);
  return (
    <div className="progress-bar" aria-label={label ?? "Прогресс"}>
      <div
        className="progress-bar__fill"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        style={{ width: `${pct}%` }}
      />
      <span className="progress-bar__text">{pct}%</span>
    </div>
  );
}
