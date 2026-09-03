# Contracts — Персональный игровой слой Х5 Клуб

JSON Schema (Draft 2020-12) — **единый источник истины** формы данных (research.md R7).
Из этих файлов генерируются:

- TS-типы + `zod`-схемы → `web/src/contract/`
- pydantic-модели → `engine/src/gaming_engine/contracts.py`

Контрактный тест (`engine/tests/contract/`, `web/tests/client.test.ts`) валидирует
все фикстуры `fixtures/out/*.json` и отчёты симуляции против этих схем.

| Файл | Направление | Кто продюсер / консьюмер |
|---|---|---|
| `purchase-event.schema.json` | вход движка | `sim/generator.py` / `fixtures/scenario.py` → `engine.event_log` |
| `profile-screen.schema.json` | выход → фронт | `fixtures/build.py` → `web ProfileAvatar.tsx` |
| `challenge-screen.schema.json` | выход → фронт | `fixtures/build.py` → `web Challenge.tsx` |
| `referral-screen.schema.json` | выход → фронт | `fixtures/build.py` → `web Referral.tsx` |
| `simulation-report.schema.json` | выход симуляции | `sim/report.py` → аналитик / слайд пилота |

Правила: денежные суммы — `number`, ₽; идентификаторы пользователей — обезличенные хэши
(никаких ФИО/адреса — FR-029); `iso_week` — строка `^\d{4}-W\d{2}$`.
