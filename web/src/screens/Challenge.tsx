import { Icon } from "../components/Icon";
import { ProgressRing } from "../components/ProgressRing";
import type { ChallengeScreenView } from "../contract/types";

interface Props {
  view: ChallengeScreenView;
}

const NOTE_LABEL: Record<string, string> = {
  cold_start_fallback: "Пока мало истории покупок — цель подобрана по рабочему профилю",
  template_pool_exhausted: "Свежие варианты на эту неделю закончились",
  anti_fatigue_switch: "Формат изменён, чтобы цели не повторялись",
};

const CATEGORY: Record<string, { title: string; icon: string }> = {
  baby_food: { title: "детское питание", icon: "baby-food" },
  diapers: { title: "подгузники", icon: "diapers" },
  hygiene: { title: "гигиена", icon: "hygiene" },
  dairy: { title: "молочные продукты", icon: "dairy" },
  groceries: { title: "базовая корзина", icon: "groceries" },
  household: { title: "товары для дома", icon: "household" },
  snacks: { title: "снеки", icon: "snacks" },
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);

function formatWeek(value: string): string {
  const [, week] = value.split("-W");
  return week ? `Неделя ${Number(week)}` : value;
}

function remainingStepsLabel(progress: number, target: number): string {
  const remaining = Math.max(0, target - progress);
  if (remaining === 0) return "Цель выполнена";
  if (remaining === 1) return "Остался один шаг";
  return `Осталось шагов: ${remaining}`;
}

export function Challenge({ view }: Props) {
  const challenge = view.challenge;
  const category = challenge ? CATEGORY[challenge.params.category] : undefined;

  return (
    <section className="screen goal-screen" aria-labelledby="challenge-title">
      <div className="screen-heading">
        <span className="screen__eyebrow">{formatWeek(view.iso_week)}</span>
        <h1 id="challenge-title">Цель недели</h1>
        <p>Одно понятное действие из вашей привычной корзины.</p>
      </div>

      {challenge === null ? (
        <div className="card empty-state">
          <span><Icon name="check" /></span>
          <h2>На этой неделе всё спокойно</h2>
          <p className="ch__empty">Новая цель появится после следующего обновления покупок.</p>
        </div>
      ) : (
        <>
          <article className="card ch" data-status={challenge.status}>
            <div className="ch__topline">
              <span className="ch__ico"><Icon family="category" name={category?.icon ?? "groceries"} /></span>
              <span>{category?.title ?? challenge.params.category}</span>
            </div>
            <h2>{remainingStepsLabel(challenge.progress, challenge.target)}</h2>
            <p className="ch__text">
              Сделайте {challenge.target} покупки в категории «{category?.title ?? challenge.params.category}» до {new Date(challenge.valid_to).toLocaleDateString("ru-RU", { day: "numeric", month: "long" })}.
            </p>

            <div className="ch__progress-layout">
              <ProgressRing
                value={challenge.progress}
                target={challenge.target}
                centerTop={`${challenge.progress}/${challenge.target}`}
                centerBottom="ГОТОВО"
                size={124}
                label="Прогресс цели"
              />
              <div>
                <span>После выполнения</span>
                <strong>+{rub(challenge.reward_amount)}</strong>
                <small>Награда начислится после проверки чека</small>
              </div>
            </div>

            <div className="ch__deadline">
              <Icon name={challenge.status === "completed" ? "check" : "clock"} />
              {challenge.status === "completed"
                ? "Выполнено"
                : challenge.status === "expired"
                  ? "Срок завершён"
                  : `До ${new Date(challenge.valid_to).toLocaleDateString("ru-RU")}`}
            </div>
          </article>

          <details className="why-card" open>
            <summary><Icon name="info" /> Почему эта цель?</summary>
            <p>Категория уже встречается в вашей истории покупок, а цель остаётся достижимой относительно привычного темпа.</p>
            <small>Объяснение построено на синтетическом профиле демо.</small>
          </details>
        </>
      )}

      {(view.notes ?? []).length > 0 && (
        <ul className="notes">
          {(view.notes ?? []).map((note) => (
            <li key={note} className="note"><Icon name="info" /><span>{NOTE_LABEL[note] ?? note}</span></li>
          ))}
        </ul>
      )}

      {(view.history ?? []).length > 0 && (
        <details className="card history-card goal-history">
          <summary>Прошлые цели <span>Показать</span></summary>
          <ul className="chist">
            {(view.history ?? []).map((item) => (
              <li key={item.challenge_id} className="chist__row">
                <span><Icon name={item.status === "completed" ? "check" : "clock"} /></span>
                <span className="chist__txt">{item.text.replace(/baby_food/g, "детское питание")}</span>
                <span className="chist__amt">{item.reward_amount > 0 ? `+${rub(item.reward_amount)}` : "—"}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
