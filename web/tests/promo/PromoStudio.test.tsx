import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "../../src/App";
import { PromoStudio } from "../../src/promo/PromoStudio";

describe("PromoStudio", () => {
  beforeEach(() => {
    const values = new Map<string, string>();
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: {
        clear: () => values.clear(),
        getItem: (key: string) => values.get(key) ?? null,
        removeItem: (key: string) => values.delete(key),
        setItem: (key: string, value: string) => values.set(key, value),
      },
    });
    window.localStorage.clear();
    window.history.replaceState({}, "", "/promo-studio");
  });

  it("явно помечает тестовые промо как не прошедшие проверку", () => {
    render(<PromoStudio />);

    expect(
      screen.getByText("Демо-набор · не прошёл проверку маркетолога"),
    ).toBeInTheDocument();
    expect(screen.getByText("Выгода на базовую корзину")).toBeInTheDocument();
  });

  it("создаёт промо с продуктовой целью и сохраняет его в списке", () => {
    render(<PromoStudio />);
    fireEvent.click(screen.getAllByRole("button", { name: /новое промо/i })[0]);

    fireEvent.change(screen.getByLabelText("Название *"), {
      target: { value: "Возвращаем молочную корзину" },
    });
    fireEvent.change(screen.getByLabelText("ID промо *"), {
      target: { value: "promo_dairy_return" },
    });
    fireEvent.change(screen.getByLabelText("Описание *"), {
      target: { value: "Вознаграждаем следующую покупку привычной категории" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить промо" }));

    expect(screen.getByText("Возвращаем молочную корзину")).toBeInTheDocument();
    expect(screen.getByText("promo_dairy_return")).toBeInTheDocument();
    expect(window.localStorage.getItem("x5-promo-studio-v1")).toContain(
      "promo_dairy_return",
    );
  });

  it("не позволяет сохранить процентную скидку больше 100%", () => {
    render(<PromoStudio />);
    fireEvent.click(screen.getAllByRole("button", { name: /новое промо/i })[0]);

    fireEvent.change(screen.getByLabelText("Размер скидки"), {
      target: { value: "101" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить промо" }));

    expect(
      screen.getByText("Процентная скидка не может превышать 100%"),
    ).toBeInTheDocument();
  });

  it("открывает редактор в фиксированной диалоговой панели и закрывает по Escape", () => {
    render(<PromoStudio />);
    fireEvent.click(screen.getAllByRole("button", { name: "Редактировать" })[0]);

    expect(screen.getByRole("dialog", { name: "Редактор промо" })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Редактор промо" })).not.toBeInTheDocument();
  });

  it("показывает прогноз и демонстрационный результат A/B-теста", () => {
    render(<PromoStudio />);
    fireEvent.click(
      screen.getAllByRole("button", { name: "Аналитика и превью" })[0],
    );

    expect(screen.getByText(/Синтетический прогноз/)).toBeInTheDocument();
    expect(screen.getByText("Экономический guardrail")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Результаты" }));
    expect(screen.getByText(/Демонстрация результата A\/B-теста/)).toBeInTheDocument();
    expect(screen.getByText("Автоматический вердикт")).toBeInTheDocument();
  });

  it("публикует одобренное промо и показывает его в клиентском X5 Рост", () => {
    render(<PromoStudio />);
    fireEvent.click(screen.getAllByRole("button", { name: "Редактировать" })[0]);
    fireEvent.change(screen.getAllByLabelText("Статус")[1], {
      target: { value: "approved" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить промо" }));

    fireEvent.click(
      screen.getAllByRole("button", { name: "Аналитика и превью" })[0],
    );
    fireEvent.click(screen.getByRole("button", { name: "В X5 Рост" }));
    fireEvent.change(screen.getByLabelText("Тестовый клиент"), {
      target: { value: "m2_oscillating" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Опубликовать" }));

    expect(screen.getByText("Промо опубликовано в X5 Рост")).toBeInTheDocument();
    expect(window.localStorage.getItem("x5-promo-studio-v1")).toContain("published");
    expect(window.localStorage.getItem("x5-growth-assignment-v1")).toContain("Артём");

    cleanup();
    window.history.pushState({}, "", "/");
    render(<App />);
    expect(
      screen.getByLabelText("Опубликованное персональное промо"),
    ).toBeInTheDocument();
    expect(screen.getByText("Привет, Артём")).toBeInTheDocument();
  });

  it("при нескольких published использует промо из текущего назначения", () => {
    render(<PromoStudio />);
    const pool = JSON.parse(
      window.localStorage.getItem("x5-promo-studio-v1") ?? "{}",
    );
    pool.promos[0].approval_status = "published";
    pool.promos[1].approval_status = "published";
    window.localStorage.setItem("x5-promo-studio-v1", JSON.stringify(pool));
    window.localStorage.setItem(
      "x5-growth-assignment-v1",
      JSON.stringify({
        promo_id: pool.promos[1].promo_id,
        client_id: "m2_cross_shopper",
        client_name: "Елена",
        client_description: "5 покупок в месяц · доля X5 36%",
        published_at: new Date().toISOString(),
      }),
    );

    cleanup();
    window.history.pushState({}, "", "/");
    render(<App />);

    expect(screen.getByText("Привет, Елена")).toBeInTheDocument();
    expect(screen.getByText(/Товары для дома/)).toBeInTheDocument();
  });

  it("обновляет уже открытый X5 Рост после нового назначения", () => {
    render(<PromoStudio />);
    const pool = JSON.parse(
      window.localStorage.getItem("x5-promo-studio-v1") ?? "{}",
    );
    pool.promos[0].approval_status = "published";
    window.localStorage.setItem("x5-promo-studio-v1", JSON.stringify(pool));
    const assignment = {
      promo_id: pool.promos[0].promo_id,
      client_id: "m2_steady",
      client_name: "Анна",
      client_description: "4 покупки в месяц · доля X5 52%",
      published_at: new Date().toISOString(),
    };
    window.localStorage.setItem(
      "x5-growth-assignment-v1",
      JSON.stringify(assignment),
    );

    cleanup();
    window.history.pushState({}, "", "/");
    render(<App />);
    expect(screen.getByText("Привет, Анна")).toBeInTheDocument();

    window.localStorage.setItem(
      "x5-growth-assignment-v1",
      JSON.stringify({
        ...assignment,
        client_id: "m2_oscillating",
        client_name: "Артём",
      }),
    );
    fireEvent(window, new StorageEvent("storage", {
      key: "x5-growth-assignment-v1",
    }));

    expect(screen.getByText("Привет, Артём")).toBeInTheDocument();
  });

  it("помечает предыдущее промо как снятое с публикации в открытой админке", () => {
    render(<PromoStudio />);
    const pool = JSON.parse(
      window.localStorage.getItem("x5-promo-studio-v1") ?? "{}",
    );
    pool.promos[0].approval_status = "published";
    pool.promos[1].approval_status = "approved";
    window.localStorage.setItem("x5-promo-studio-v1", JSON.stringify(pool));
    window.localStorage.setItem(
      "x5-growth-assignment-v1",
      JSON.stringify({
        promo_id: pool.promos[0].promo_id,
        client_id: "m2_steady",
        client_name: "Анна",
        client_description: "4 покупки в месяц · доля X5 52%",
        published_at: new Date().toISOString(),
      }),
    );
    fireEvent(window, new StorageEvent("storage", {
      key: "x5-promo-studio-v1",
    }));

    const secondCard = screen
      .getByText("Выгода на товары для дома")
      .closest(".ps-promo-card");
    expect(secondCard).not.toBeNull();
    fireEvent.click(
      within(secondCard as HTMLElement).getByRole("button", {
        name: "Аналитика и превью",
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "В X5 Рост" }));
    fireEvent.click(screen.getByRole("button", { name: "Опубликовать" }));
    fireEvent.keyDown(window, { key: "Escape" });

    const firstCard = screen
      .getByText("Выгода на базовую корзину")
      .closest(".ps-promo-card");
    expect(within(firstCard as HTMLElement).getByText("Снято с публикации")).toBeInTheDocument();
    expect(within(secondCard as HTMLElement).getByText("Опубликовано")).toBeInTheDocument();
  });
});
