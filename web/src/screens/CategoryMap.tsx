import { Icon } from "../components/Icon";
import type { ProfileScreenView } from "../contract/types";

interface Props {
  view: ProfileScreenView;
}

const CATEGORY_META = [
  { id: "baby_food", icon: "baby-food", title: "Детское питание", hint: "В привычном ритме" },
  { id: "diapers", icon: "diapers", title: "Подгузники", hint: "В привычном ритме" },
  { id: "dairy", icon: "dairy", title: "Молочные продукты", hint: "Покупали недавно" },
  { id: "hygiene", icon: "hygiene", title: "Гигиена", hint: "Пора вернуться" },
  { id: "snacks", icon: "snacks", title: "Снеки", hint: "Категория открыта" },
  { id: "groceries", icon: "groceries", title: "Базовая корзина", hint: "Ещё не открыта" },
  { id: "household", icon: "household", title: "Для дома", hint: "Ещё не открыта" },
] as const;

function purchasedCategories(view: ProfileScreenView): Set<string> {
  const categories = new Set<string>();
  for (const item of view.history ?? []) {
    if (item.kind !== "purchase" || !item.detail) continue;
    for (const category of item.detail.split(",")) categories.add(category.trim());
  }
  return categories;
}

export function CategoryMap({ view }: Props) {
  const purchased = purchasedCategories(view);
  const opened = CATEGORY_META.filter((category) => purchased.has(category.id)).length;

  return (
    <section className="screen category-screen" aria-labelledby="category-title">
      <div className="screen-heading">
        <span className="screen__eyebrow">Персональный маршрут</span>
        <h1 id="category-title">Мои категории</h1>
        <p>Карта растёт от реальных покупок и не требует отдельной награды.</p>
      </div>

      <div className="category-overview">
        <div>
          <span>Открыто</span>
          <strong>{opened} из {CATEGORY_META.length}</strong>
        </div>
        <Icon name="progress" />
      </div>

      <ul className="category-grid" aria-label="Карта категорий">
        {CATEGORY_META.map((category) => {
          const isOpen = purchased.has(category.id);
          const needsAttention = category.id === "hygiene" && isOpen;
          return (
            <li
              key={category.id}
              className="category-tile"
              data-open={isOpen}
              data-attention={needsAttention}
            >
              <span className="category-tile__icon"><Icon family="category" name={category.icon} /></span>
              <strong>{category.title}</strong>
              <small>{isOpen ? category.hint : "Откроется после покупки"}</small>
            </li>
          );
        })}
      </ul>

      <article className="category-next">
        <span className="category-next__icon"><Icon name="clock" /></span>
        <div>
          <span>Следующее полезное действие</span>
          <h2>Проверьте товары для гигиены</h2>
          <p>По синтетической истории категория вышла из привычного окна покупки.</p>
        </div>
        <details>
          <summary>Почему это мне?</summary>
          <p>Рекомендация опирается на интервалы между подтверждёнными покупками, а не на частоту открытий приложения.</p>
        </details>
      </article>

      <p className="demo-note"><Icon name="info" /> Пример механики на синтетической истории покупок.</p>
    </section>
  );
}
