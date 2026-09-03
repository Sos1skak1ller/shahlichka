# Phase 1 Data Model: Персональный игровой слой Х5 Клуб

Дата: 2026-09-03. Источник: `spec.md` §Key Entities + §Functional Requirements,
`research.md` R2/R4/R5/R8.

Все идентификаторы пользователей — обезличенные хэши (FR-029: ФИО/адрес не хранятся).
Все денежные величины — в рублях, целые или с 2 знаками; неотрицательны, кроме
`saved_amount` события-корректировки. «Неделя» везде — ISO-неделя от `timestamp`
события (R2), формат ключа `YYYY-Www`.

---

## 1. User (Профиль игрока)

| Поле | Тип | Правила |
|---|---|---|
| `user_id` | string (hash) | PK; хэш номера карты Х5 Клуб |
| `segment` | enum | один из 5 сегментов; целевой — `parents_0_3` |
| `archetype` | enum | `bargain_hunter` \| `loyalist` \| `sleeper` \| `cross_shopper` \| `mixed` (синтетика) |
| `chain_code` | enum | `TS5` \| `TSX` \| `TSC` — основная сеть |
| `registration_date` | date | ≤ дата первого события |
| `device_id_hash` | string | для антифрода/self-referral |
| `payment_instrument_hash` | string | для антифрода/self-referral |
| `total_saved_amount` | number ≥ 0 | сумма всех `saved_amount` учтённых чеков минус корректировки; не опускается ниже 0 |
| `current_avatar_level` | int 0..`AVATAR_LEVELS-1` | проекция из Avatar |
| `streak_count` | int ≥ 0 | см. StreakState |

**Отношения**: 1:1 `Avatar`; 1:N `PurchaseEvent`, `Challenge`, `Referral` (как inviter),
`RewardLedger`, `FraudScore`.

**Инвариант**: `current_avatar_level` = функция только от `total_saved_amount`
(FR-003); никакое поле активности в приложении в модель не входит.

---

## 2. Avatar

| Поле | Тип | Правила |
|---|---|---|
| `avatar_id` | string | PK |
| `user_id` | string | FK → User, уникально (1:1) |
| `level` | int 0..`AVATAR_LEVELS-1` | монотонно растёт при накоплении; может **снизиться** при корректировке (FR-005) |
| `visual_stage` | int 1..`VISUAL_STAGES` | 1:1 с `level` по `config` |
| `state` | enum | `progressing` \| `level_up_pending` \| `max_level` |
| `last_transition_at` | datetime | из `timestamp` события, вызвавшего переход |
| `unlocked_customizations` | string[] | накопительный список; не очищается при понижении уровня |
| `transition_history` | Transition[] | append-only |

**Transition**: `{ from_level, to_level, trigger_receipt_id, at, reason: "accrual" \| "correction" }`.

**Переходы состояния** (`avatar.py`):

```
progressing --(total_saved crosses threshold[L+1])--> level L+1, append Transition, unlock customization[L+1]
progressing --(correction drops total_saved below threshold[L])--> level L-1, append Transition(reason=correction)
level < MAX with accrual reaching top threshold --> max_level
max_level --(further accrual)--> max_level (накопление растёт, новых уровней нет — FR-004 сценарий 5)
```

Правило: чек с `saved_amount ≤ 0` не двигает прогресс вперёд (FR-002, US1 сценарий 3).

---

## 3. PurchaseEvent (Событие покупки)

| Поле | Тип | Правила |
|---|---|---|
| `receipt_id` | string | PK; **ключ идемпотентности** (FR-030a) |
| `user_id` | string | FK → User |
| `store_code` | string | код магазина |
| `chain_code` | enum | `TS5` \| `TSX` \| `TSC` |
| `district_code` | string | код района (для антифрод-фич; не адрес) |
| `timestamp` | datetime | единственный источник «времени» в движке (R2) |
| `sku_list` | string[] | может быть пустым (edge case) |
| `category_list` | string[] | может быть пустым |
| `total_sum` | number ≥ 0 | сумма чека |
| `saved_amount` | number | сумма экономии; **берётся как есть** (FR-002); у корректировки — отрицательна |
| `device_id_hash` | string | |
| `payment_instrument_hash` | string | |
| `corrects_receipt_id` | string \| null | не null ⇒ событие-корректировка/возврат исходного чека |
| `kind` | enum | `purchase` \| `correction` (derived: `correction` ⇔ `corrects_receipt_id != null`) |

**Правила обработки** (`event_log.py`):
- Повторный `receipt_id` (уже в логе) ⇒ игнор, прогресс/стрик/триггеры не двигаются (FR-030a).
- `correction` без известного исходного `receipt_id` ⇒ отклоняется, лог `orphan_correction`.
- `correction` применяет `saved_amount` (отрицательный) к `total_saved_amount`, затем
  пересчёт Avatar (возможно понижение).

