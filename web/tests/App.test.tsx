import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { App } from "../src/App";
import { Icon } from "../src/components/Icon";

describe("карусель демо-аккаунтов", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
  });

  afterEach(cleanup);

  it("переключает аккаунты кнопками и показывает следующую форму аватара", () => {
    render(<App />);

    expect(screen.getByText("Кирилл · Завязь")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Следующий аккаунт" }));

    expect(screen.getByText("София · Созревающий плод")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Созревающий плод, этап 4 из 5/ })).toBeInTheDocument();
  });

  it("поддерживает горизонтальный свайп по телефону", () => {
    render(<App />);
    const viewport = screen.getByLabelText("Телефон с аккаунтом; листайте влево или вправо");

    fireEvent.touchStart(viewport, { changedTouches: [{ clientX: 240 }] });
    fireEvent.touchEnd(viewport, { changedTouches: [{ clientX: 120 }] });

    expect(screen.getByText("София · Созревающий плод")).toBeInTheDocument();
  });

  it("даёт открыть все пять стадий напрямую", () => {
    render(<App />);

    const stages = [
      ["Ника, этап 1", /Почка, этап 1 из 5/],
      ["Марина, этап 2", /Листик, этап 2 из 5/],
      ["Кирилл, этап 3", /Завязь, этап 3 из 5/],
      ["София, этап 4", /Созревающий плод, этап 4 из 5/],
      ["Максим, этап 5", /Апельсинка, этап 5 из 5/],
    ] as const;

    for (const [buttonName, imageName] of stages) {
      fireEvent.click(screen.getByRole("button", { name: buttonName }));
      expect(screen.getByRole("img", { name: imageName })).toBeInTheDocument();
    }
  });

  it("открывает выбранный на лендинге аккаунт по ссылке", () => {
    window.history.replaceState({}, "", "/?account=demo-sofia");
    render(<App />);
    expect(screen.getByText("София · Созревающий плод")).toBeInTheDocument();
  });

  it("безопасно возвращается к основному профилю при неизвестном аккаунте", () => {
    window.history.replaceState({}, "", "/?account=unknown");
    render(<App />);
    expect(screen.getByText("Кирилл · Завязь")).toBeInTheDocument();
  });

  it("использует общий знак X5 со ссылкой на лендинг", () => {
    render(<App />);
    const brands = screen.getAllByRole("link", { name: "X5 Клуб · Рост — на главную" });
    expect(brands).toHaveLength(2);
    for (const brand of brands) {
      expect(brand).toHaveAttribute("href", "/landing");
      expect(within(brand).getByRole("img", { name: "X5" })).toHaveAttribute("src", "/assets/growth/brand/x5-logo.svg");
    }
  });

  it("сохраняет все четыре сценария и выбранный аккаунт при переходах", () => {
    window.history.replaceState({}, "", "/?account=demo-sofia");
    render(<App />);
    const navigation = within(screen.getByRole("navigation", { name: "Разделы" }));
    for (const [tab, title] of [["Цель", "Цель недели"], ["Категории", "Мои категории"], ["Друзья", "Пригласить друга"]]) {
      fireEvent.click(navigation.getByRole("button", { name: tab }));
      expect(navigation.getByRole("button", { name: tab })).toHaveAttribute("aria-current", "page");
      expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    }
    fireEvent.click(navigation.getByRole("button", { name: "Главная" }));
    expect(screen.getByRole("img", { name: /Созревающий плод, этап 4 из 5/ })).toBeInTheDocument();
  });

  it("не переключает аккаунт при вертикальном или отменённом жесте", () => {
    render(<App />);
    const viewport = screen.getByLabelText("Телефон с аккаунтом; листайте влево или вправо");
    fireEvent.touchStart(viewport, { changedTouches: [{ clientX: 240, clientY: 400 }] });
    fireEvent.touchEnd(viewport, { changedTouches: [{ clientX: 170, clientY: 100 }] });
    expect(screen.getByText("Кирилл · Завязь")).toBeInTheDocument();
    fireEvent.touchStart(viewport, { changedTouches: [{ clientX: 240, clientY: 400 }] });
    fireEvent.touchCancel(viewport);
    fireEvent.touchEnd(viewport, { changedTouches: [{ clientX: 100, clientY: 400 }] });
    expect(screen.getByText("Кирилл · Завязь")).toBeInTheDocument();
  });
});

describe("Icon", () => {
  afterEach(cleanup);

  it("задаёт контурные SVG-атрибуты на самом элементе для Safari", () => {
    const { container } = render(<Icon name="receipt" />);
    const svg = container.querySelector("svg");

    expect(svg).toHaveAttribute("fill", "none");
    expect(svg).toHaveAttribute("stroke", "currentColor");
    expect(svg).toHaveAttribute("stroke-linecap", "round");
  });
});
