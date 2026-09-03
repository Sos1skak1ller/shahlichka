"""gaming_sim — синтетическая популяция и когортная симуляция игрового слоя Х5 Клуб.

Использует тот же ``gaming_engine``, что и демо-фикстуры (FR-031). Каждый прогон
формирует две когорты из одного микса популяции: treatment (слой включён) и
control (выключен); заявляемый сдвиг метрики = treatment − control (FR-032a).
"""

from gaming_sim.runner import SimulationResult, run_simulation

__all__ = ["run_simulation", "SimulationResult"]
