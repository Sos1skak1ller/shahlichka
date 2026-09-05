import { useState } from "react";

interface Props {
  /** Визуальная стадия аватара, 1..5. */
  stage: number;
  state: "progressing" | "level_up_pending" | "max_level";
  live?: boolean;
}

const STAGES = [
  { name: "Почка", file: "stage-01-bud.png" },
  { name: "Листик", file: "stage-02-leaf.png" },
  { name: "Завязь", file: "stage-03-fruit-set.png" },
  { name: "Созревающий плод", file: "stage-04-ripening.png" },
  { name: "Апельсинка", file: "stage-05-orange.png" },
] as const;

const ASSET_ROOT = "/assets/growth/avatars/leaf-to-orange-v2";

function normalizeStage(stage: number): number {
  return Math.min(Math.max(Math.round(stage), 1), STAGES.length);
}

export function mascotName(stage: number): string {
  return STAGES[normalizeStage(stage) - 1].name;
}

export function mascotAsset(stage: number, variant: "portrait" | "seamless" = "portrait"): string {
  const root = variant === "seamless" ? "/assets/growth/avatars/leaf-to-orange-seamless-v1" : ASSET_ROOT;
  return `${root}/${STAGES[normalizeStage(stage) - 1].file}`;
}

export function Mascot({ stage, state, live = false }: Props) {
  const [greeting, setGreeting] = useState(0);
  const normalized = normalizeStage(stage);
  const current = STAGES[normalized - 1];
  const status = state === "max_level" ? ", максимальная форма" : "";

  const avatar = (
      <img key={`${normalized}-${greeting}`}
        src={mascotAsset(normalized, live ? "seamless" : "portrait")}
        alt={`${current.name}, этап ${normalized} из ${STAGES.length}${status}`}
        width="1024" height="1536" draggable={false}
      />
  );

  return (
    <figure className={live ? "mascot mascot--live" : "mascot"} data-stage={normalized} data-state={state}>
      {live ? (
        <button type="button" className="mascot__greeting"
          aria-label={`Поздороваться с аватаром «${current.name}»`}
          title="Поздороваться — не влияет на прогресс"
          onClick={() => setGreeting((value) => value + 1)}>
          {avatar}
        </button>
      ) : avatar}
    </figure>
  );
}
