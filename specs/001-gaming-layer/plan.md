# Implementation Plan: Персональный игровой слой Х5 Клуб

**Branch**: `001-gaming-layer` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-gaming-layer/spec.md`

## Summary

Персональный игровой слой поверх Х5 Клуб: аватар растёт от суммы **экономии** по
подтверждённым чекам (не от активности), раз в неделю выдаётся персональный челлендж,
подобранный объяснимым ML-пайплайном (шаблоны + ранжирование, без LLM), работает
реферальная программа с отложенной наградой и персональное ранжирование акций. Каждый
чек и реферал проходит синхронный антифрод-скоринг с фиксированным порогом; экономика
награды считается и лимитируется заранее (недельный потолок как % маржи, инвариант
«стоимость награды ≤ прирост маржи»). Когортная симуляция 1–10 тыс. синтетических
профилей (treatment vs control) на том же расчётном коде даёт метрики пилота и ROI.

**Технический подход**: единый детерминированный расчётный движок на Python
(`engine/`), которым пользуются и офлайн-генератор демо-фикстур, и симуляция
(`sim/`) — это выполняет инвариант FR-031 «один код — один результат». Демо — статичный
React-фронт (`web/`) из трёх экранов, читающий заранее сгенерированные JSON-фикстуры по
контракту из JSON Schema; на сцене нет сети, БД и очередей. Данные — только синтетика.

## Technical Context

**Language/Version**: Python 3.11 (движок + симуляция); TypeScript 5.x / React 18
(демо-фронт)

**Primary Dependencies**: Python — `numpy`, `pandas`, `scikit-learn` (LogisticRegression
для ранжирования челленджей; LightGBM отложен как апгрейд), `pydantic` (валидация
контрактов), `pytest`. Frontend — `react`, `vite`, `zod` (валидация фикстур по контракту
на клиенте), `vitest` + `@testing-library/react`. Общий контракт — JSON Schema
(Draft 2020-12), из него генерируются TS-типы и Python-модели.

**Storage**: Демо — статичные JSON-файлы в `fixtures/` (нет БД). Движок в рантайме
держит состояние в памяти (in-memory event log + проекции). Симуляция пишет отчёт в
JSON/Parquet на диск. Продовая БД — вне скоупа; контракты спроектированы так, что
фикстура — заменяемая реализация того же интерфейса.

**Testing**: `pytest` — юнит-тесты движка, интеграционный реплей 30–50 синтетических
историй (golden-файлы), тест паритета демо ↔ симуляция, тест precision антифрода.
Контрактные тесты — валидация всех фикстур против JSON Schema. `vitest` — компоненты и
клиент контракта на фронте.

**Target Platform**: Локальный запуск на ноутбуке (демо на сцене) — Python CLI +
статичный веб-бандл в браузере. Linux/macOS для движка и симуляции.

**Project Type**: Web application с офлайн расчётным ядром — три модуля: `engine/`
(Python-библиотека), `sim/` (Python CLI), `web/` (React SPA); плюс `fixtures/`
(сгенерированные данные + схема контракта).

**Performance Goals**: Симуляция 10 000 профилей за 4 недели модельного времени —
прогон < 60 c на ноутбуке. Реген фикстур демо — < 5 c. Экран демо рендерится из
локального JSON мгновенно (нет сетевых вызовов — SC-011).

**Constraints**: Полный детерминизм расчётного ядра (одинаковый вход → одинаковый
выход, никаких обращений к wall-clock, сид RNG фиксирован) — обязателен для SC-005,
SC-006, FR-031. Никаких ПДн (ФИО/адрес) нигде (FR-029). Никаких реальных данных и
интеграций X5 (FR-028). В названии продукта нет слова «ИИ»/«AI» (FR-035).

**Scale/Scope**: 1–10 тыс. синтетических профилей в симуляции; 3 экрана демо; 6
пользовательских историй; ~13 доменных сущностей. Один целевой сегмент («родители с
детьми до 3 лет», пользователи МП) по трём сетям ТС5/ТСХ/ТСЧ.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Проверка против `.specify/memory/constitution.md` v1.0.0.

| Принцип | Как план соответствует | Статус |
|---|---|---|
| **I. Экономия → награда, никогда наоборот** | `engine/avatar.py` двигает уровень **только** от `total_saved_amount`; открытия приложения не входят во входной контракт движка. `engine/streak.py` считает недели с подтверждённой покупкой. FR-002/003/006. | PASS |
| **II. Объяснимость важнее сложности** | Челлендж-ранкер — `LogisticRegression` + сборка текста из шаблонной строки, без LLM. Антифрод — взвешенный scorecard с фиксированным порогом и вкладом каждой фичи (`explanation{}`). Апгрейды (LightGBM, contextual bandit) вынесены в «отложено». FR-010/016/020. | PASS |
| **III. Экономика награды считается заранее** | `engine/ledger.py`: недельный `budget_cap` = % маржи; каждая выдача проходит pre-check против остатка потолка и против `expected_margin_uplift`; реферальная награда отложена до `purchase_confirmed`. FR-018/019/021. | PASS |
| **IV. Антифрод и симуляция — обязательный контур** | `engine/antifraud.py` синхронно скорит каждый чек и реферал; self-referral блокируется по хэшам устройства/платежа. `sim/` использует **тот же** `engine/`; тест паритета в CI. Метрика — precision на фрод-классе. FR-015/017/031/032. | PASS |
| **V. Демо-first + только синтетика** | `web/` читает статичные JSON из `fixtures/`, ноль сетевых вызовов (SC-011). Единственный источник данных — `sim/generator.py`. Рабочее имя репозитория нейтральное; продуктовое имя без «AI» фиксирует команда. FR-028/029/035. | PASS |
| **Ограничения скоупа** | Ровно 3 экрана в `web/src/screens/` (profile-avatar, challenge, referral); экран рейтинга экономии не создаётся. Два осознанных отклонения (LLM→ML, убран рейтинг) зафиксированы в spec и в `research.md`. | PASS |

**Итог гейта (до Phase 0)**: нарушений нет. Complexity Tracking не заполняется.

### Post-Design Re-check (после Phase 1)

Пересмотр после `data-model.md`, `contracts/`, `quickstart.md`:

- **I** — `profile-screen.schema.json` не содержит ни одного поля активности в
  приложении; `savings.progress_ratio` считается только из `total_saved_amount`. Модель
  `Avatar` (data-model §2) явно допускает понижение уровня при корректировке — прогресс
  идёт строго от денег. ✔
- **II** — `challenge-screen.schema.json` фиксирует `generated_by ∈ {ml_ranker, rule,
  fallback}` (нет `llm`); `FraudScore.explanation` обязателен в data-model §10. ✔
- **III** — `RewardLedger` (data-model §11) с двойным pre-check и
  `simulation-report.schema.json.economy.invariant_holds` выносят инвариант экономики в
  проверяемое поле отчёта (SC-003). ✔
- **IV** — `simulation-report.schema.json` требует `antifraud.fraud_class_precision` и
  когортные `metrics`; `quickstart.md` сценарий 5 гоняет тест паритета demo↔sim. ✔
- **V** — `contracts/*-screen.schema.json` — единственный вход `web/`; `quickstart.md`
  сценарий 6 проверяет ноль сетевых запросов и отсутствие «AI»/«ИИ». ✔

Новых нарушений нет; отклонения №1 и №2 остаются задокументированными (research.md,
FR-036). Гейт пройден повторно.

## Project Structure

### Documentation (this feature)

```text
specs/001-gaming-layer/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (+ Clarifications session 2026-09-03)
├── research.md          # Phase 0 output — решения и обоснования
├── data-model.md        # Phase 1 output — сущности, поля, переходы состояний
├── quickstart.md        # Phase 1 output — прогоняемые сценарии валидации
├── contracts/           # Phase 1 output — JSON Schema контрактов
│   ├── README.md
│   ├── purchase-event.schema.json
│   ├── profile-screen.schema.json
│   ├── challenge-screen.schema.json
│   ├── referral-screen.schema.json
│   └── simulation-report.schema.json
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
engine/                              # Python — детерминированное расчётное ядро (без I/O)
├── src/gaming_engine/
│   ├── __init__.py
│   ├── config.py                    # иллюстративные константы (пороги уровней, N,
│   │                                #   budget_cap %, review-hold, referral-window)
│   ├── contracts.py                 # pydantic-модели, сгенерированные из contracts/*.schema.json
│   ├── event_log.py                 # приём PurchaseEvent, дедуп по receipt_id, корректировки
│   ├── avatar.py                    # state-machine: saved_amount → level → visual_stage
│   ├── streak.py                    # недельный стрик по подтверждённым покупкам
│   ├── challenge/
│   │   ├── features.py              # RFM-профиль по категориям, архетип, уровень аватара
│   │   ├── templates.py             # реестр ChallengeTemplate + eligibility
│   │   ├── candidates.py            # фильтр кандидатов (бюджет, недавно показанные)
│   │   ├── ranker.py                # LogisticRegression ранжирование + rule fallback
│   │   └── assemble.py              # подстановка параметров в шаблонную строку
│   ├── antifraud.py                 # взвешенный scorecard, порог, объяснение, review-hold
│   ├── referral.py                  # state-machine invited→…→reward_released / blocked
│   ├── promo.py                     # эвристическое ранжирование пула акций
│   ├── ledger.py                    # RewardLedger, недельный потолок, инвариант экономики
│   └── timing.py                    # rule-based: показать челлендж vs напомнить реферал; anti-fatigue
└── tests/
    ├── unit/                        # по модулю: avatar, streak, antifraud, ledger, ranker…
    ├── integration/
    │   ├── test_avatar_replay.py    # 30–50 golden-историй → уровень совпадает (SC-005)
    │   ├── test_antifraud_precision.py  # помеченный набор → precision ≥ 0.90 (SC-004)
    │   ├── test_budget_cap.py       # начисления стоп при исчерпании потолка
    │   └── test_idempotency.py      # дубль receipt_id не двигает прогресс (FR-030a)
    └── contract/
        └── test_schema_roundtrip.py # contracts/*.schema.json ↔ pydantic-модели

sim/                                 # Python — синтетика + когортная симуляция (использует engine)
├── src/gaming_sim/
│   ├── __init__.py
│   ├── archetypes.py                # 4–5 архетипов покупателя (эконом-охотник, лоялист,
│   │                                #   спящий, кросс-шоппер [+ опц. 5-й])
│   ├── population.py                # сэмплер по миксу сегментов/сетей из §3.1, вес на «МП»
│   ├── generator.py                 # поток PurchaseEvent + социальный граф (рефералы)
│   ├── runner.py                    # прогон двух когорт: treatment (слой вкл) / control (выкл)
│   ├── metrics.py                   # primary + guardrail метрики по когортам
│   └── report.py                    # отчёт по simulation-report.schema.json + формула ROI
└── tests/
    ├── test_population_mix.py       # доли сегментов/архетипов в допуске (US4 сценарий 1)
    ├── test_cohort_split.py         # treatment/control из одного микса
    └── test_parity.py               # тот же сценарий: sim == демо-фикстура (SC-006)

fixtures/                            # JSON-снимки, произведённые engine на скриптовом сценарии
├── scenario.py                      # скриптовый демо-сценарий (Python, использует engine)
├── build.py                         # запись экранных JSON по contracts/*-screen.schema.json
├── data/
│   ├── promo_pool.json              # фикстура «от маркетинга» (вход US6)
│   ├── segment_mix.json             # доли сегментов по 3 сетям (§3.1) — вход симуляции
│   └── challenge_templates.json     # реестр шаблонов челленджей
└── out/                             # profile-screen.json, challenge-screen.json, referral-screen.json

web/                                 # React + TS — 3 экрана, читает fixtures/out/*.json
├── src/
│   ├── contract/                    # TS-типы, сгенерированные из ../../contracts/*.schema.json
│   ├── client.ts                    # fixture-backed реализация интерфейса контракта
│   ├── screens/
│   │   ├── ProfileAvatar.tsx        # аватар, прогресс-бар экономии, уровень, кастомизация
│   │   ├── Challenge.tsx            # текущий недельный челлендж, прогресс по чекам
│   │   └── Referral.tsx             # статус приглашений, отложенная награда
│   ├── components/                  # ProgressBar, AvatarStage, StatusPill…
│   └── App.tsx                      # таб-бар из 3 экранов
└── tests/
    ├── client.test.ts              # клиент валидирует фикстуру по zod-схеме контракта
    └── screens/*.test.tsx          # рендер экранов из фикстур

scripts/
├── gen-contract-types.sh           # JSON Schema → TS + pydantic
└── check-parity.sh                 # прогон sim-сценария и diff с fixtures/out
```

**Structure Decision**: Три исходных модуля + каталог сгенерированных данных.
`engine/` — чистая детерминированная библиотека без I/O: это физическое воплощение
инварианта «один расчётный код» (FR-031) — и `fixtures/scenario.py`, и `sim/runner.py`
импортируют один и тот же `gaming_engine`. `sim/` добавляет синтетическую популяцию и
когортный прогон. `fixtures/` — это выход `engine` на одном скриптовом сценарии,
сериализованный по контракту; `web/` зависит **только** от `contracts/*.schema.json`,
не от Python, поэтому демо на сцене не имеет ни одной серверной зависимости (SC-011).
Контракт в JSON Schema — единый источник истины, из него генерируются и TS-типы для
фронта, и pydantic-модели для движка, что не даёт форме данных разойтись между слоями.

## Complexity Tracking

> Constitution Check пройден без нарушений — таблица не заполняется.
