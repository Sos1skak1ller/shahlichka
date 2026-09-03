import { ProgressBar } from "../components/ProgressBar";
import type { ChallengeScreenView } from "../contract/types";

interface Props {
  view: ChallengeScreenView;
}

const NOTE_LABEL: Record<string, string> = {
  cold_start_fallback: "Пока мало истории покупок — челлендж по сегменту",
  template_pool_exhausted: "Свежие форматы на эту неделю закончились",
  anti_fatigue_switch: "Сменили формат, чтобы не наскучило",
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(n);

export function Challenge({ view }: Props) {
  const c = view.challenge;

  return (
    <section className="screen screen--challenge" aria-labelledby="challenge-title">
      <h1 id="challenge-title">Челлендж недели</h1>
      <div className="challenge__week">{view.iso_week}</div>

      {c === null ? (
        <p className="challenge__empty">На этой неделе активного челленджа нет.</p>
      ) : (
        <div className="challenge__card" data-status={c.status}>
          <p className="challenge__text">{c.text}</p>
          <ProgressBar ratio={c.target === 0 ? 0 : c.progress / c.target} label="Прогресс челленджа" />
          <div className="challenge__meta">
            <span>
              {c.progress} из {c.target}
            </span>
            <span>Награда: {rub(c.reward_amount)}</span>
          </div>
          <div className="challenge__status">
            {c.status === "completed"
              ? "Выполнено 🎉"
              : c.status === "expired"
                ? "Срок вышел"
                : `Успеть до ${new Date(c.valid_to).toLocaleDateString("ru-RU")}`}
          </div>
        </div>
      )}

      {(view.notes ?? []).length > 0 && (
        <ul className="challenge__notes">
          {(view.notes ?? []).map((n) => (
            <li key={n}>{NOTE_LABEL[n] ?? n}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
