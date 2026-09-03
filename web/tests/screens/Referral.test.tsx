/**
 * T062 / US5 — экран рефералов рендерит список, статусы, начисленную награду и
 * причины блокировки; пустое состояние.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Referral } from "../../src/screens/Referral";
import type { ReferralScreenView } from "../../src/contract/types";

const base: ReferralScreenView = {
  user_id: "u1",
  invite_link: "https://x5.local/i/u1",
  released_reward_total: 15,
  budget_remaining_this_week: 24,
  referrals: [
    {
      referral_id: "r1",
      invitee_alias: "anna",
      status: "reward_released",
      invited_at: "2026-03-10T09:00:00Z",
      window_deadline: "2026-04-10T10:00:00Z",
      reward_amount: 15,
      block_reason: null,
    },
    {
      referral_id: "r2",
      invitee_alias: "oleg",
      status: "registered",
      invited_at: "2026-03-20T09:00:00Z",
      window_deadline: "2026-04-20T10:00:00Z",
      reward_amount: 0,
      block_reason: null,
    },
  ],
};

describe("Referral", () => {
  it("показывает ссылку-приглашение и сумму начислений", () => {
    render(<Referral view={base} />);
    expect(screen.getByText("https://x5.local/i/u1")).toBeInTheDocument();
    expect(screen.getByText(/Начислено за друзей/)).toBeInTheDocument();
  });

  it("рендерит все рефералы с их статусами", () => {
    render(<Referral view={base} />);
    expect(screen.getByText("Награда начислена")).toBeInTheDocument();
    expect(screen.getByText("Зарегистрировался")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("показывает причину блокировки", () => {
    render(
      <Referral
        view={{
          ...base,
          referrals: [
            {
              referral_id: "r3",
              invitee_alias: "alt",
              status: "blocked",
              invited_at: "2026-03-01T00:00:00Z",
              window_deadline: null,
              reward_amount: 0,
              block_reason: "self_referral",
            },
          ],
        }}
      />,
    );
    expect(screen.getByText(/самоприглашение/)).toBeInTheDocument();
  });

  it("пустое состояние", () => {
    render(<Referral view={{ ...base, referrals: [] }} />);
    expect(screen.getByText(/Пока никого не пригласили/)).toBeInTheDocument();
  });
});
