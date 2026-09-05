/**
 * T029 / US2 — экран челленджа рендерит текст, прогресс и заметки; корректно
 * показывает пустое состояние.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Challenge } from "../../src/screens/Challenge";
import type { ChallengeScreenView } from "../../src/contract/types";

const withChallenge: ChallengeScreenView = {
  user_id: "u1",
  iso_week: "2026-W13",
  challenge: {
    challenge_id: "ch1",
    text: "Купите 3 раза категорию «baby_food» до 30 марта",
    mechanic_type: "category_repeat",
    generated_by: "ml_ranker",
    params: { category: "baby_food", n: 3, deadline: "2026-03-30T07:00:00Z" },
    progress: 2,
    target: 3,
    status: "active",
    valid_to: "2026-03-30T07:00:00Z",
    reward_amount: 24,
    within_budget: true,
  },
  notes: [],
};

describe("Challenge", () => {
  it("показывает текст челленджа и прогресс", () => {
    render(<Challenge view={withChallenge} />);
    expect(screen.getByText(/Сделайте 3 покупки в категории «детское питание»/)).toBeInTheDocument();
    expect(screen.getByText("2/3")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "67");
  });

  it("пустое состояние, если челленджа нет", () => {
    render(
      <Challenge view={{ user_id: "u1", iso_week: "2026-W13", challenge: null, notes: [] }} />,
    );
    expect(screen.getByText(/На этой неделе всё спокойно/)).toBeInTheDocument();
  });

  it("рендерит заметку про холодный старт", () => {
    render(
      <Challenge
        view={{ ...withChallenge, notes: ["cold_start_fallback"] }}
      />,
    );
    expect(screen.getByText(/по рабочему профилю/)).toBeInTheDocument();
  });
});
