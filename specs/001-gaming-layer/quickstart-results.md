# Результаты прогона quickstart — Персональный игровой слой Х5 Клуб

Дата прогона: 2026-09-03. Окружение: Python 3.11 (uv workspace), Node 20, macOS.

## Сводка по сценариям quickstart.md

| Сценарий | Что проверяет | Команда | Результат |
|---|---|---|---|
| 1 | US1: детерминизм аватара, идемпотентность (SC-005) | `pytest engine/tests/integration/test_avatar_replay.py test_idempotency.py` | ✅ pass (7 golden-историй + идемпотентность) |
| 2 | US3: precision антифрода ≥ 0.90 (SC-004), бюджетный потолок, review-hold | `pytest engine/tests/integration/test_antifraud_precision.py test_budget_cap.py` + `unit/test_review_hold.py test_threshold_boundary.py` | ✅ pass; precision 0.98 на размеченном наборе |
| 3 | US2/US6: персональность челленджа и акций | `pytest engine/tests/unit/test_challenge_*.py test_promo_ranking.py` | ✅ pass; relevance ≥ 70% — **ручная разметка**, см. `eval/*.md` |
| 4 | US5: реферальная state-machine, отложенная награда | `pytest engine/tests/unit/test_referral_state_machine.py` | ✅ pass |
| 5 | US4: когортная симуляция, ROI, паритет demo↔sim (SC-003/006/007/010) | `python -m gaming_sim.runner --population {1000,10000}` + `pytest sim/tests` | ✅ pass; отчёт валиден по схеме |
| 6 | 3 экрана, ноль сетевых зависимостей, нейминг (SC-009/011) | `npm run test` + `npm run build` + аудит | ✅ pass; 3 экрана, «AI»/«ИИ» не найдены |

## Числа последнего прогона симуляции (`run-10000-4w-s42`)

| Метрика | control | treatment | Δ |
|---|---:|---:|---:|
| d7_return_no_push (primary) | 0.842 | 0.874 | +0.032 |
| purchase_frequency (primary) | 2.09 | 2.35 | +0.26 |
| avg_check (primary) | 1780 | 1816 | +35 |
| retention (guardrail) | 0.959 | 0.969 | +0.010 |
| referral_new_users (guardrail) | 444 | 654 | +210 |
| basket_items (guardrail) | 4.02 | 4.22 | +0.19 |
| session_length (guardrail) | 180 | 193 | +13 |

- economy: reward_cost 81 315 ₽ · margin_uplift 465 570 ₽ · **ROI 384 255 ₽** · invariant_holds **true** (SC-003)
- antifraud: precision **0.977** (цель ≥ 0.90, SC-004) · recall 0.999 · review_auto_resolved 1 799

## T075 — аудит приватности (SC-008)

Поиск по `engine/src`, `specs/001-gaming-layer/contracts`, `fixtures/data` полей вида
`first_name/last_name/full_name/адрес/passport/birth_date/phone_number` — **совпадений
нет**. Единственное «похожее» — `district_code` (код района, не адрес; используется как
антифрод-признак). Идентификатор пользователя — обезличенный хэш. ✅ FR-029.

## T076 — аудит нейминга и скоупа (SC-009)

- `grep -E '\bAI\b|\bИИ\b'` по `web/src`, `web/index.html`, `fixtures/` — **совпадений
  нет**. Продуктовое имя-плейсхолдер: «Х5 Клуб · Рост». ✅ FR-035.
- Экранов в `web/src/screens/`: ровно **3** (ProfileAvatar, Challenge, Referral).
  Экран рейтинга экономии не реализован. ✅ FR-007 (осознанное отклонение №2).

## T078 — производительность

| Операция | Время |
|---|---:|
| Пересборка демо-фикстур (`python -m fixtures.build`) | ~0.7 с (бюджет < 5 с) |
| Симуляция 10 000 профилей × 4 недели × 2 когорты | ~11–12 с (бюджет < 60 с, SC-007) |
| Симуляция 1 000 профилей × 4 недели × 2 когорты | ~0.7 с |
| `pytest engine/tests` (65 тестов) | ~0.7 с |
| `pytest sim/tests` (19 тестов, вкл. 10k) | ~18 с |

## Открытые пункты (ручная работа, не блокируют код)

- **SC-001 / SC-002** (relevance ≥ 70%) требуют экспертной разметки held-out профилей —
  чек-листы и команды выгрузки в `eval/challenge-relevance.md` и `eval/promo-relevance.md`.
- Числа маржи/среднего чека — иллюстративные (ТЗ 12); помечены как таковые в
  `pilot-plan.md`.
