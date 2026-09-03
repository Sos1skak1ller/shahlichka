import { Mascot, mascotName } from "../components/Mascot";
import { ProgressRing } from "../components/ProgressRing";
import type { ProfileScreenView } from "../contract/types";

interface Props {
  view: ProfileScreenView;
}

const CHIP_ICON: Record<string, string> = {
  starter_skin: "🌱",
  bronze_badge: "🥉",
  silver_badge: "🥈",
  gold_badge: "🥇",
  prestige_frame: "👑",
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);

export function ProfileAvatar({ view }: Props) {
  const { avatar, savings, streak } = view;
  const toNext =
    savings.next_threshold === null
      ? null
      : Math.max(0, savings.next_threshold - savings.total_saved_amount);
  const pct = Math.round(savings.progress_ratio * 100);
  const dried = streak.streak_count === 0;

  return (
    <section className="screen" aria-label="Прогресс">
      <div className="hero">
        <div className="hero__stage">
          <Mascot stage={avatar.visual_stage} state={avatar.state} dried={dried} />
        </div>
        <div className="hero__name">{mascotName(avatar.visual_stage)}</div>
        <span className="hero__lvl" data-max={avatar.state === "max_level"}>
          {avatar.state === "max_level" ? "★" : "●"} Уровень {avatar.level}
        </span>
        {dried && (
          <div className="hero__dry">Подсох — на этой неделе ещё не было покупок</div>
        )}
      </div>

      <div className="card card--dark">
        <div className="card__k">Накоплено экономии</div>
        <div className="gauge">
          <ProgressRing
            ratio={savings.progress_ratio}
            centerTop={`${pct}%`}
            centerBottom={toNext === null ? "МАКСИМУМ" : "ДО УРОВНЯ"}
            size={128}
            label="Прогресс до следующего уровня"
          />
          <div className="gauge__side">
            <div className="card__big">{rub(savings.total_saved_amount)}</div>
            <span className="lvltag card__hint">Уровень {avatar.level}</span>
            <div className="card__hint">
              {toNext === null
                ? "Максимальный уровень достигнут"
                : `ещё ${rub(toNext)} — и вырастет`}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="metric">
          <span className="metric__ico" aria-hidden>
            🔥
          </span>
          <div>
            <div className="metric__n">{streak.streak_count}</div>
            <div className="metric__cap">
              недель подряд с покупками
              {streak.last_active_week ? ` · ${streak.last_active_week}` : ""}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card__k">Коллекция</div>
        <ul className="chips" aria-label="Разблокированные кастомизации">
          {avatar.unlocked_customizations.map((c) => (
            <li key={c} className="chip">
              <span className="chip__ico" aria-hidden>
                {CHIP_ICON[c] ?? "✨"}
              </span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
