interface Props {
  level: number;
  visualStage: number;
  state: "progressing" | "level_up_pending" | "max_level";
}

const STAGE_GLYPH = ["🌱", "🌿", "🌳", "🏆", "👑"];

export function AvatarStage({ level, visualStage, state }: Props) {
  const glyph = STAGE_GLYPH[Math.min(visualStage - 1, STAGE_GLYPH.length - 1)];
  return (
    <div className="avatar-stage" data-state={state}>
      <div className="avatar-stage__glyph" aria-hidden>
        {glyph}
      </div>
      <div className="avatar-stage__meta">
        <div className="avatar-stage__level">Уровень {level}</div>
        <div className="avatar-stage__state">
          {state === "max_level"
            ? "Максимальный уровень"
            : state === "level_up_pending"
              ? "Почти новый уровень"
              : "Копим экономию"}
        </div>
      </div>
    </div>
  );
}
