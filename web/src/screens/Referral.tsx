import type { ReferralScreenView } from "../contract/types";

interface Props {
  view: ReferralScreenView;
}

const STATUS_LABEL: Record<string, string> = {
  invited: "Приглашён",
  registered: "Зарегистрировался",
  purchase_confirmed: "Совершил первую покупку",
  reward_released: "Награда начислена",
  blocked: "Заблокирован",
  expired: "Срок истёк",
};

const BLOCK_LABEL: Record<string, string> = {
  self_referral: "самоприглашение",
  antifraud_block: "антифрод",
  window_expired: "истёк срок",
};

const rub = (n: number) =>
  new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(n);

export function Referral({ view }: Props) {
  return (
    <section className="screen screen--referral" aria-labelledby="referral-title">
      <h1 id="referral-title">Пригласить друга</h1>

      <div className="referral__link" aria-label="Ссылка-приглашение">
        {view.invite_link}
      </div>
      <div className="referral__summary">
        Начислено за друзей: <strong>{rub(view.released_reward_total)}</strong>
        {view.budget_remaining_this_week != null && (
          <span className="referral__budget">
            {" "}
            · доступно на этой неделе {rub(view.budget_remaining_this_week)}
          </span>
        )}
      </div>

      {view.referrals.length === 0 ? (
        <p className="referral__empty">Пока никого не пригласили.</p>
      ) : (
        <ul className="referral__list">
          {view.referrals.map((r) => (
            <li key={r.referral_id} className="referral__item" data-status={r.status}>
              <span className="referral__alias">{r.invitee_alias ?? "друг"}</span>
              <span className="referral__status">
                {STATUS_LABEL[r.status] ?? r.status}
                {r.block_reason ? ` (${BLOCK_LABEL[r.block_reason] ?? r.block_reason})` : ""}
              </span>
              <span className="referral__reward">
                {r.reward_amount > 0 ? rub(r.reward_amount) : "—"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
