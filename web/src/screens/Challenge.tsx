import { ProgressRing } from "../components/ProgressRing";
import type { ChallengeScreenView } from "../contract/types";

interface Props {
  view: ChallengeScreenView;
}

const NOTE_LABEL: Record<string, string> = {
  cold_start_fallback: "Пока мало истории покупок — подобрали челлендж по сегменту",
  template_pool_exhausted: "Свежие форматы на эту неделю закончились",
  anti_fatigue_switch: "Сменили формат, чтобы не наскучило",
};

const CAT_ICON: Record<string, string> = {
  baby_food: "🍼",
  diapers: "🧷",
  hygiene: "🧼",
  dairy: "🥛",
  groceries: "🛒",
  household: "🧴",
  snacks: "🍪",
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);

export function Challenge({ view }: Props) {
  const c = view.challenge;

  return (
    <section className="screen" aria-labelledby="challenge-title">
      <h1 id="challenge-title" className="screen__eyebrow">
        Челлендж недели · {view.iso_week}
      </h1>

      {c === null ? (
        <div className="card">
          <p className="ch__empty">На этой неделе активного челленджа нет.</p>
        </div>
      ) : (
        <div className="card ch" data-status={c.status}>
          <div className="ch__ico" aria-hidden>
            {CAT_ICON[c.params.category] ?? "🎯"}
          </div>
          <p className="ch__text">{c.text}</p>

          <ProgressRing
            value={c.progress}
            target={c.target}
            centerTop={`${c.progress}/${c.target}`}
            centerBottom="ГОТОВО"
            size={132}
            label="Прогресс челленджа"
          />
          <div className="card__hint" style={{ textAlign: "center" }}>
            {c.progress} из {c.target}
          </div>

          <div className="ch__reward">🎁 +{rub(c.reward_amount)}</div>

          <div className="ch__deadline">
            {c.status === "completed" ? (
              <span className="ch__done">Выполнено 🎉</span>
            ) : c.status === "expired" ? (
              "Срок вышел"
            ) : (
              `Успеть до ${new Date(c.valid_to).toLocaleDateString("ru-RU")}`
            )}
          </div>
        </div>
      )}

      {(view.notes ?? []).length > 0 && (
        <ul className="notes">
          {(view.notes ?? []).map((n) => (
            <li key={n} className="note">
              <span aria-hidden>💡</span>
              <span>{NOTE_LABEL[n] ?? n}</span>
            </li>
          ))}
        </ul>
      )}

      {(view.catalog ?? []).length > 0 && (
        <div className="card">
          <div className="card__k">Форматы челленджей</div>
          <ul className="cat">
            {(view.catalog ?? []).map((c) => (
              <li key={c.template_id} className="cat__row" data-lock={!c.available}>
                <span className="cat__ico" aria-hidden>
                  {CAT_ICON[c.category] ?? "🎯"}
                </span>
                <div className="cat__body">
                  <div className="cat__title">{c.title}</div>
                  <div className="cat__sub">
                    {c.available
                      ? `категория «${c.category}»`
                      : (c.lock_reason ?? "недоступно")}
                  </div>
                </div>
                <span className="cat__reward">
                  {c.available ? `+${rub(c.reward_amount)}` : "🔒"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {(view.history ?? []).length > 0 && (
        <div className="card">
          <div className="card__k">Прошлые челленджи</div>
          <ul className="chist">
            {(view.history ?? []).map((h) => (
              <li key={h.challenge_id} className="chist__row">
                <span aria-hidden>{h.status === "completed" ? "✅" : "⏳"}</span>
                <span className="chist__txt">{h.text}</span>
                <span className="chist__amt">
                  {h.reward_amount > 0 ? `+${rub(h.reward_amount)}` : "—"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
