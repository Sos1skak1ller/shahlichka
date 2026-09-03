/**
 * Zod-схемы и TS-типы контракта — ручная реализация JSON Schema из
 * specs/001-gaming-layer/contracts/*.schema.json (research.md R7).
 *
 * Синхронность с схемами проверяет web/tests/client.test.ts (валидация фикстур
 * против schemas/*.schema.json) и engine/tests/contract/test_schema_roundtrip.py.
 */
import { z } from "zod";

const isoWeek = z
  .string()
  .regex(/^\d{4}-W\d{2}$/, "ожидается формат YYYY-Www");

/* ----------------------------- profile-screen ---------------------------- */
export const AvatarViewSchema = z
  .object({
    level: z.number().int().min(0),
    visual_stage: z.number().int().min(1),
    state: z.enum(["progressing", "level_up_pending", "max_level"]),
    unlocked_customizations: z.array(z.string()),
    last_transition_at: z.string().nullable().optional(),
  })
  .strict();

export const SavingsViewSchema = z
  .object({
    total_saved_amount: z.number().min(0),
    current_threshold: z.number().min(0),
    next_threshold: z.number().nullable(),
    progress_ratio: z.number().min(0).max(1),
  })
  .strict();

export const StreakViewSchema = z
  .object({
    streak_count: z.number().int().min(0),
    last_active_week: isoWeek.nullable(),
  })
  .strict();

export const ProfileScreenViewSchema = z
  .object({
    user_id: z.string(),
    display_name: z.string().nullable().optional(),
    avatar: AvatarViewSchema,
    savings: SavingsViewSchema,
    streak: StreakViewSchema,
  })
  .strict();

export type ProfileScreenView = z.infer<typeof ProfileScreenViewSchema>;

/* ---------------------------- challenge-screen -------------------------- */
export const ChallengeViewSchema = z
  .object({
    challenge_id: z.string(),
    text: z.string().min(1),
    mechanic_type: z.enum([
      "category_repeat",
      "basket_growth",
      "streak_keep",
      "cross_chain",
    ]),
    generated_by: z.enum(["ml_ranker", "rule", "fallback"]),
    params: z
      .object({
        category: z.string(),
        n: z.number().int().min(1),
        deadline: z.string(),
      })
      .strict(),
    progress: z.number().int().min(0),
    target: z.number().int().min(1),
    status: z.enum(["active", "completed", "expired"]),
    valid_to: z.string(),
    reward_amount: z.number().min(0),
    within_budget: z.boolean().nullable().optional(),
  })
  .strict();

export const ChallengeScreenViewSchema = z
  .object({
    user_id: z.string(),
    iso_week: isoWeek,
    challenge: ChallengeViewSchema.nullable(),
    notes: z
      .array(
        z.enum([
          "cold_start_fallback",
          "template_pool_exhausted",
          "anti_fatigue_switch",
        ]),
      )
      .optional()
      .default([]),
  })
  .strict();

export type ChallengeScreenView = z.infer<typeof ChallengeScreenViewSchema>;

/* ---------------------------- referral-screen -------------------------- */
export const ReferralItemSchema = z
  .object({
    referral_id: z.string(),
    invitee_alias: z.string().nullable().optional(),
    status: z.enum([
      "invited",
      "registered",
      "purchase_confirmed",
      "reward_released",
      "blocked",
      "expired",
    ]),
    invited_at: z.string(),
    window_deadline: z.string().nullable().optional(),
    reward_amount: z.number().min(0).optional().default(0),
    block_reason: z
      .enum(["self_referral", "antifraud_block", "window_expired"])
      .nullable()
      .optional(),
  })
  .strict();

export const ReferralScreenViewSchema = z
  .object({
    user_id: z.string(),
    invite_link: z.string(),
    released_reward_total: z.number().min(0),
    budget_remaining_this_week: z.number().min(0).nullable().optional(),
    referrals: z.array(ReferralItemSchema).default([]),
  })
  .strict();

export type ReferralScreenView = z.infer<typeof ReferralScreenViewSchema>;
