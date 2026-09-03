interface Props {
  /** визуальная стадия аватара, 1..5 */
  stage: number;
  state: "progressing" | "level_up_pending" | "max_level";
  /** нет покупок на этой неделе → маскот «высыхает» */
  dried?: boolean;
}

/** Имя маскота по стадии: 1 — Листик, дальше — Апельсинка (референс Перекрёстка). */
export function mascotName(stage: number): string {
  return stage <= 1 ? "Листик" : "Апельсинка";
}

type Accessory = "none" | "scarf" | "medal" | "crown";

function accessoryFor(stage: number): Accessory {
  if (stage >= 5) return "crown";
  if (stage >= 4) return "medal";
  if (stage >= 3) return "scarf";
  return "none";
}

const HOODIE = "#1f4a2c";
const HOODIE_DARK = "#173a22";
const SHOE = "#f5f1e6";

export function Mascot({ stage, state, dried = false }: Props) {
  const s = Math.min(Math.max(stage, 1), 5);
  const kind: "leaf" | "orange" = s <= 1 ? "leaf" : "orange";
  const acc = accessoryFor(s);

  const skin = dried ? "#c69a63" : kind === "leaf" ? "#a6d968" : "#f6a94b";
  const headFill = dried
    ? kind === "leaf"
      ? "#c7a56d"
      : "#c99a5f"
    : kind === "leaf"
      ? "url(#leafGrad)"
      : "url(#orangeGrad)";
  const headStroke = dried ? "#8a6a3d" : kind === "leaf" ? "#5aa833" : "#e07d18";

  return (
    <svg
      className={`mascot${dried ? " mascot--dried" : ""}`}
      viewBox="0 0 200 200"
      role="img"
      aria-label={`${mascotName(s)}${dried ? ", подсох — давно не было покупок" : `, стадия ${s}`}`}
    >
      <defs>
        <linearGradient id="leafGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#b6e46f" />
          <stop offset="1" stopColor="#6cb63c" />
        </linearGradient>
        <radialGradient id="orangeGrad" cx="0.4" cy="0.35" r="0.8">
          <stop offset="0" stopColor="#ffc164" />
          <stop offset="1" stopColor="#f2901f" />
        </radialGradient>
      </defs>

      <ellipse cx="100" cy="188" rx="46" ry="8" fill="rgba(20,40,25,.12)" />

      {acc === "crown" && (
        <path
          d="M66 22l13 12 21-18 21 18 13-12-5 26H71z"
          fill="#f4b740"
          stroke="#d99a1e"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
      )}

      {/* ноги + кроссовки */}
      <rect x="84" y="150" width="12" height="20" rx="5" fill={HOODIE} />
      <rect x="104" y="150" width="12" height="20" rx="5" fill={HOODIE} />
      <ellipse cx="84" cy="174" rx="13" ry="7" fill={SHOE} stroke="#dcd6c4" strokeWidth="1.5" />
      <ellipse cx="116" cy="174" rx="13" ry="7" fill={SHOE} stroke="#dcd6c4" strokeWidth="1.5" />

      {/* тело в худи (маленькое, пухлое) */}
      <path
        d="M64 128c0-14 14-22 36-22s36 8 36 22v18c0 9-7 16-16 16H80c-9 0-16-7-16-16z"
        fill={HOODIE}
      />
      <path d="M70 128q30 16 60 0v8q-30 14 -60 0z" fill={HOODIE_DARK} />
      {/* ручки-варежки */}
      <circle cx="60" cy="138" r="9" fill={skin} />
      <circle cx="140" cy="138" r="9" fill={skin} />
      {/* клевер X5 */}
      <g transform="translate(100 140)" fill="#fff" opacity="0.96">
        <circle cx="0" cy="-5.5" r="4.6" />
        <circle cx="5.5" cy="0" r="4.6" />
        <circle cx="0" cy="5.5" r="4.6" />
        <circle cx="-5.5" cy="0" r="4.6" />
        <circle cx="0" cy="0" r="2.6" fill={HOODIE} />
      </g>

      {acc === "scarf" && (
        <>
          <path d="M72 108q28 15 56 0l-3 12q-25 12 -50 0z" fill="#3aa544" />
          <path d="M120 118l9 26 11-4-7-27z" fill="#2e8a38" />
        </>
      )}

      {/* ГОЛОВА — крупная */}
      {kind === "leaf" ? (
        <path
          d="M100 8c22 20 34 44 34 62 0 22-15 38-34 38S66 92 66 70c0-18 12-42 34-62z"
          fill={headFill}
          stroke={headStroke}
          strokeWidth="3"
        />
      ) : (
        <>
          <circle cx="100" cy="66" r="54" fill={headFill} stroke={headStroke} strokeWidth="3" />
          {[
            [78, 42], [116, 40], [128, 70], [70, 82], [98, 100], [120, 92], [88, 58], [106, 50],
          ].map(([cx, cy], i) => (
            <circle key={i} cx={cx} cy={cy} r="2.3" fill={dried ? "#a67a41" : "#e07d18"} opacity=".4" />
          ))}
          <path d="M104 16l-3-12" stroke={dried ? "#8a6a3d" : "#7a5a2a"} strokeWidth="5" strokeLinecap="round" />
          <path
            d={dried ? "M100 6q20 -2 27 12q-18 8 -27 -12z" : "M100 4q22 -8 31 6q-15 15 -31 -6z"}
            fill={dried ? "#8f9a5c" : "#5aa833"}
            stroke={dried ? "#6f7a44" : "#4f9e34"}
            strokeWidth="2"
          />
        </>
      )}

      {/* ЛИЦО */}
      {dried ? (
        <g>
          <path d="M80 66q7 -6 14 0" stroke="#5a4326" strokeWidth="3.5" fill="none" strokeLinecap="round" />
          <path d="M106 66q7 -6 14 0" stroke="#5a4326" strokeWidth="3.5" fill="none" strokeLinecap="round" />
          <circle cx="87" cy="72" r="4" fill="#3f2f1a" />
          <circle cx="113" cy="72" r="4" fill="#3f2f1a" />
          <path d="M91 88q9 -4 18 0" stroke="#5a4326" strokeWidth="3" fill="none" strokeLinecap="round" />
        </g>
      ) : (
        <g>
          <circle cx="86" cy="68" r="6.5" fill="#1e2c1c" />
          <circle cx="114" cy="68" r="6.5" fill="#1e2c1c" />
          <circle cx="88.4" cy="65.6" r="2.2" fill="#fff" />
          <circle cx="116.4" cy="65.6" r="2.2" fill="#fff" />
          {state === "level_up_pending" && (
            <>
              <path d="M78 58q8 -7 16 0" stroke="#1e2c1c" strokeWidth="3" fill="none" strokeLinecap="round" />
              <path d="M106 58q8 -7 16 0" stroke="#1e2c1c" strokeWidth="3" fill="none" strokeLinecap="round" />
            </>
          )}
          <path
            d={state === "max_level" ? "M84 82q16 16 32 0" : "M87 82q13 12 26 0"}
            stroke="#1e2c1c"
            strokeWidth="3.5"
            fill="none"
            strokeLinecap="round"
          />
          <circle cx="76" cy="80" r="5" fill="#f2846a" opacity=".45" />
          <circle cx="124" cy="80" r="5" fill="#f2846a" opacity=".45" />
        </g>
      )}

      {acc === "medal" && (
        <>
          <path d="M92 118l6 14M108 118l-6 14" stroke="#d99a1e" strokeWidth="3" />
          <circle cx="100" cy="136" r="10" fill="#f4b740" stroke="#d99a1e" strokeWidth="2.5" />
          <path d="M100 129l2.2 4.6 5 .7-3.6 3.6.9 5-4.5-2.4-4.5 2.4.9-5-3.6-3.6 5-.7z" fill="#fff8e6" />
        </>
      )}

      {dried ? (
        <>
          <path className="mascot__leaf" d="M148 58q10 -4 14 6q-10 6 -14 -6z" fill="#b98f52" />
          <path className="mascot__leaf" d="M44 96q-9 2 -10 12q10 2 10 -12z" fill="#a67a41" />
        </>
      ) : (
        s >= 5 && (
          <>
            <path className="mascot__spark" d="M36 40l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" fill="#f4b740" />
            <path className="mascot__spark" d="M162 32l2.5 6 6 2.5-6 2.5-2.5 6-2.5-6-6-2.5 6-2.5z" fill="#f4b740" />
            <path className="mascot__spark" d="M168 92l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#6cb63c" />
          </>
        )
      )}
    </svg>
  );
}
