interface Props {
  /** режим «доля» — если задан, используется вместо value/target для дуги и aria */
  ratio?: number;
  value?: number;
  target?: number;
  /** крупный текст в центре; по умолчанию `${value} / ${target}` */
  centerTop?: string;
  centerBottom?: string;
  size?: number;
  label?: string;
}

/** Круговой индикатор в стиле «health score». */
export function ProgressRing({
  ratio,
  value = 0,
  target = 1,
  centerTop,
  centerBottom,
  size = 148,
  label,
}: Props) {
  const stroke = 13;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const frac =
    ratio != null ? ratio : target > 0 ? value / target : 0;
  const clamped = Math.min(1, Math.max(0, frac));
  const pct = Math.round(clamped * 100);

  return (
    <svg
      className="ring"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="progressbar"
      aria-label={label ?? "Прогресс"}
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <defs>
        <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--acc)" />
          <stop offset="1" stopColor="var(--green-600)" />
        </linearGradient>
      </defs>
      <circle className="ring__track" cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={stroke} />
      <circle
        className="ring__fill"
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        strokeWidth={stroke}
        strokeDasharray={circ}
        strokeDashoffset={circ * (1 - clamped)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text className="ring__num" x="50%" y="47%" dominantBaseline="middle" textAnchor="middle">
        {centerTop ?? `${value} / ${target}`}
      </text>
      <text className="ring__sub" x="50%" y="63%" dominantBaseline="middle" textAnchor="middle">
        {centerBottom ?? "ГОТОВО"}
      </text>
    </svg>
  );
}
