import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Mascot, mascotAsset } from "../src/components/Mascot";

describe("Персонаж на общей поверхности", () => {
  it("сохраняет исходные портреты для лендинга", () => {
    expect(mascotAsset(3)).toBe("/assets/growth/avatars/leaf-to-orange-v2/stage-03-fruit-set.png");
    render(<Mascot stage={3} state="progressing" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("использует отдельную бесшовную версию и повторяет короткое приветствие", () => {
    render(<Mascot stage={3} state="progressing" live />);
    const originalImage = screen.getByRole("img", { name: /Завязь, этап 3 из 5/ });
    expect(originalImage).toHaveAttribute("src", "/assets/growth/avatars/leaf-to-orange-seamless-v1/stage-03-fruit-set.png");
    const greeting = screen.getByRole("button", { name: "Поздороваться с аватаром «Завязь»" });
    greeting.focus();
    fireEvent.click(greeting);
    const replayedImage = screen.getByRole("img", { name: /Завязь, этап 3 из 5/ });
    expect(replayedImage).not.toBe(originalImage);
    expect(replayedImage).toHaveAttribute("src", originalImage.getAttribute("src"));
    expect(greeting).toHaveFocus();
    expect(greeting).toHaveAttribute("type", "button");
  });

  it("не создаёт несуществующих стадий для крайних значений", () => {
    expect(mascotAsset(0, "seamless")).toMatch(/stage-01-bud.png$/);
    expect(mascotAsset(9, "seamless")).toMatch(/stage-05-orange.png$/);
  });
});
