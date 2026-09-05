type IconFamily = "ui" | "category" | "collection";

interface Props {
  name: string;
  family?: IconFamily;
  className?: string;
}

const SPRITES: Record<IconFamily, string> = {
  ui: "/assets/growth/icons/ui-sprite.svg",
  category: "/assets/growth/icons/category-sprite.svg",
  collection: "/assets/growth/icons/collection-sprite.svg",
};

export function Icon({ name, family = "ui", className }: Props) {
  const outline = family !== "collection";

  return (
    <svg
      className={["app-icon", `app-icon--${family}`, className].filter(Boolean).join(" ")}
      aria-hidden="true"
      focusable="false"
      fill={outline ? "none" : undefined}
      stroke={outline ? "currentColor" : undefined}
      strokeWidth={outline ? 1.9 : undefined}
      strokeLinecap={outline ? "round" : undefined}
      strokeLinejoin={outline ? "round" : undefined}
    >
      <use href={`${SPRITES[family]}#${name}`} />
    </svg>
  );
}
