import { StatusPill } from "../components/StatusPill";
import { Icon } from "../components/Icon";
import type { ReferralScreenView } from "../contract/types";

interface Props {
  view: ReferralScreenView;
}

const STATUS: Record<string, { label: string; tone: "good" | "wait" | "bad" }> = {
  invited: { label: "Приглашён", tone: "wait" },
  registered: { label: "Зарегистрировался", tone: "wait" },
  purchase_confirmed: { label: "Совершил покупку", tone: "good" },
  reward_released: { label: "Награда начислена", tone: "good" },
  blocked: { label: "Заблокирован", tone: "bad" },
  expired: { label: "Срок истёк", tone: "bad" },
};

const BLOCK_LABEL: Record<string, string> = {
  self_referral: "самоприглашение",
  antifraud_block: "антифрод",
  window_expired: "истёк срок",
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);

function copy(text: string): void {
  try {
    void navigator.clipboard?.writeText(text);
  } catch {
    /* демо: буфер обмена недоступен — не критично */
  }
}

function displayAlias(value?: string | null): string {
  const clean = (value ?? "друг").replace(/^d-/, "");
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

export function Referral({ view }: Props) {
  return (
    <section className="screen" aria-labelledby="referral-title">
      <div className="screen-heading">
        <span className="screen__eyebrow">Вместе выгоднее</span>
        <h1 id="referral-title">Пригласить друга</h1>
        <p>Награда появится только после первой подтверждённой покупки друга.</p>
      </div>

      <div className="card card--dark referral-hero">
        <div className="referral-hero__icon"><Icon name="friends" /></div>
        <div className="card__k">Ссылка-приглашение</div>
        <div className="ref__link">
          <code>{view.invite_link}</code>
          <button type="button" className="ref__copy" onClick={() => copy(view.invite_link)}>
            Копировать
          </button>
        </div>
        <div className="ref__sum">
          Уже начислено: <strong>{rub(view.released_reward_total)}</strong>
        </div>
      </div>

      <div className="referral-rule">
        <Icon name="check" />
        <span><strong>Честное условие</strong>Сначала покупка и проверка чека — потом награда обеим сторонам.</span>
      </div>

      {view.referrals.length === 0 ? (
        <div className="card">
          <p className="ref__empty">Пока никого не пригласили. Поделитесь ссылкой 👆</p>
        </div>
      ) : (
        <ul className="ref__list">
          {view.referrals.map((r) => {
            const st = STATUS[r.status] ?? { label: r.status, tone: "wait" as const };
            const alias = displayAlias(r.invitee_alias);
            return (
              <li key={r.referral_id} className="ref__item">
                <span className="ref__ava" aria-hidden>
                  {alias.slice(0, 1).toUpperCase()}
                </span>
                <div>
                  <div className="ref__alias">{alias}</div>
                  <StatusPill tone={st.tone}>
                    {st.label}
                    {r.block_reason ? ` · ${BLOCK_LABEL[r.block_reason] ?? r.block_reason}` : ""}
                  </StatusPill>
                </div>
                <span
                  className={r.reward_amount > 0 ? "ref__reward" : "ref__reward ref__reward--muted"}
                >
                  {r.reward_amount > 0 ? `+${rub(r.reward_amount)}` : "—"}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
