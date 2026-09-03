/**
 * T019 / US1 — экран профиля рендерит уровень, прогресс-бар экономии и
 * разблокированные кастомизации из фикстуры.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProfileAvatar } from "../../src/screens/ProfileAvatar";
import type { ProfileScreenView } from "../../src/contract/types";

const baseView: ProfileScreenView = {
  user_id: "demo",
  display_name: "Родитель · демо",
  avatar: {
    level: 2,
    visual_stage: 3,
    state: "progressing",
    unlocked_customizations: ["starter_skin", "bronze_badge", "silver_badge"],
    last_transition_at: "2026-03-23T08:50:00Z",
  },
  savings: {
    total_saved_amount: 1720,
    current_threshold: 1500,
    next_threshold: 3500,
    progress_ratio: 0.11,
  },
  streak: { streak_count: 4, last_active_week: "2026-W13" },
};

describe("ProfileAvatar", () => {
  it("показывает уровень аватара", () => {
    render(<ProfileAvatar view={baseView} />);
    expect(screen.getByText("Уровень 2")).toBeInTheDocument();
  });

  it("рендерит прогресс-бар с корректным значением", () => {
    render(<ProfileAvatar view={baseView} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "11");
  });

  it("перечисляет разблокированные кастомизации", () => {
    render(<ProfileAvatar view={baseView} />);
    expect(screen.getByText("silver_badge")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it("на максимальном уровне показывает соответствующую подсказку", () => {
    render(
      <ProfileAvatar
        view={{
          ...baseView,
          avatar: { ...baseView.avatar, level: 4, visual_stage: 5, state: "max_level" },
          savings: { ...baseView.savings, next_threshold: null, progress_ratio: 1 },
        }}
      />,
    );
    expect(screen.getByText("Максимальный уровень достигнут")).toBeInTheDocument();
  });

  it("не содержит слов «ИИ»/«AI» (FR-035)", () => {
    const { container } = render(<ProfileAvatar view={baseView} />);
    expect(container.textContent ?? "").not.toMatch(/\bИИ\b|\bAI\b/i);
  });
});
