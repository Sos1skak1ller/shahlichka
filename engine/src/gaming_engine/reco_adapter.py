"""Мост от движка к пакету `recsys`.

Направление зависимости здесь одностороннее и это принципиально: `recsys` про движок
не знает ничего (критерий приёмки №1 его спеки), движок знает про `recsys` ровно три
функции.

Мост мягкий. Если пакет не установлен или артефакт не обучен, адаптер возвращает
None, и `promo.rank_promos` откатывается на прежнюю RFM-эвристику. Так демо и тесты
живут без обученной модели, а движок не превращается в заложника артефакта.
"""

from __future__ import annotations

from gaming_engine.contracts import PurchaseEvent

DEFAULT_SHORTLIST_K = 20


def available() -> bool:
    """Установлен ли `recsys` и читается ли артефакт."""
    return model_version() is not None


def model_version() -> str | None:
    try:
        from recsys import api
    except ImportError:
        return None
    try:
        return api.model_version()
    except (FileNotFoundError, OSError, KeyError):
        return None


def category_shortlist(
    events: list[PurchaseEvent],
    *,
    exclude: set[str],
    as_of_week: str,
    k: int = DEFAULT_SHORTLIST_K,
) -> dict[str, float] | None:
    """Шортлист категорий: `{категория: сырой ALS-скор}` либо None.

    None означает «рекомендателя нет» — это не ошибка, а штатный режим работы без
    артефакта. Пустой словарь означал бы «модель есть, но ничего не советует», и
    смешивать эти два случая нельзя: во втором промо показывать не надо.
    """
    try:
        from recsys import api
    except ImportError:
        return None

    payload = [
        {
            "receipt_id": e.receipt_id,
            "user_id": e.user_id,
            "timestamp": e.timestamp,
            "category_list": list(e.category_list),
            "sku_list": list(e.sku_list),
            "total_sum": e.total_sum,
            "corrects_receipt_id": e.corrects_receipt_id,
        }
        for e in events
    ]
    try:
        scored = api.recommend_categories(
            payload, exclude=exclude, k=k, as_of_week=as_of_week
        )
    except (FileNotFoundError, OSError, KeyError):
        return None
    return {c.category: c.score for c in scored}