**Отношения**: fan-out на Avatar, StreakState, Challenge-триггер, FraudScore.

---

## 4. StreakState

| Поле | Тип | Правила |
|---|---|---|
| `user_id` | string | FK → User (1:1) |
| `streak_count` | int ≥ 0 | подряд идущие ISO-недели с ≥1 подтверждённой покупкой |
| `last_active_week` | string `YYYY-Www` | неделя последней подтверждённой покупки |

**Правила** (`streak.py`, FR-006):
- Покупка на неделе `W`: если `W == last_active_week` → без изменений; если `W` —
  следующая неделя после `last_active_week` → `streak_count += 1`; если между ними есть
  пропущенная неделя → `streak_count = 1`.
- Определение «пропуска» вычисляется при следующей покупке или при запросе на неделе `> last_active_week + 1`.
- Корректировка, обнуляющая все покупки недели, может уменьшить `streak_count`.

---

## 5. ChallengeTemplate (Шаблон челленджа)

| Поле | Тип | Правила |
|---|---|---|
| `template_id` | string | PK |
| `mechanic_type` | enum | `category_repeat` \| `basket_growth` \| `streak_keep` \| `cross_chain` |
| `condition_pattern` | string | шаблонная строка, напр. `«Купите {n} раз {category} до {deadline}»` |
| `reward_formula` | string/expr | детерминированная функция от параметров → `budget_cost` |
| `eligibility_rules` | object | мин/макс уровень аватара, допустимые сегменты, cooldown в неделях |
| `param_space` | object | диапазоны для `n`, `deadline_offset`, `category` источник |

---

## 6. Challenge (Челлендж)

| Поле | Тип | Правила |
|---|---|---|
| `challenge_id` | string | PK |
| `user_id` | string | FK → User |
| `cache_key` | string | `{segment}:{iso_week}` (R3; «район»/«рейтинг» из ключа убраны) |
| `template_id` | string | FK → ChallengeTemplate |
| `filled_params` | object | `{ category, n, deadline, reward_amount }` |
| `text` | string | результат подстановки в `condition_pattern` (FR-010) |
| `generated_by` | enum | `ml_ranker` \| `rule` \| `fallback` (**не** `llm`) (FR-011) |
| `budget_cost` | number ≥ 0 | из `reward_formula`; проверен против потолка (R5) |
| `status` | enum | `active` \| `completed` \| `expired` \| `rejected_economy` |
| `valid_from` / `valid_to` | datetime | окно недели |
| `progress` | int ≥ 0 | число подтверждающих чеков (FR-012) |
| `algo_version` | string | версия ранкера для `RecommendationLog` |

**Переходы** (`challenge/`):

```
(нет активного) --generate--> active            (не более 1 active на user — FR-008)
active --progress reaches n before valid_to--> completed  --> accrue reward via RewardLedger
active --valid_to passes--> expired
candidate --economy pre-check fails--> rejected_economy (не показывается — US3 сценарий 5)
active + начало новой недели --> остаётся active, новый не выдаётся (US2 сценарий 2)
```

**Fallback** (FR-013): пустая история ИЛИ пул шаблонов сегмента на неделю исчерпан ⇒
`generated_by = "fallback"`, лог `template_pool_exhausted` при второй причине.
**Anti-fatigue** (FR-014): `≥ ANTI_FATIGUE_N` завершённых циклов с `progress == 0` ⇒
следующий подбор меняет `mechanic_type`.

---

## 7. RecommendationLog

Append-only; `{ user_id, segment, iso_week, chosen_template_id, algo_version,
context_features{}, response_signal: "completed" | "ignored" | "expired" }`.
Метки `response_signal` из `sim/` — обучающая выборка для `ranker.py`.

---

## 8. Referral (Реферал)

| Поле | Тип | Правила |
|---|---|---|
| `referral_id` | string | PK |
| `inviter_user_id` | string | FK → User |
| `invitee_token` | string | до регистрации |
| `invitee_user_id` | string \| null | после регистрации |
| `status` | enum | `invited` \| `registered` \| `purchase_confirmed` \| `reward_released` \| `blocked` \| `expired` |
| `status_timestamps` | object | время каждого перехода (FR-022) |
| `reward_amount` | number ≥ 0 | заполняется при `reward_released` |
| `fraud_score_ref` | string | FK → FraudScore |
| `window_deadline` | datetime | `registered_at + REFERRAL_WINDOW` |

**Переходы** (`referral.py`):

```
invited --invitee registers--> registered
        └─ constraint: invitee.device_id_hash ≠ inviter.device_id_hash
                     И invitee.payment_instrument_hash ≠ inviter.payment_instrument_hash
                     иначе --> blocked (self-referral, FR-017)
registered --invitee first confirmed purchase before window_deadline--> purchase_confirmed
registered --window_deadline passes--> expired (без награды, FR-024)
purchase_confirmed --antifraud pass + budget pre-check ok--> reward_released
                    (награда обеим сторонам, списание из budget_cap инвайтера — FR-023)
purchase_confirmed --antifraud review--> удержание, авто-разрешение (R4); при block --> blocked
any --antifraud block--> blocked
```

