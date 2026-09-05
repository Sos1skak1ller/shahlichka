import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { App } from "../../src/App";

describe("LandingPage", () => {
  afterEach(() => {
    window.history.replaceState({}, "", "/");
  });

  it("открывается на отдельном маршруте и ведёт в оба демо-контура", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Экономия, которая растёт вместе с вами" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /демо клиента/i })[0]).toHaveAttribute("href", "/");
    expect(screen.getAllByRole("link", { name: /Promo Studio/i })[0]).toHaveAttribute(
      "href",
      "/promo-studio",
    );
    expect(screen.getByText("+5 п.п.")).toBeInTheDocument();
    expect(screen.queryByText("+1,5 п.п.")).not.toBeInTheDocument();
  });

  it("переключает шаги продуктового цикла", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);

    const rewardStep = screen.getByRole("button", { name: /Награда прошла лимит/i });
    fireEvent.click(rewardStep);

    expect(rewardStep).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Шаг 4 из 5")).toBeInTheDocument();
  });

  it("использует оригинальный знак и показывает категории как прототип", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);
    for (const logo of screen.getAllByRole("img", { name: "X5" })) {
      expect(logo).toHaveAttribute("src", "/assets/growth/brand/x5-logo.svg");
    }
    expect(screen.getByText("Категории · UI-прототип")).toBeInTheDocument();
  });

  it("согласованно переключает аватар, имя, экономию и ссылку на аккаунт", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);
    const carousel = within(screen.getByRole("region", { name: "Демоаккаунты" }));
    expect(carousel.getByRole("heading", { name: "Привет, Кирилл" })).toBeInTheDocument();
    fireEvent.click(carousel.getByRole("button", { name: "Следующий аккаунт" }));
    expect(carousel.getByRole("heading", { name: "Привет, София" })).toBeInTheDocument();
    expect(carousel.getByRole("img", { name: "Созревающий плод, этап 4 из 5" })).toBeInTheDocument();
    expect(carousel.getByText(/4\s820 ₽/)).toBeInTheDocument();
    expect(carousel.getByRole("progressbar")).toHaveAttribute("value", "38");
    expect(carousel.getByRole("link", { name: /Открыть аккаунт/ })).toHaveAttribute("href", "/?account=demo-sofia");
  });

  it("показывает максимум и циклически переключает аккаунты клавиатурой", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Максим, Апельсинка, этап 5" }));
    const carousel = screen.getByRole("region", { name: "Демоаккаунты" });
    expect(within(carousel).getByText("Максимальная форма открыта")).toBeInTheDocument();
    fireEvent.keyDown(carousel, { key: "ArrowRight" });
    expect(within(carousel).getByRole("heading", { name: "Привет, Ника" })).toBeInTheDocument();
    fireEvent.keyDown(carousel, { key: "ArrowLeft" });
    expect(within(carousel).getByRole("heading", { name: "Привет, Максим" })).toBeInTheDocument();
  });

  it("различает горизонтальный свайп и вертикальную прокрутку", () => {
    window.history.replaceState({}, "", "/landing");
    render(<App />);
    const carousel = screen.getByRole("region", { name: "Демоаккаунты" });
    fireEvent.touchStart(carousel, { touches: [{ clientX: 220, clientY: 300 }] });
    fireEvent.touchEnd(carousel, { changedTouches: [{ clientX: 200, clientY: 100 }] });
    expect(within(carousel).getByRole("heading", { name: "Привет, Кирилл" })).toBeInTheDocument();
    fireEvent.touchStart(carousel, { touches: [{ clientX: 220, clientY: 300 }] });
    fireEvent.touchEnd(carousel, { changedTouches: [{ clientX: 100, clientY: 310 }] });
    expect(within(carousel).getByRole("heading", { name: "Привет, София" })).toBeInTheDocument();
  });

  it("размещает клиентский опыт перед профессиональным контуром", () => {
    window.history.replaceState({}, "", "/landing");
    const { container } = render(<App />);
    const sections = Array.from(container.querySelectorAll("main > section[id]"), (section) => section.id);
    expect(sections).toEqual(["product", "avatars", "how-it-works", "team", "pilot"]);
  });

  it("закрывает мобильное меню по Escape и возвращает фокус", () => {
    window.history.replaceState({}, "", "/landing");
    const { container } = render(<App />);
    const menu = container.querySelector("details")!;
    menu.open = true;
    fireEvent.keyDown(menu, { key: "Escape" });
    expect(menu.open).toBe(false);
    expect(screen.getByLabelText("Открыть меню")).toHaveFocus();
  });
});
