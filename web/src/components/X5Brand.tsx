interface Props {
  className: string;
  compact?: boolean;
}

export function X5Brand({ className, compact = false }: Props) {
  return (
    <a className={className} href="/landing" aria-label="X5 Клуб · Рост — на главную">
      <img src="/assets/growth/brand/x5-logo.svg" width="62" height="42" alt="X5" />
      <span className={className + "__name"}>
        Клуб · Рост
        {!compact && <small>Проектная концепция</small>}
      </span>
    </a>
  );
}
