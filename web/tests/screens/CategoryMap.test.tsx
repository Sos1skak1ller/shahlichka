import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CategoryMap } from "../../src/screens/CategoryMap";
import type { ProfileScreenView } from "../../src/contract/types";

const view: ProfileScreenView = {
  user_id: "demo",
  avatar: {
    level: 1,
    visual_stage: 2,
    state: "progressing",
    unlocked_customizations: ["starter_skin"],
  },
  savings: {
    total_saved_amount: 800,
    current_threshold: 500,
    next_threshold: 1500,
    progress_ratio: 0.3,
  },
  streak: { streak_count: 2, last_active_week: "2026-W13" },
  history: [
    { ts: "2026-03-20T00:00:00Z", kind: "purchase", title: "Покупка", detail: "dairy, hygiene", amount: 100 },
  ],
};

describe("CategoryMap", () => {
  it("строит карту из категорий в подтверждённой истории", () => {
    render(<CategoryMap view={view} />);
    expect(screen.getByRole("heading", { name: "Мои категории" })).toBeInTheDocument();
    expect(screen.getByText("2 из 7")).toBeInTheDocument();
    expect(screen.getByText("Пора вернуться")).toBeInTheDocument();
  });

  it("явно маркирует синтетический характер рекомендации", () => {
    render(<CategoryMap view={view} />);
    expect(screen.getByText(/синтетической истории покупок/i)).toBeInTheDocument();
  });
});
