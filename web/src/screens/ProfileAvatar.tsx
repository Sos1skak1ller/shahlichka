import { Icon } from "../components/Icon";
import { Mascot, mascotName } from "../components/Mascot";
import { ProgressRing } from "../components/ProgressRing";
import type { ChallengeScreenView, ProfileScreenView } from "../contract/types";

interface Props {
  view: ProfileScreenView;
  challenge?: ChallengeScreenView;
  onOpenGoal?: () => void;
  onOpenCategories?: () => void;
}

const CUSTOMIZATION: Record<string, { label: string; icon: string }> = {
  starter_skin: { label: "Начало", icon: "starter" },
  bronze_badge: { label: "Бронза", icon: "bronze" },
  silver_badge: { label: "Серебро", icon: "silver" },
  gold_badge: { label: "Золото", icon: "gold" },
  prestige_frame: { label: "Престиж", icon: "prestige" },
};

const CATEGORY_LABEL: Record<string, string> = {
  baby_food: "детское питание",
  diapers: "подгузники",
  hygiene: "гигиена",
  dairy: "молочные продукты",
  groceries: "базовая корзина",
  household: "товары для дома",
  snacks: "снеки",
};

const FEED_ICON: Record<string, string> = {
  purchase: "receipt",
  level_up: "progress",
  challenge_done: "target",
  referral_reward: "gift",
};

const fmtDate = (ts: string) =>
  new Date(ts).toLocaleDateString("ru-RU", { day: "numeric", month: "long" });

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);

function humanizeDetails(value?: string | null): string | undefined {
  if (!value) return undefined;
  return value
    .split(",")
    .map((part) => CATEGORY_LABEL[part.trim()] ?? part.trim())
    .join(", ");
}

function purchaseWord(value: number): string {
  const mod100 = value % 100;
  const mod10 = value % 10;
  if (mod100 >= 11 && mod100 <= 14) return "покупок";
  if (mod10 === 1) return "покупка";
  if (mod10 >= 2 && mod10 <= 4) return "покупки";
  return "покупок";
}

function weekWord(value: number): string {
  const mod100 = value % 100;
  const mod10 = value % 10;
  if (mod100 >= 11 && mod100 <= 14) return "недель";
  if (mod10 === 1) return "неделя";
  if (mod10 >= 2 && mod10 <= 4) return "недели";
  return "недель";
}

export function ProfileAvatar({ view, challenge, onOpenGoal, onOpenCategories }: Props) {
  const { avatar, savings, streak } = view;
  const toNext = savings.next_threshold === null
    ? null
    : Math.max(0, savings.next_threshold - savings.total_saved_amount);
  const pct = Math.round(savings.progress_ratio * 100);
  const activeGoal = challenge?.challenge;
  const stage = avatar.visual_stage;
  const openedCategories = new Set(
    (view.history ?? [])
      .filter((item) => item.kind === "purchase" && item.detail)
      .flatMap((item) => item.detail!.split(","))
      .map((category) => category.trim())
      .filter((category) => category in CATEGORY_LABEL),
  ).size;
  const goalRemaining = activeGoal
    ? Math.max(0, activeGoal.target - activeGoal.progress)
    : 0;

  return (
    <section className="screen home-screen" aria-label="Главная">
      <div className="hero hero--integrated">
        <div className="hero__stage">
          <Mascot stage={stage} state={avatar.state} live />
        </div>
        <div className="hero__identity">
          <div>
            <span>Ваш аватар</span>
            <strong>{mascotName(stage)}</strong>
          </div>
          <span className="hero__lvl" data-max={avatar.state === "max_level"}>
            Этап {stage} из 5
          </span>
        </div>
        <p className="hero__rule"><Icon name="check" /> Меняется только от подтверждённой экономии</p>
      </div>

      <div className="card savings-card">
        <div className="card__k">Накопленная экономия</div>
        <div className="gauge">
          <ProgressRing
            ratio={savings.progress_ratio}
            centerTop={`${pct}%`}
            centerBottom={toNext === null ? "МАКСИМУМ" : `ДО ЭТАПА ${Math.min(stage + 1, 5)}`}
            size={120}
            label="Прогресс до следующего этапа"
          />
          <div className="gauge__side">
            <div className="card__big">{rub(savings.total_saved_amount)}</div>
            <div className="card__hint">
              {toNext === null
                ? "Все формы аватара открыты"
                : `Ещё ${rub(toNext)} до новой формы`}
            </div>
          </div>
        </div>
        <p className="savings-card__source"><Icon name="receipt" /> Скидки и баллы из проверенных чеков</p>
      </div>

      <div className="home-stats">
        <article className="home-stat">
          <span className="home-stat__icon"><Icon name="sparkles" /></span>
          <div><strong>{streak.streak_count} {weekWord(streak.streak_count)}</strong><span>подряд с покупками</span></div>
        </article>
        <article className="home-stat">
          <span className="home-stat__icon home-stat__icon--orange"><Icon name="wallet" /></span>
          <div>
            <strong>{toNext === null ? "5 из 5" : `${pct}%`}</strong>
            <span>{toNext === null ? "все формы открыты" : "до следующей формы"}</span>
          </div>
        </article>
      </div>

      {activeGoal && (
        <article className="next-action">
          <div className="next-action__head">
            <span><Icon name="target" /> Цель недели</span>
            <b>{activeGoal.progress} из {activeGoal.target}</b>
          </div>
          <h2>{goalRemaining === 1 ? "Остался один привычный шаг" : `Осталось шагов: ${goalRemaining}`}</h2>
          <p>Ещё {goalRemaining} {purchaseWord(goalRemaining)} в категории «{CATEGORY_LABEL[activeGoal.params.category] ?? activeGoal.params.category}».</p>
          <button type="button" onClick={onOpenGoal}>Открыть цель <span aria-hidden>→</span></button>
        </article>
      )}

      <button type="button" className="category-preview" onClick={onOpenCategories}>
        <span className="category-preview__icon"><Icon name="progress" /></span>
        <span><strong>Карта категорий</strong><small>{openedCategories} из {Object.keys(CATEGORY_LABEL).length} областей уже открыты</small></span>
        <span aria-hidden>→</span>
      </button>

      <div className="card collection-card">
        <div className="card__k">Коллекция этапов</div>
        <ul className="chips" aria-label="Разблокированные этапы">
          {avatar.unlocked_customizations.map((item) => {
            const customization = CUSTOMIZATION[item] ?? { label: item, icon: "starter" };
            return (
              <li key={item} className="chip">
                <span className="chip__ico"><Icon family="collection" name={customization.icon} /></span>
                <span>{customization.label}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {(view.history ?? []).length > 0 && (
        <details className="card history-card">
          <summary>Последние начисления <span>Показать</span></summary>
          <ul className="feed">
            {(view.history ?? []).slice(0, 5).map((item, index) => (
              <li key={`${item.ts}-${index}`} className="feed__row">
                <span className="feed__ico"><Icon name={FEED_ICON[item.kind] ?? "check"} /></span>
                <div className="feed__body">
                  <div className="feed__title">{item.title}</div>
                  {item.detail && <div className="feed__detail">{humanizeDetails(item.detail)}</div>}
                  <div className="feed__date">{fmtDate(item.ts)}</div>
                </div>
                {item.amount != null && <span className="feed__amt">+{rub(item.amount)}</span>}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
