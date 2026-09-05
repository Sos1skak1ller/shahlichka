"""Устойчивый покупательский профиль: какие категории человек берёт и с каким ритмом.

Зачем это отдельно от генератора. До 05.09 категория чека сэмплировалась независимо
на каждый чек из весов сегмента. Следствий два, и оба ломали продукт:

* **Персонального вкуса не существовало.** За 14 недель пользователь задевал 20 с
  лишним категорий из 48, и внутри сегмента все профили становились
  взаимозаменяемыми. Коллаборативной фильтрации не с чем коллаборировать —
  рекомендатель выучивал популярность и выдавал шум.
* **Не было цикличности.** `X5-status_6.md` §6 Этап 1 требует, чтобы история несла
  «категорийную структуру с разной цикличностью», иначе гипотезы H10 (возврат в
  категорию в предсказанное окно) и H13 (обрыв категорийной привычки) нечем
  проверять — предсказывать нечего, обрываться нечему.

Профиль детерминирован по `user_id`: своя RNG, не связанная с потоком генератора,
поэтому вкус не зависит от порядка вызовов и одинаков между прогонами.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from gaming_sim.catalog import affinity_to_core, cadence_of, segment_weights

# Ширина корзины: сколько категорий человек реально покупает регулярно.
# Это ядро (§ критерий M2: топ-5 категорий ≥ 50 % корзины), а не весь ассортимент.
CORE_CATEGORIES = (5, 11)
# Разброс личного цикла вокруг типового: кто-то берёт молочку раз в неделю,
# кто-то раз в две.
CYCLE_JITTER = (0.7, 1.6)
# Вероятность пропустить положенную по циклу покупку — иначе ритм идеально
# метрономный и детект обрыва привычки становится тривиальным.
SKIP_PROB = 0.18
# Вероятность импульсной покупки вне ядра: без неё матрица распадается на
# непересекающиеся блоки и у категорий нет общего контекста.
IMPULSE_PROB = 0.12
# До какого цикла категория считается staple — тем, что берут попутно каждый поход.
STAPLE_CYCLE_MAX = 1.6
# Температура softmax для выбора новой категории. Чем ниже, тем предсказуемее
# освоение: человек берёт соседнюю к своему ядру категорию, а не любую из сорока
# восьми. Значение подобрано так, чтобы потолок recall@5 (доля вероятностной массы
# в топ-5) лёг в 55–65 % — диапазон, типичный для предсказания следующей категории
# на реальных ритейл-данных. Это параметр ДАННЫХ, а не модели: он задаёт, насколько
# задача вообще решаема, и его надо предъявлять вместе с любой цифрой recall.
IMPULSE_TEMPERATURE = 0.045
# Насколько связным получается ядро: ниже — теснее кластер категорий у одного
# человека. Это то, что даёт ALS восстанавливаемую структуру.
CORE_COHESION = 0.25


@dataclass(frozen=True)
class CategoryHabit:
    category: str
    cycle_weeks: float  # личный межпокупочный интервал
    phase: int  # в какую неделю цикла человек обычно покупает


@dataclass(frozen=True)
class TasteProfile:
    user_id: str
    core: tuple[CategoryHabit, ...]
    tail: tuple[str, ...]  # категории для импульсных покупок
    tail_probs: tuple[float, ...] = ()  # веса хвоста: близость к ядру

    def sample_impulse(self, rng: np.random.Generator) -> str | None:
        """Импульсная покупка, смещённая к тому, что человек уже берёт.

        Равномерный выбор из хвоста делал бы освоение новой категории чистой
        случайностью — тогда «предскажи следующую категорию» не имеет решения
        в принципе, и recall@5 упирается в потолок случайного угадывания.
        """
        if not self.tail:
            return None
        p = np.asarray(self.tail_probs, dtype=float)
        if p.size != len(self.tail) or p.sum() <= 0:
            return self.tail[int(rng.integers(0, len(self.tail)))]
        return self.tail[int(rng.choice(len(self.tail), p=p / p.sum()))]

    @property
    def core_categories(self) -> tuple[str, ...]:
        return tuple(h.category for h in self.core)

    @property
    def staples(self) -> tuple[str, ...]:
        """Категории, которые берут почти каждый поход: хлеб, молоко, овощи.

        Только ими добивается корзина. Если добивать любой категорией ядра, то
        бытовая химия попадает в чек каждую неделю, её месячный цикл исчезает —
        и H10 с H13 нечего предсказывать.
        """
        return tuple(h.category for h in self.core if h.cycle_weeks <= STAPLE_CYCLE_MAX)

    def due_categories(self, week_index: int, rng: np.random.Generator) -> list[str]:
        """Категории, которым по циклу пора быть купленными на этой неделе."""
        due: list[str] = []
        for h in self.core:
            cycle = max(1, int(round(h.cycle_weeks)))
            if (week_index - h.phase) % cycle == 0 and rng.random() > SKIP_PROB:
                due.append(h.category)
        return due


def _seed_for(user_id: str) -> int:
    digest = hashlib.sha256(user_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


@lru_cache(maxsize=20000)
def taste_of(user_id: str, segment: str) -> TasteProfile:
    """Устойчивый профиль пользователя. Кэшируется: одна и та же выдача на прогон."""
    rng = np.random.default_rng(_seed_for(user_id))

    weighted = segment_weights(segment)
    names = [c for c, _ in weighted]
    probs = np.asarray([w for _, w in weighted], dtype=float)
    probs = probs / probs.sum()

    n_core = int(rng.integers(CORE_CATEGORIES[0], CORE_CATEGORIES[1] + 1))
    n_core = min(n_core, len(names))

    # Ядро растёт связно: первая категория — по популярности сегмента, каждая
    # следующая тянется к уже выбранным.
    #
    # Так было не всегда, и это была ключевая ошибка. Пока ядро набиралось
    # независимыми розыгрышами по популярности, основная масса данных не несла
    # той геометрии, которая управляет освоением новых категорий, — ALS честно
    # выучивал популярность и всем подряд советовал макароны. Реальная корзина
    # тоже связная: человек с детским питанием берёт подгузники, а не автохимию.
    picked: list[int] = [int(rng.choice(len(names), p=probs))]
    while len(picked) < n_core:
        chosen = tuple(sorted(names[i] for i in picked))
        aff = np.asarray(
            [
                0.0 if i in picked else affinity_to_core(names[i], chosen) * probs[i]
                for i in range(len(names))
            ],
            dtype=float,
        )
        if aff.sum() <= 0:
            break
        logits = (aff / aff.max() - 1.0) / CORE_COHESION
        w = np.exp(logits) * (aff > 0)
        picked.append(int(rng.choice(len(names), p=w / w.sum())))

    habits: list[CategoryHabit] = []
    for ix in sorted(picked):  # сортировка — детерминированный порядок
        cat = names[int(ix)]
        base = cadence_of(cat)
        jitter = float(rng.uniform(*CYCLE_JITTER))
        cycle = max(1.0, base * jitter)
        habits.append(
            CategoryHabit(
                category=cat,
                cycle_weeks=cycle,
                phase=int(rng.integers(0, max(1, int(round(cycle))))),
            )
        )

    core_set = {h.category for h in habits}
    core_ids = tuple(sorted(core_set))
    tail = tuple(c for c in names if c not in core_set)
    # Хвост взвешен близостью к ядру: следующая освоенная категория — соседняя
    # по товарной группе или по профилю сегмента, а не любая из сорока восьми.
    aff = np.asarray([affinity_to_core(c, core_ids) for c in tail], dtype=float)
    if aff.size:
        logits = (aff - aff.max()) / IMPULSE_TEMPERATURE
        weights = np.exp(logits)
        tail_probs = tuple(float(x) for x in weights / weights.sum())
    else:
        tail_probs = ()
    return TasteProfile(
        user_id=user_id, core=tuple(habits), tail=tail, tail_probs=tail_probs
    )
