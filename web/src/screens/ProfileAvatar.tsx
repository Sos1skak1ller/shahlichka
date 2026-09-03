import { AvatarStage } from "../components/AvatarStage";
import { ProgressBar } from "../components/ProgressBar";
import type { ProfileScreenView } from "../contract/types";

interface Props {
  view: ProfileScreenView;
}

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(n);

export function ProfileAvatar({ view }: Props) {
  const { avatar, savings, streak } = view;
  const toNext =
    savings.next_threshold === null
      ? null
      : Math.max(0, savings.next_threshold - savings.total_saved_amount);

  return (
    <section className="screen screen--profile" aria-labelledby="profile-title">
      <h1 id="profile-title">Мой прогресс</h1>

      <AvatarStage
        level={avatar.level}
        visualStage={avatar.visual_stage}
        state={avatar.state}
      />

      <div className="savings">
        <div className="savings__total">
          Накоплено экономии: <strong>{rub(savings.total_saved_amount)}</strong>
        </div>
        <ProgressBar ratio={savings.progress_ratio} label="Прогресс до следующего уровня" />
        {toNext !== null ? (
          <div className="savings__hint">До следующего уровня: {rub(toNext)}</div>
        ) : (
          <div className="savings__hint">Максимальный уровень достигнут</div>
        )}
      </div>

      <div className="streak">
        Серия недель с покупками: <strong>{streak.streak_count}</strong>
        {streak.last_active_week ? ` (последняя: ${streak.last_active_week})` : ""}
      </div>

      <ul className="customizations" aria-label="Разблокированные кастомизации">
        {avatar.unlocked_customizations.map((c) => (
          <li key={c} className="customizations__item">
            {c}
          </li>
        ))}
      </ul>
    </section>
  );
}