Награда **не** начисляется ни на одном статусе до `reward_released` (FR-021, US5 сценарий 1).

---

## 9. Promo (Акция) / PromoRanking

**Promo**: `{ promo_id, category, discount_type, margin_impact (number), eligibility_rules }`
— фикстура «от маркетинга» (`fixtures/data/promo_pool.json`).

**PromoRanking**: `{ user_id, promo_id, rank_score, shown_at, redeemed: bool }`.

**Правило ранжирования** (`promo.py`, FR-025/026/027):
`rank_score = w_cat·category_match(history) + w_rec·recency(category) + w_margin·normalized(margin_impact)`.
При равенстве по истории — выше `margin_impact` (FR-026). Пустая история ⇒ нейтральный
порядок по сегменту, без ошибки (FR-027).

---

## 10. FraudScore (Оценка риска)

| Поле | Тип | Правила |
|---|---|---|
| `fraud_score_id` | string | PK |
| `entity_type` | enum | `receipt` \| `referral` |
| `entity_id` | string | `receipt_id` \| `referral_id` |
| `score` | number 0..1 | нормированный `Σ wᵢ·fᵢ` |
| `threshold_used` | object | `{ review, block }` из `config.FRAUD_THRESHOLDS` |
| `decision` | enum | `pass` \| `review` \| `block`; на границе — строже (R4) |
| `feature_vector` | object | значения фич |
| `explanation` | object | вклад каждой фичи `wᵢ·fᵢ` (FR-016) |
| `review_outcome` | enum \| null | `pass` \| `block` — для `decision == review` (Q5) |
| `review_resolved_at` | datetime \| null | время авто-разрешения |

**Фичи** (R4): `receipt_velocity`, `archetype_deviation`, `device_hash_collision`,
`payment_hash_collision`, `invite_burst`.

---

## 11. RewardLedger (Реестр наград)

| Поле | Тип | Правила |
|---|---|---|
| `user_id` | string | FK → User |
| `iso_week` | string `YYYY-Www` | PK вместе с `user_id` |
| `budget_cap` | number ≥ 0 | `BUDGET_CAP_PCT × weekly_margin(archetype)` (R8) |
| `accrued_reward` | number ≥ 0 | сумма фактически начисленного |
| `spent_to_date` | number ≥ 0 | ≤ `budget_cap` (инвариант) |
| `rejections` | Rejection[] | `{ mechanic, reason: "budget_exceeded" \| "economy_invariant_violation", at }` |

**Pre-check перед выдачей** (R5, FR-018/019):
`reward_cost + spent_to_date ≤ budget_cap` **И** `reward_cost ≤ expected_margin_uplift(mechanic, user)`.
Полоса `review` не трогает `accrued_reward`/`spent_to_date` до авто-разрешения.

---

## 12. SyntheticUserProfile (только `sim/`)

`{ archetype_type, chain_code, segment, generation_params{}, behavior_distribution{} }`
— шаблон, из которого `generator.py` порождает поток `PurchaseEvent` и рёбра
социального графа (рефералы).

---

## 13. SimulationRun

| Поле | Тип | Правила |
|---|---|---|
| `run_id` | string | PK |
| `population_size` | int 1000..10000 | (US4) |
| `chain_mix` | object | доли по `TS5/TSX/TSC` × сегмент из `segment_mix.json` (§3.1) |
| `parameters` | object | сид RNG, число недель, версия `engine`, версия ранкера |
| `cohorts` | enum[] | всегда `["treatment", "control"]` (FR-032a) |

**Отношения**: 1:N `PilotMetric`.

---

## 14. PilotMetric

`{ run_id, name, kind: "primary" | "guardrail", cohort: "treatment" | "control",
value, period }`.

- **primary**: `d7_return_no_push`, `purchase_frequency`, `avg_check`.
- **guardrail**: `retention`, `referral_new_users`, `basket_items`, `session_length`.
- Отчёт приводит по обеим когортам + `delta = treatment − control`;
  `roi = Δmargin(treatment − control) − Σ reward_cost` (FR-033).

---

## Диаграмма связей (текстом)

```
User 1─1 Avatar
User 1─N PurchaseEvent ─fan-out→ Avatar / StreakState / Challenge-trigger / FraudScore
User 1─1 StreakState
User 1─N Challenge ─N─1 ChallengeTemplate ;  Challenge 1─N RecommendationLog
User 1─N Referral (as inviter) ─1─1 FraudScore ;  Referral N─1 User (as invitee)
User 1─N PromoRanking ─N─1 Promo
User 1─N RewardLedger (по ISO-неделям)
SimulationRun 1─N PilotMetric ;  SimulationRun uses SyntheticUserProfile[]
```
