import { z } from "zod";

export const PROMO_STORAGE_KEY = "x5-promo-studio-v1";
export const ASSIGNMENT_STORAGE_KEY = "x5-growth-assignment-v1";

export const PROMO_OBJECTIVES = [
  "retain_category",
  "expand_categories",
  "trade_up",
  "basket_completion",
] as const;

export const SHOPPING_MISSIONS = [
  "regular_replenishment",
  "stock_up",
  "quick_meal",
  "family_shopping",
  "home_care",
  "basket_completion",
] as const;

export const PROMO_CHANNELS = ["in_store", "delivery", "pickup"] as const;
export const PROMO_STATUSES = [
  "draft",
  "pending_marketing_review",
  "approved",
  "published",
  "unpublished",
  "paused",
] as const;

export const TARGET_METRICS = [
  "category_repeat_rate",
  "unique_categories_per_active_user",
  "incremental_margin",
  "cross_chain_rate",
  "digital_feature_adoption",
] as const;

export const PromoSchema = z
  .object({
    promo_id: z.string().min(3),
    title: z.string().min(3),
    description: z.string().min(5),
    objective: z.enum(PROMO_OBJECTIVES),
    category: z.string().min(1),
    shopping_missions: z.array(z.enum(SHOPPING_MISSIONS)).min(1),
    channels: z.array(z.enum(PROMO_CHANNELS)).min(1),
    discount_type: z.enum(["percent", "fixed"]),
    discount_value: z.number().positive(),
    margin_impact: z.number().min(0),
    eligibility_rules: z.object({ segments: z.array(z.string()) }),
    target_metric: z.enum(TARGET_METRICS),
    approval_status: z.enum(PROMO_STATUSES),
    demo_only: z.boolean(),
  })
  .superRefine((promo, ctx) => {
    if (promo.discount_type === "percent" && promo.discount_value > 100) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["discount_value"],
        message: "Процентная скидка не может превышать 100%",
      });
    }
  });

export const PromoPoolSchema = z.object({
  dataset_kind: z.string(),
  approval_status: z.string(),
  demo_only: z.boolean(),
  replace_before_pilot: z.boolean(),
  note: z.string(),
  promos: z.array(PromoSchema),
});

export const PublishedAssignmentSchema = z.object({
  promo_id: z.string(),
  client_id: z.string(),
  client_name: z.string(),
  client_description: z.string(),
  published_at: z.string(),
});

export type Promo = z.infer<typeof PromoSchema>;
export type PromoPool = z.infer<typeof PromoPoolSchema>;
export type PublishedAssignment = z.infer<typeof PublishedAssignmentSchema>;

export const CATEGORY_LABELS: Record<string, string> = {
  groceries: "Базовая корзина",
  household: "Товары для дома",
  hygiene: "Гигиена",
  dairy: "Молочные продукты",
  snacks: "Снеки",
  baby_food: "Детское питание",
  diapers: "Подгузники",
};

export const OBJECTIVE_LABELS: Record<(typeof PROMO_OBJECTIVES)[number], string> = {
  retain_category: "Удержать категорию",
  expand_categories: "Расширить корзину",
  trade_up: "Повысить ценность выбора",
  basket_completion: "Дополнить покупку",
};

export const MISSION_LABELS: Record<(typeof SHOPPING_MISSIONS)[number], string> = {
  regular_replenishment: "Регулярное пополнение",
  stock_up: "Закупка впрок",
  quick_meal: "Быстрая еда",
  family_shopping: "Семейная покупка",
  home_care: "Забота о доме",
  basket_completion: "Дополнение корзины",
};

export const CHANNEL_LABELS: Record<(typeof PROMO_CHANNELS)[number], string> = {
  in_store: "В магазине",
  delivery: "Доставка",
  pickup: "Самовывоз",
};

export const STATUS_LABELS: Record<(typeof PROMO_STATUSES)[number], string> = {
  draft: "Черновик",
  pending_marketing_review: "На проверке",
  approved: "Одобрено",
  published: "Опубликовано",
  unpublished: "Снято с публикации",
  paused: "Приостановлено",
};

export const METRIC_LABELS: Record<(typeof TARGET_METRICS)[number], string> = {
  category_repeat_rate: "Повторная покупка категории",
  unique_categories_per_active_user: "Уникальные категории на клиента",
  incremental_margin: "Инкрементальная маржа",
  cross_chain_rate: "Кросс-сетевые покупки",
  digital_feature_adoption: "Использование цифровых сервисов",
};
