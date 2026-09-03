# Quickstart — валидация игрового слоя Х5 Клуб

Прогоняемые сценарии, доказывающие, что фича работает end-to-end. Реализация — в
`tasks.md` и фазе implement; здесь только команды и ожидаемые результаты, привязанные к
Success Criteria из `spec.md`.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Репозиторий склонирован, ветка `001-gaming-layer`

## Setup

```bash
# Python: движок + симуляция (editable)
python -m venv .venv && source .venv/bin/activate
pip install -e "engine[dev]" -e "sim[dev]"

# сгенерировать типы контракта из contracts/*.schema.json
bash scripts/gen-contract-types.sh          # → engine/.../contracts.py, web/src/contract/

# фронт
cd web && npm install && cd ..
```

## Сценарий 1 — US1: аватар растёт только от экономии (P1)

```bash
pytest engine/tests/integration/test_avatar_replay.py -q
```

**Ожидание**: 30–50 golden-историй прогнаны через `event_log → avatar`; для каждой
итоговый `level` и `visual_stage` совпадают с эталоном. Тест включает кейсы: подъём
через порог, 10 «заходов» без покупок (уровень не меняется), чек с `saved_amount ≤ 0`
(прогресс не двигается), корректировка с понижением уровня, накопление на максимальном
уровне без новых уровней. → **SC-005**, FR-002/003/004/005.

```bash
pytest engine/tests/integration/test_idempotency.py -q
```

**Ожидание**: повторная доставка события с тем же `receipt_id` не двигает
`total_saved_amount`, `streak_count` и триггеры челленджа. → FR-030a.

## Сценарий 2 — US3: антифрод и бюджетный потолок (P2)

```bash
pytest engine/tests/integration/test_antifraud_precision.py -q
pytest engine/tests/integration/test_budget_cap.py -q
```

**Ожидание**:
- На помеченном наборе синтетических паттернов (нормальные + аномальная скорость чеков,
  коллизии `device_id_hash`/`payment_instrument_hash`, self-referral) **precision на
  фрод-классе ≥ 0.90**; recall выводится, но не гейтит. → **SC-004**, FR-016/017/020.
- При достижении недельного `budget_cap` начисления останавливаются, пишется
  `rejections[].reason = "budget_exceeded"`; челлендж со стоимостью выше
  `expected_margin_uplift` получает `status = "rejected_economy"` и не попадает на экран.
  → FR-018/019, US3 сценарии 3 и 5.
- Полоса `review` удерживает награду и авто-разрешается по правилу из `config.REVIEW_HOLD`;
  новый сигнал риска в окне удержания ⇒ исход `block`. → FR-015a, edge case.

## Сценарий 3 — US2 / US6: персонализация (P2 / P3)

```bash
pytest engine/tests/unit/test_challenge_ranker.py engine/tests/unit/test_promo_ranking.py -q
```

**Ожидание**:
- Два пользователя одного сегмента с разной историей получают **разные** челленджи;
  выданный челлендж относится к категории из истории пользователя; `budget_cost`
  проходит pre-check. Пустая история ⇒ `generated_by = "fallback"`; исчерпание пула ⇒
  лог `template_pool_exhausted`; `≥ ANTI_FATIGUE_N` циклов без отклика ⇒ смена
  `mechanic_type`. → FR-009..014.
- Ранжирование акций: категория из недавней истории поднимается выше; при равной
  релевантности выше — акция с большей `margin_impact`; пустая история ⇒ нейтральный
  порядок без ошибки. → FR-025/026/027.
- Экспертная разметка релевантности на 30–50 held-out профилях (отдельный чек-лист
  команды) даёт **≥ 70%** для челленджей и для акций. → **SC-001**, **SC-002**.

## Сценарий 4 — US5: реферальная программа (P3)

```bash
pytest engine/tests/unit/test_referral_state_machine.py -q
```

**Ожидание**: награда не начислена ни на `invited`, ни на `registered`, ни на
`purchase_confirmed` — только на `reward_released`; приглашённый с совпадающим
`device_id_hash`/`payment_instrument_hash` ⇒ `blocked` (self_referral); отсутствие
покупки до `window_deadline` ⇒ `expired` без награды. → FR-021/022/023/024, FR-017.

## Сценарий 5 — US4: когортная симуляция и паритет (P2)

```bash
python -m gaming_sim.runner --population 1000  --weeks 4 --seed 42 --out sim/out/run_1k.json
python -m gaming_sim.runner --population 10000 --weeks 4 --seed 42 --out sim/out/run_10k.json
pytest sim/tests/test_population_mix.py sim/tests/test_cohort_split.py -q
```

**Ожидание**: оба прогона завершаются < 60 c; `chain_mix` в отчёте воспроизводит доли
из `fixtures/data/segment_mix.json` в пределах допуска; отчёт валиден по
`contracts/simulation-report.schema.json`, содержит primary + guardrail метрики по
когортам `treatment`/`control` с `delta`, блок `economy` с `roi` и
`invariant_holds = true`. → **SC-003**, **SC-007**, **SC-010**, FR-032/032a/033.

```bash
bash scripts/check-parity.sh          # прогон демо-сценария в sim и diff с fixtures/out
pytest sim/tests/test_parity.py -q
```

**Ожидание**: ключевые числа (уровень аватара, `budget_cost`) для одного сценария
совпадают между `fixtures/out/*.json` и результатом того же сценария в `sim/`. →
**SC-006**, FR-031.

## Сценарий 6 — демо из 3 экранов без сети (P1)

```bash
python -m fixtures.build            # engine → fixtures/out/{profile,challenge,referral}-screen.json
cd web && npm run test:contract     # zod-валидация фикстур по contracts/*-screen.schema.json
npm run test                        # рендер экранов из фикстур (vitest + RTL)
npm run dev                         # открыть в браузере
```

**Ожидание**: три экрана (профиль/аватар, челлендж, реферал) рендерятся из локального
JSON; в DevTools → Network **нет запросов** во время навигации; экрана «рейтинг
экономии» нет; в UI отсутствует слово «ИИ»/«AI». → **SC-009**, **SC-011**, FR-007/035.

## Сводная матрица

| Сценарий | Проверяет | Success Criteria |
|---|---|---|
| 1 | детерминизм аватара, идемпотентность | SC-005 |
| 2 | антифрод precision, бюджетный потолок, review-hold | SC-004, SC-003 (частично) |
| 3 | персональность челленджа и акций, relevance ≥ 70% | SC-001, SC-002 |
| 4 | реферальная state-machine, отложенная награда | — (FR-021..024) |
| 5 | когортная симуляция, ROI, паритет demo↔sim | SC-003, SC-006, SC-007, SC-010 |
| 6 | 3 экрана, ноль сетевых зависимостей, нейминг | SC-009, SC-011 |
| ревизия `data-model.md` | отсутствие полей ПДн | SC-008 |
