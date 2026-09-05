"""ALS-рекомендатель категорий и сопутствующих товаров.

Самостоятельный пакет: не импортирует `gaming_engine` и ничего не знает про промо,
бюджет и уровни аватара. Engine потребляет его через три функции из `recsys.api`.
"""

from recsys.types import CategoryScore, Interaction, ItemScore

__all__ = ["CategoryScore", "ItemScore", "Interaction"]
