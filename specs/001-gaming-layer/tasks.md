---

description: "Task list for feature implementation — Персональный игровой слой Х5 Клуб"
---

# Tasks: Персональный игровой слой Х5 Клуб

**Input**: Design documents from `/specs/001-gaming-layer/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — spec.md defines an "Independent Test" per user story and quickstart.md
is an explicit test plan; SC-004/005/006/007 are test-gated. Test tasks are therefore part
of every story.

**Organization**: Tasks are grouped by user story (US1–US6 from spec.md) for independent
implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US6; Setup/Foundational/Polish carry no story label
- File paths are relative to repository root unless noted

## Path Conventions (from plan.md)

- `engine/src/gaming_engine/` — deterministic compute core (Python, no I/O)
- `engine/tests/{unit,integration,contract}/` — pytest
- `sim/src/gaming_sim/` — synthetic data + cohort simulation (Python, imports engine)
- `fixtures/` — scripted scenario + generated screen JSON
- `web/src/` — React + TS demo (3 screens); `web/tests/` — vitest
- `specs/001-gaming-layer/contracts/*.schema.json` — JSON Schema, single source of truth

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository skeleton and toolchains for the three modules.

- [X] T001 Create repo directory structure (`engine/`, `sim/`, `fixtures/{data,out}/`, `web/`, `scripts/`) per plan.md "Source Code" tree
- [X] T002 [P] Initialize `engine/` Python package: `engine/pyproject.toml` (deps: `numpy`, `pandas`, `scikit-learn`, `pydantic`; `dev` extra: `pytest`, `ruff`) and `engine/src/gaming_engine/__init__.py`
- [X] T003 [P] Initialize `sim/` Python package: `sim/pyproject.toml` (deps: `gaming-engine` editable, `numpy`; `dev` extra: `pytest`, `ruff`) and `sim/src/gaming_sim/__init__.py`
- [X] T004 [P] Initialize `web/` project: Vite + React 18 + TypeScript + `vitest` + `@testing-library/react` + `zod` in `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`
- [X] T005 [P] Configure lint/format: `ruff` sections in `engine/pyproject.toml` and `sim/pyproject.toml`; ESLint + Prettier config in `web/`
- [X] T006 [P] Write `scripts/gen-contract-types.sh` — generate pydantic models (`engine/src/gaming_engine/contracts.py`) and TS types + zod schemas (`web/src/contract/`) from `specs/001-gaming-layer/contracts/*.schema.json`
- [X] T007 [P] Write `scripts/check-parity.sh` — run the demo scenario through `gaming_sim` and diff key numbers against `fixtures/out/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting engine infrastructure every user story depends on: the data
contract, illustrative config, the event log with idempotency, and the reward-economy
ledger (constitution principle III makes economy foundational, not per-story).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T008 Run `scripts/gen-contract-types.sh`; commit generated `engine/src/gaming_engine/contracts.py` and `web/src/contract/` (PurchaseEvent, 3 screen views, SimulationReport)
- [X] T009 [P] Implement `engine/src/gaming_engine/config.py` — illustrative constants from research.md R8 (`AVATAR_LEVELS` thresholds, `VISUAL_STAGES`, `ANTI_FATIGUE_N`, `BUDGET_CAP_PCT`, `WEEKLY_MARGIN_BY_ARCHETYPE`, `REVIEW_HOLD`, `REFERRAL_WINDOW`, `FRAUD_THRESHOLDS`, `PRECISION_TARGET`, `SEGMENT`), each annotated "illustrative — team to ratify"
- [X] T010 [P] Implement `engine/src/gaming_engine/weekcal.py` — `iso_week(timestamp) -> "YYYY-Www"`, week-adjacency and gap detection; no wall-clock access (research.md R2)
- [X] T011 Implement `engine/src/gaming_engine/event_log.py` — in-memory append-only log; ingest `PurchaseEvent`; dedup by `receipt_id` (FR-030a); route `corrects_receipt_id` to correction handling; reject orphan corrections (`orphan_correction` log); stable ordering by `(timestamp, receipt_id)` (data-model §3)
- [X] T012 Implement `engine/src/gaming_engine/ledger.py` — `RewardLedger` keyed `(user_id, iso_week)`; `budget_cap = BUDGET_CAP_PCT × weekly_margin(archetype)`; `pre_check(reward_cost, mechanic, user)` enforcing `spent_to_date + cost ≤ budget_cap`; record `rejections[]` with reason (data-model §11, FR-018)
- [X] T013 [P] Create `engine/tests/conftest.py` deterministic fixtures + golden-history loader; add 30–50 synthetic purchase histories as JSON under `engine/tests/integration/_histories/`
- [X] T014 [P] Contract test `engine/tests/contract/test_schema_roundtrip.py` — every `contracts/*.schema.json` round-trips through the generated pydantic models
- [X] T015 [P] Scaffold `fixtures/scenario.py` (scripted demo scenario stub using `gaming_engine`) and `fixtures/build.py` (writes `fixtures/out/*.json`, validates each against its screen schema); seed `fixtures/data/{promo_pool,segment_mix,challenge_templates}.json` with illustrative content
- [X] T016 [P] Scaffold `web/src/App.tsx` (3-tab shell) and `web/src/client.ts` (fixture-backed contract client: loads `fixtures/out/*.json`, validates with generated zod schemas, no network)

**Checkpoint**: Foundation ready — user stories can begin.

---

## Phase 3: User Story 1 - Аватар растёт от реальной экономии (Priority: P1) 🎯 MVP

**Goal**: Accumulated `saved_amount` from confirmed receipts drives the avatar level/visual
stage state machine; the profile/avatar screen renders it. App activity never moves progress.

**Independent Test**: Replay 30–50 synthetic histories → level & visual stage match the
golden values; 10 app-opens with no purchase leave progress unchanged; a `saved_amount ≤ 0`
receipt is a no-op; a correction can demote a level; at max level further savings accrue
without new levels.

### Tests for User Story 1

- [X] T017 [P] [US1] Integration test `engine/tests/integration/test_avatar_replay.py` — golden histories → `level`/`visual_stage` match (SC-005); covers threshold cross, 10 app-opens no-op, `saved_amount ≤ 0` no-op, correction demotion, max-level accrual
- [X] T018 [P] [US1] Integration test `engine/tests/integration/test_idempotency.py` — duplicate `receipt_id` does not change `total_saved_amount` or `streak_count` (FR-030a)
- [X] T019 [P] [US1] Web test `web/tests/screens/ProfileAvatar.test.tsx` — renders level, `savings.progress_ratio` bar, and `unlocked_customizations` from `fixtures/out/profile-screen.json`

### Implementation for User Story 1

- [X] T020 [P] [US1] Implement `engine/src/gaming_engine/avatar.py` — `Avatar` entity + state machine (`progressing` / `level_up_pending` / `max_level`); `apply_saved_amount`; thresholds from `config`; demotion on correction; append `transition_history`; unlock customization per level (data-model §2, FR-003/004/005)
- [X] T021 [P] [US1] Implement `engine/src/gaming_engine/streak.py` — `StreakState`; consecutive ISO weeks with ≥1 confirmed purchase; a purchase-less week resets to 0; correction may decrement (data-model §4, FR-006)
- [X] T022 [US1] Wire `event_log` fan-out to `avatar` + `streak` and add `get_profile_view(user_id) -> ProfileScreenView` to the engine projection API in `engine/src/gaming_engine/__init__.py`
- [X] T023 [US1] Extend `fixtures/scenario.py` with a US1 user journey; make `fixtures/build.py` emit `fixtures/out/profile-screen.json` (validated vs `profile-screen.schema.json`)
- [X] T024 [P] [US1] Implement `web/src/screens/ProfileAvatar.tsx` + `web/src/components/{ProgressBar,AvatarStage}.tsx` — render from `client.getProfileView()`
- [X] T025 [US1] Add a profile-screen fixture case to `web/tests/client.test.ts` (zod validation of the loaded fixture)

**Checkpoint**: US1 fully functional and demoable on its own — MVP.

---

## Phase 4: User Story 2 - Персональный недельный челлендж (Priority: P2)

**Goal**: One personalized weekly challenge per user, selected from purchase history + avatar
level by an explainable pipeline (template candidates + logistic-regression ranker), text
assembled from a template string, with cold-start fallback and anti-fatigue switching.

**Independent Test**: Two same-segment users with different history get different challenges;
the challenge category comes from the user's own history; `budget_cost` passes the pre-check;
empty history → `fallback`; exhausted template pool → `template_pool_exhausted` note;
`ANTI_FATIGUE_N` unanswered cycles → mechanic type switches. Expert relevance ≥ 70% on
30–50 held-out profiles (SC-001).

**Depends on**: US1 (avatar level feature), Foundational `ledger` (budget pre-check).

### Tests for User Story 2

- [X] T026 [P] [US2] Unit test `engine/tests/unit/test_challenge_features.py` — RFM-per-category, recency, archetype, avatar level assembled from an event stream
- [X] T027 [P] [US2] Unit test `engine/tests/unit/test_challenge_ranker.py` — different history → different top-1; chosen category ∈ user history; `generated_by` ∈ {`ml_ranker`,`rule`,`fallback`}; cold-start → `fallback`; pool exhausted → note; anti-fatigue after `ANTI_FATIGUE_N`
- [X] T028 [P] [US2] Unit test `engine/tests/unit/test_challenge_economy.py` — challenge whose `budget_cost > expected_margin_uplift` → `status = rejected_economy`, never shown (FR-019; US3 scenario 5)
- [X] T029 [P] [US2] Web test `web/tests/screens/Challenge.test.tsx` — renders challenge text, `progress`/`target`, notes; `challenge = null` → empty state

### Implementation for User Story 2

- [X] T030 [P] [US2] Implement `engine/src/gaming_engine/challenge/templates.py` — `ChallengeTemplate` registry from `fixtures/data/challenge_templates.json` (`mechanic_type`, `condition_pattern`, `reward_formula`, `eligibility_rules`, `param_space`) (data-model §5)
- [X] T031 [P] [US2] Implement `engine/src/gaming_engine/challenge/features.py` — feature builder (RFM by category, recency, archetype, avatar level)
- [X] T032 [US2] Implement `engine/src/gaming_engine/challenge/candidates.py` — eligibility filter (remaining budget cap, user categories, cooldown of K weeks on recently shown templates)
- [X] T033 [US2] Implement `engine/src/gaming_engine/challenge/ranker.py` — `sklearn` LogisticRegression ranker with serialized deterministic weights; rule-based fallback; delegates mechanic switch to `timing.py` (research.md R3, FR-009/013/014)
- [X] T034 [P] [US2] Implement `engine/src/gaming_engine/challenge/assemble.py` — parameter substitution into `condition_pattern` (FR-010); no free-text generation
- [X] T035 [US2] Implement `engine/src/gaming_engine/timing.py` — rule-based: no active challenge → generate; else consider referral reminder; anti-fatigue counter of unanswered cycles (research.md R3)
- [X] T036 [US2] Implement Challenge lifecycle in `engine/src/gaming_engine/challenge/__init__.py` — ≤ 1 `active` per user (FR-008), weekly `cache_key = {segment}:{iso_week}`, `progress` from confirming receipts (FR-012), `completed` → accrue via `ledger`, `expired` on `valid_to` (data-model §6)
- [X] T037 [US2] Add `get_challenge_view(user_id) -> ChallengeScreenView` to the engine projection API
- [X] T038 [US2] Extend `fixtures/scenario.py` + `fixtures/build.py` → emit `fixtures/out/challenge-screen.json`
- [X] T039 [P] [US2] Implement `web/src/screens/Challenge.tsx` — render from `client.getChallengeView()`
- [X] T040 [US2] Add relevance-labelling worksheet `specs/001-gaming-layer/eval/challenge-relevance.md` — 30–50 held-out profiles, ≥ 70% target (SC-001)

**Checkpoint**: US1 + US2 both work independently.

---

## Phase 5: User Story 3 - Антифрод чеков и рефералов + бюджетный потолок (Priority: P2)

**Goal**: Synchronous risk scoring of every receipt and referral before any reward, with a
fixed explicit threshold, per-feature explanation, three decision bands, deterministic
review-hold auto-resolution, and enforcement of the weekly budget cap + economy invariant on
top of the Foundational `ledger`.

**Independent Test**: Labeled synthetic set → precision on the fraud class ≥ 0.90 (SC-004);
weekly cap reached → accruals stop with `budget_exceeded`; review-band reward is held (not
accrued, not spent) and auto-resolves; a new risk signal during the hold window → `block`.

**Depends on**: Foundational `ledger`; integrates with US2 (challenge reward gate) and later US5.

### Tests for User Story 3

- [X] T041 [P] [US3] Integration test `engine/tests/integration/test_antifraud_precision.py` — labeled set (normal + receipt-velocity, device/payment hash collision, self-referral, invite burst) → `fraud_class_precision ≥ 0.90` (SC-004); recall reported, not gated
- [X] T042 [P] [US3] Integration test `engine/tests/integration/test_budget_cap.py` — weekly cap reached → `rejections[].reason = budget_exceeded`, no accrual
- [X] T043 [P] [US3] Unit test `engine/tests/unit/test_review_hold.py` — review band: reward not accrued / not spent; auto-resolve after `REVIEW_HOLD` → `pass`; new risk signal in window → `block` (FR-015a, edge case)
- [X] T044 [P] [US3] Unit test `engine/tests/unit/test_threshold_boundary.py` — score exactly at the block threshold → `block` (research.md R4)

### Implementation for User Story 3

- [X] T045 [P] [US3] Implement `engine/src/gaming_engine/antifraud.py` — feature extractors (`receipt_velocity`, `archetype_deviation`, `device_hash_collision`, `payment_hash_collision`, `invite_burst`); weighted scorecard `Σ wᵢ·fᵢ` normalized to 0..1; `FRAUD_THRESHOLDS` bands; `explanation{}` = per-feature contribution (data-model §10, FR-016)
- [X] T046 [US3] Implement the review-hold scheduler in `antifraud.py` — deterministic model-time queue; auto-resolve rule (pass if no new signal, else block); write `review_outcome` / `review_resolved_at`
- [X] T047 [US3] Wire the antifraud gate into the reward path — `event_log` / `challenge` / `referral` call `antifraud.score()` before `ledger.accrue()`; `block` → no reward, `review` → hold (FR-015)
- [X] T048 [US3] Add `expected_margin_uplift(mechanic, user)` (illustrative, research.md R8) to `ledger.py` and enforce `cost ≤ expected_margin_uplift` in `pre_check` (FR-019)
- [X] T049 [US3] Emit antifraud + economy counters from the engine run summary API for the sim report `antifraud` / `economy` blocks

**Checkpoint**: US1 + US2 + US3 independently functional.

---

## Phase 6: User Story 4 - Когортная симуляция и одностраничный план пилота (Priority: P2)

**Goal**: Offline run of 1–10k synthetic profiles through the *same* `gaming_engine`, split
into treatment (layer on) and control (layer off) cohorts from one population mix; primary +
guardrail metrics per cohort; ROI; one-page pilot plan.

**Independent Test**: Run 1k and 10k; sampled population reproduces the §3.1 segment×chain
mix within tolerance; report validates against `simulation-report.schema.json`; the same
scenario yields matching key numbers in sim and in the demo fixtures (SC-006).

**Depends on**: `gaming_engine` capabilities (runs richer as US1–US3/US5/US6 land); can start
after US1 with a minimal engine.

### Tests for User Story 4

- [X] T050 [P] [US4] Test `sim/tests/test_population_mix.py` — sampled `chain_mix` / segment shares match `fixtures/data/segment_mix.json` within tolerance (US4 scenario 1)
- [X] T051 [P] [US4] Test `sim/tests/test_cohort_split.py` — treatment and control drawn from an identical population sample; only `gaming_layer_enabled` differs
- [X] T052 [P] [US4] Test `sim/tests/test_parity.py` — same scenario: key numbers (avatar level, `budget_cost`) in `fixtures/out/*` equal the sim result (SC-006, FR-031)
- [X] T053 [P] [US4] Test `sim/tests/test_report_schema.py` — report validates against `contracts/simulation-report.schema.json` (SC-007)

### Implementation for User Story 4

- [X] T054 [P] [US4] Implement `sim/src/gaming_sim/archetypes.py` — 4–5 buyer archetypes with probabilistic check profiles (research.md R6)
- [X] T055 [P] [US4] Implement `sim/src/gaming_sim/population.py` — sampler proportional to the §3.1 segment×chain mix, weighted toward MP users
- [X] T056 [US4] Implement `sim/src/gaming_sim/generator.py` — emits `PurchaseEvent` stream + referral social-graph edges from `SyntheticUserProfile`, single seeded `numpy.random.Generator`
- [X] T057 [US4] Implement `sim/src/gaming_sim/runner.py` — CLI `python -m gaming_sim.runner --population --weeks --seed --out`; runs treatment and control cohorts through `gaming_engine`
- [X] T058 [US4] Implement `sim/src/gaming_sim/metrics.py` — primary (`d7_return_no_push`, `purchase_frequency`, `avg_check`) + guardrail (`retention`, `referral_new_users`, `basket_items`, `session_length`) per cohort with `delta = treatment − control`
- [X] T059 [US4] Implement `sim/src/gaming_sim/report.py` — assemble `SimulationReport` (metrics, `economy` with `roi` + `invariant_holds`, `antifraud` precision/recall, `pilot_plan`) as JSON per schema (FR-033)
- [X] T060 [US4] Thread a `gaming_layer_enabled` feature flag through the engine projection/reward path so the control cohort runs with mechanics disabled

**Checkpoint**: US4 runnable; SC-003 / SC-007 / SC-010 verifiable.

---

## Phase 7: User Story 5 - Реферальная программа с отложенной наградой (Priority: P3)

**Goal**: `invited → registered → purchase_confirmed → reward_released` state machine; reward
to both sides only after the invitee's first confirmed purchase; self-referral blocked by
device/payment hash; window expiry closes with no reward.

**Independent Test**: Walk a synthetic invitee through the states — no reward before
`purchase_confirmed`; matching device/payment hash → `blocked`; no purchase before the
window deadline → `expired`.

**Depends on**: US3 (antifraud self-referral + scoring), Foundational `ledger`.

### Tests for User Story 5

- [X] T061 [P] [US5] Unit test `engine/tests/unit/test_referral_state_machine.py` — all transitions; no accrual before `reward_released` (FR-021); device/payment hash collision → `blocked` (FR-017); window expiry → `expired` (FR-024)
- [X] T062 [P] [US5] Web test `web/tests/screens/Referral.test.tsx` — renders referral list, statuses, `released_reward_total`, `block_reason` from `fixtures/out/referral-screen.json`

### Implementation for User Story 5

- [X] T063 [P] [US5] Implement `engine/src/gaming_engine/referral.py` — `Referral` entity + state machine (data-model §8); `window_deadline = registered_at + REFERRAL_WINDOW`; self-referral constraint on `device_id_hash` / `payment_instrument_hash` (FR-017)
- [X] T064 [US5] Wire referral reward release through the antifraud gate + `ledger.accrue()` against the inviter's weekly cap (FR-023); deferred until `purchase_confirmed` (FR-021)
- [X] T065 [US5] Add `get_referral_view(user_id) -> ReferralScreenView` to the engine projection API
- [X] T066 [US5] Extend `fixtures/scenario.py` + `fixtures/build.py` → emit `fixtures/out/referral-screen.json`
- [X] T067 [P] [US5] Implement `web/src/screens/Referral.tsx` — render from `client.getReferralView()`
- [X] T068 [US5] Add referral edges + reward outcomes to `sim/src/gaming_sim/generator.py` so the `referral_new_users` guardrail is populated

**Checkpoint**: US1–US3 + US5 independently functional; all 3 screens complete.

---

## Phase 8: User Story 6 - Персонализированное ранжирование акций (Priority: P3)

**Goal**: Rank the marketing promo pool per profile (category match with history + recency +
promo margin); tie-break by margin; neutral segment order for no-history users. No new
screen (FR-007) — surfaced within existing views and validated by tests.

**Independent Test**: Recent-category promos rank above unseen categories; equal relevance →
higher margin wins; empty history → neutral order, no error. Hit rate ≥ 70% on 30–50
held-out profiles (SC-002).

**Depends on**: US2 `challenge/features.py` (shared RFM); otherwise independent.

### Tests for User Story 6

- [X] T069 [P] [US6] Unit test `engine/tests/unit/test_promo_ranking.py` — category-from-history ranks higher; margin tie-break (FR-026); empty history → neutral order, no error (FR-027)

### Implementation for User Story 6

- [X] T070 [P] [US6] Implement `engine/src/gaming_engine/promo.py` — load `fixtures/data/promo_pool.json`; `rank_score = w_cat·category_match + w_rec·recency + w_margin·norm(margin_impact)`; emit `PromoRanking[]` (data-model §9, FR-025/026/027)
- [X] T071 [US6] Expose `rank_promos(user_id) -> PromoRanking[]` in the engine projection API (consumed by existing screens/tests; no new screen)
- [X] T072 [US6] Add relevance-labelling worksheet `specs/001-gaming-layer/eval/promo-relevance.md` — ≥ 70% hit rate (SC-002)
- [X] T073 [US6] Feed a promo-redemption signal into `sim/src/gaming_sim/metrics.py` (affects `avg_check` / `basket_items`)

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T074 [P] Run all 6 `quickstart.md` scenarios; record pass/fail + numbers in `specs/001-gaming-layer/quickstart-results.md`
- [X] T075 [P] Privacy audit: assert no PII field (name/address) in any entity or schema; document in `quickstart-results.md` (SC-008)
- [X] T076 [P] Naming/scope audit: grep `web/src/` and `fixtures/` for "AI"/"ИИ"; confirm exactly 3 screens (SC-009, FR-007/035)
- [X] T077 [P] Add CI workflow `.github/workflows/ci.yml` — `engine` pytest, `sim` pytest, `web` vitest, `scripts/check-parity.sh` (guards FR-031 / SC-006)
- [X] T078 Performance check: 10k-profile sim run < 60 s; fixture rebuild < 5 s; record numbers in `quickstart-results.md`
- [X] T079 [P] Write one-page pilot plan `specs/001-gaming-layer/pilot-plan.md` from `SimulationReport.pilot_plan` (H1–H3 hypotheses, primary/guardrail metrics, ROI formula) (SC-010)
- [X] T080 [P] Update `README.md` with run instructions for `engine` / `sim` / `web` and the two documented case deviations (FR-036)
- [X] T081 Tune `ranker.py` weights and `FRAUD_THRESHOLDS` against the labeled sets until SC-001 / SC-002 ≥ 70% and SC-004 ≥ 0.90; freeze serialized artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Setup — **blocks all user stories**
- **User Stories (Phases 3–8)**: all depend on Foundational
  - US1 (P1): no story dependencies
  - US2 (P2): depends on **US1** (avatar level feature) + Foundational `ledger`
  - US3 (P2): depends on Foundational `ledger`; US2 challenge reward path integrates with US3's gate (US2 testable before US3 with the gate stubbed to `pass`)
  - US4 (P2): depends on `gaming_engine` — minimal after US1, richer after US2/US3/US5/US6
  - US5 (P3): depends on **US3** (antifraud self-referral + scoring) + Foundational `ledger`
  - US6 (P3): depends on **US2** `challenge/features.py`; otherwise independent
- **Polish (Phase 9)**: depends on all targeted stories being complete

### Within Each User Story

- Tests are written first and must fail before implementation
- Models before services before projection API before web screen before fixtures
- Story is validated at its checkpoint before moving on

### Parallel Opportunities

- Setup: T002–T007 all `[P]`
- Foundational: T009, T010, T013, T014, T015, T016 `[P]` (after T008); T011 then T012 are sequential (ledger reads the event log's week calc)
- US1: tests T017–T019 `[P]`; then T020 + T021 `[P]`; T024 `[P]` with engine work
- US2: tests T026–T029 `[P]`; T030, T031, T034 `[P]`; T039 `[P]`
- US3: tests T041–T044 `[P]`; T045 `[P]` then T046→T047→T048 sequential (same file / call path)
- US4: tests T050–T053 `[P]`; T054, T055 `[P]`
- US5: T061, T062 `[P]`; T063, T067 `[P]`
- US6: T069 then T070 `[P]`
- Across teams: once Foundational is done, US1 → then US2/US3/US4 in parallel by different devs; US5/US6 after their deps

---

## Parallel Example: User Story 1

```bash
# Tests first (all fail), in parallel:
Task: "Integration test engine/tests/integration/test_avatar_replay.py"
Task: "Integration test engine/tests/integration/test_idempotency.py"
Task: "Web test web/tests/screens/ProfileAvatar.test.tsx"

# Then core models in parallel:
Task: "Implement engine/src/gaming_engine/avatar.py"
Task: "Implement engine/src/gaming_engine/streak.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational (contract types, config, event log, ledger) — **blocks everything**
3. Phase 3: US1 — avatar from savings + profile screen
4. **STOP and VALIDATE**: run `test_avatar_replay.py` and the profile screen with no network
5. Demo the avatar screen — this is a viable standalone MVP

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 → avatar screen (MVP demo)
3. + US2 → weekly personal challenge screen
4. + US3 → antifraud gate + budget cap enforced on all rewards
5. + US4 → cohort simulation + pilot plan (defensible numbers)
6. + US5 → referral screen (3 screens complete)
7. + US6 → personalized promo ranking inside existing screens
8. Phase 9 polish → quickstart green, CI, tuned thresholds, pilot-plan.md

### Parallel Team Strategy

After Foundational: dev A takes US1 → then US2; dev B takes US3 (gate stub for US2 until ready);
dev C starts US4 harness on the minimal engine and enriches it as stories land; US5 and US6
picked up once US3 / US2 respectively are done.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task
- `[Story]` label ties each task to a spec.md user story for traceability
- Every story is independently completable and testable at its checkpoint
- Verify each test fails before implementing
- Commit after each task or logical group
- The engine stays I/O-free and deterministic (research.md R2) — no wall-clock, seeded RNG only in `sim/`
- Illustrative constants live only in `engine/src/gaming_engine/config.py` — one place for the team to ratify
