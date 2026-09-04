import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import seedSource from "../../../fixtures/data/promo_pool.json";
import {
  ASSIGNMENT_STORAGE_KEY,
  CATEGORY_LABELS,
  CHANNEL_LABELS,
  METRIC_LABELS,
  MISSION_LABELS,
  OBJECTIVE_LABELS,
  PROMO_CHANNELS,
  PROMO_OBJECTIVES,
  PROMO_STORAGE_KEY,
  PROMO_STATUSES,
  PromoPoolSchema,
  PromoSchema,
  PublishedAssignmentSchema,
  SHOPPING_MISSIONS,
  STATUS_LABELS,
  TARGET_METRICS,
  type Promo,
  type PublishedAssignment,
} from "./types";

const seedPool = PromoPoolSchema.parse(seedSource);

const CATEGORIES = [
  "groceries",
  "dairy",
  "snacks",
  "household",
  "hygiene",
  "baby_food",
  "diapers",
] as const;

type FilterStatus = "all" | Promo["approval_status"];
type EditorTab = "settings" | "forecast" | "results" | "preview";

interface AnalyticsSnapshot {
  estimatedReach: number;
  expectedUpliftPct: number;
  budgetRub: number;
  expectedIncrementalMarginRub: number;
  rewardToMarginPct: number;
  exposedUsers: number;
  activatedUsers: number;
  convertedUsers: number;
  controlConversionPct: number;
  treatmentConversionPct: number;
  actualCostRub: number;
  actualIncrementalMarginRub: number;
}

function analyticsFor(promo: Promo): AnalyticsSnapshot {
  const fingerprint = [...promo.promo_id].reduce(
    (total, letter) => total + letter.charCodeAt(0),
    0,
  );
  const estimatedReach = 3_500 + (fingerprint % 145) * 100;
  const expectedUpliftPct = Number((1.4 + (fingerprint % 29) / 10).toFixed(1));
  const estimatedDiscount =
    promo.discount_type === "percent"
      ? 650 * (promo.discount_value / 100)
      : promo.discount_value;
  const budgetRub = Math.round((estimatedReach * estimatedDiscount * 0.18) / 1_000) * 1_000;
  const rewardToMarginPct = 27 + (fingerprint % 12);
  const expectedIncrementalMarginRub = Math.round(
    budgetRub / (rewardToMarginPct / 100),
  );
  const exposedUsers = Math.round(estimatedReach * 0.68);
  const activatedUsers = Math.round(exposedUsers * 0.31);
  const controlConversionPct = Number((27 + (fingerprint % 45) / 10).toFixed(1));
  const treatmentConversionPct = Number(
    (controlConversionPct + expectedUpliftPct * 0.82).toFixed(1),
  );
  const convertedUsers = Math.round(
    exposedUsers * (treatmentConversionPct / 100),
  );
  const actualCostRub = Math.round(budgetRub * 0.72);
  const actualIncrementalMarginRub = Math.round(expectedIncrementalMarginRub * 0.76);

  return {
    estimatedReach,
    expectedUpliftPct,
    budgetRub,
    expectedIncrementalMarginRub,
    rewardToMarginPct,
    exposedUsers,
    activatedUsers,
    convertedUsers,
    controlConversionPct,
    treatmentConversionPct,
    actualCostRub,
    actualIncrementalMarginRub,
  };
}

function compactNumber(value: number) {
  return new Intl.NumberFormat("ru-RU", {
    notation: value >= 10_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

function rubles(value: number) {
  return `${compactNumber(value)} ₽`;
}

function ForecastPanel({ promo }: { promo: Promo }) {
  const analytics = analyticsFor(promo);
  const withinGuardrail = analytics.rewardToMarginPct <= 35;
  const ratioWidth = Math.min((analytics.rewardToMarginPct / 50) * 100, 100);

  return (
    <section className="ps-analytics-panel">
      <div className="ps-data-label"><span>≈</span> Синтетический прогноз · не фактические данные X5</div>
      <div className="ps-metric-grid">
        <article><span>Ожидаемый охват</span><strong>{compactNumber(analytics.estimatedReach)}</strong><small>клиентов</small></article>
        <article><span>Прогноз uplift</span><strong>+{analytics.expectedUpliftPct} п.п.</strong><small>к контрольной группе</small></article>
        <article><span>Бюджет промо</span><strong>{rubles(analytics.budgetRub)}</strong><small>при redemption 18%</small></article>
        <article><span>Инкр. маржа</span><strong>{rubles(analytics.expectedIncrementalMarginRub)}</strong><small>ожидаемая</small></article>
      </div>

      <article className="ps-economics">
        <div className="ps-economics__head">
          <div><span>Экономический guardrail</span><strong>Награды / инкрементальная маржа</strong></div>
          <b className={withinGuardrail ? "is-good" : "is-risk"}>{analytics.rewardToMarginPct}%</b>
        </div>
        <div className="ps-meter"><i style={{ width: `${ratioWidth}%` }} /><em style={{ left: "70%" }} /></div>
        <div className="ps-economics__foot">
          <span>0%</span>
          <strong>{withinGuardrail ? "Проходит порог ≤ 35%" : "Выше допустимого порога 35%"}</strong>
          <span>50%</span>
        </div>
      </article>

      <article className="ps-model-note">
        <span>Что влияет на прогноз</span>
        <ul>
          <li>размер целевого сегмента и частота покупок категории;</li>
          <li>размер скидки и ожидаемая доля активаций;</li>
          <li>цель «{OBJECTIVE_LABELS[promo.objective]}» и метрика «{METRIC_LABELS[promo.target_metric]}».</li>
        </ul>
      </article>
    </section>
  );
}

function ResultsPanel({ promo }: { promo: Promo }) {
  const analytics = analyticsFor(promo);
  const activationPct = Math.round(
    (analytics.activatedUsers / analytics.exposedUsers) * 100,
  );
  const conversionPct = Math.round(
    (analytics.convertedUsers / analytics.exposedUsers) * 100,
  );
  const actualRatio = Math.round(
    (analytics.actualCostRub / analytics.actualIncrementalMarginRub) * 100,
  );

  return (
    <section className="ps-analytics-panel">
      <div className="ps-data-label ps-data-label--result"><span>i</span> Демонстрация результата A/B-теста · появится после запуска</div>
      <article className="ps-ab-result">
        <div className="ps-ab-result__head">
          <div><span>Целевая метрика</span><strong>{METRIC_LABELS[promo.target_metric]}</strong></div>
          <b>+{(analytics.treatmentConversionPct - analytics.controlConversionPct).toFixed(1)} п.п.</b>
        </div>
        <div className="ps-ab-bars">
          <div><span>Контроль</span><i><em style={{ width: `${analytics.controlConversionPct * 2}%` }} /></i><strong>{analytics.controlConversionPct}%</strong></div>
          <div><span>Промо</span><i><em style={{ width: `${analytics.treatmentConversionPct * 2}%` }} /></i><strong>{analytics.treatmentConversionPct}%</strong></div>
        </div>
      </article>

      <div className="ps-funnel">
        <article><span>Увидели</span><strong>{compactNumber(analytics.exposedUsers)}</strong><small>100%</small></article>
        <i>→</i>
        <article><span>Активировали</span><strong>{compactNumber(analytics.activatedUsers)}</strong><small>{activationPct}%</small></article>
        <i>→</i>
        <article><span>Купили</span><strong>{compactNumber(analytics.convertedUsers)}</strong><small>{conversionPct}%</small></article>
      </div>

      <div className="ps-result-economics">
        <article><span>Фактическая стоимость</span><strong>{rubles(analytics.actualCostRub)}</strong></article>
        <article><span>Инкр. маржа</span><strong>{rubles(analytics.actualIncrementalMarginRub)}</strong></article>
        <article><span>Награды / маржа</span><strong>{actualRatio}%</strong></article>
      </div>

      <div className="ps-decision">
        <span>Автоматический вердикт</span>
        <strong>{actualRatio <= 35 ? "Кандидат на масштабирование" : "Нужна корректировка экономики"}</strong>
        <p>Решение появится только после достижения минимального размера выборки и проверки статистической значимости.</p>
      </div>
    </section>
  );
}

const DEMO_CLIENTS = [
  {
    id: "m2_steady",
    name: "Анна · M2",
    description: "4 покупки в месяц · доля X5 52%",
    categories: ["dairy", "groceries", "baby_food", "diapers"],
    cycle: "Привычный цикл категории подходит к концу",
  },
  {
    id: "m2_oscillating",
    name: "Артём · M2",
    description: "3 покупки в месяц · доля X5 41%",
    categories: ["groceries", "snacks", "hygiene"],
    cycle: "Следующая покупка ожидается в ближайшие 3 дня",
  },
  {
    id: "m2_cross_shopper",
    name: "Елена · M2",
    description: "5 покупок в месяц · доля X5 36%",
    categories: ["household", "hygiene", "dairy"],
    cycle: "Категория регулярно покупается, но не всегда в X5",
  },
] as const;

function customerAction(promo: Promo) {
  const category = CATEGORY_LABELS[promo.category] ?? promo.category;
  if (promo.objective === "expand_categories") {
    return `Добавьте категорию «${category}» в следующую корзину`;
  }
  if (promo.objective === "trade_up") {
    return `Попробуйте новый товар в категории «${category}»`;
  }
  if (promo.objective === "basket_completion") {
    return `Дополните следующую покупку категорией «${category}»`;
  }
  return `Совершите ещё одну покупку в категории «${category}»`;
}

interface PreviewPanelProps {
  promo: Promo;
  canPublish: boolean;
  assignment?: PublishedAssignment;
  onPublish: (client: (typeof DEMO_CLIENTS)[number]) => void;
}

function PreviewPanel({ promo, canPublish, assignment, onPublish }: PreviewPanelProps) {
  const assignedClientId = DEMO_CLIENTS.some(
    (client) => client.id === assignment?.client_id,
  )
    ? assignment?.client_id as (typeof DEMO_CLIENTS)[number]["id"]
    : DEMO_CLIENTS[0].id;
  const [clientId, setClientId] = useState<(typeof DEMO_CLIENTS)[number]["id"]>(
    assignedClientId,
  );
  const client = DEMO_CLIENTS.find((item) => item.id === clientId) ?? DEMO_CLIENTS[0];
  const categoryMatch = (client.categories as readonly string[]).includes(promo.category);
  const matchScore = categoryMatch ? 86 : 58;
  const isPublished = promo.approval_status === "published";

  return (
    <section className="ps-preview-panel">
      <div className="ps-data-label ps-data-label--result"><span>✓</span> Предпросмотр на синтетическом профиле клиента</div>
      <label className="ps-preview-client">
        <span>{isPublished ? "Назначенный клиент" : "Тестовый клиент"}</span>
        <select disabled={isPublished} value={clientId} onChange={(event) => setClientId(event.target.value as typeof clientId)}>
          {DEMO_CLIENTS.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.description}</option>)}
        </select>
      </label>

      <article className="ps-assignment-reason">
        <div>
          <span>Соответствие промо</span>
          <strong>{matchScore}%</strong>
        </div>
        <ul>
          <li>{categoryMatch ? "Категория входит в привычную корзину клиента" : "Категория может расширить привычную корзину"}</li>
          <li>{client.cycle}</li>
          <li>Промо проверяет метрику «{METRIC_LABELS[promo.target_metric]}»</li>
        </ul>
      </article>

      <div className="ps-phone-preview" aria-label="Предпросмотр в X5 Рост">
        <header><span>Х5 Клуб · Рост</span><b>{client.name.split(" · ")[0].slice(0, 1)}</b></header>
        <main>
          <small>Персональная цель</small>
          <h3>До следующей награды — один шаг</h3>
          <div className="ps-client-progress"><i /><span>1 из 2</span></div>
          <p>{customerAction(promo)}</p>
          <div className="ps-client-reward">
            <span>Награда</span>
            <strong>{discountLabel(promo)} на следующую покупку</strong>
          </div>
          <button type="button">Посмотреть условия</button>
        </main>
      </div>

      <div className="ps-publish-box">
        {isPublished ? (
          <>
            <div><span>Статус</span><strong>Промо опубликовано в X5 Рост</strong></div>
            <a className="ps-button ps-button--primary" href="/">Открыть X5 Рост →</a>
          </>
        ) : (
          <>
            <div><span>Публикация</span><strong>{canPublish ? "Промо готово к публикации" : "Сначала сохраните промо со статусом «Одобрено»"}</strong></div>
            <button className="ps-button ps-button--primary" type="button" disabled={!canPublish} onClick={() => onPublish(client)}>Опубликовать</button>
          </>
        )}
      </div>
    </section>
  );
}

function blankPromo(): Promo {
  return {
    promo_id: `promo_${Date.now()}`,
    title: "",
    description: "",
    objective: "retain_category",
    category: "groceries",
    shopping_missions: ["regular_replenishment"],
    channels: ["in_store"],
    discount_type: "percent",
    discount_value: 5,
    margin_impact: 0,
    eligibility_rules: { segments: [] },
    target_metric: "category_repeat_rate",
    approval_status: "draft",
    demo_only: true,
  };
}

function readStoredPromos(): Promo[] {
  try {
    const saved = window.localStorage.getItem(PROMO_STORAGE_KEY);
    if (!saved) return seedPool.promos;
    return PromoPoolSchema.parse(JSON.parse(saved)).promos;
  } catch {
    return seedPool.promos;
  }
}

function readStoredAssignment(): PublishedAssignment | undefined {
  try {
    const saved = window.localStorage.getItem(ASSIGNMENT_STORAGE_KEY);
    return saved ? PublishedAssignmentSchema.parse(JSON.parse(saved)) : undefined;
  } catch {
    return undefined;
  }
}

function reconcilePublishedPromos(
  promos: Promo[],
  assignment: PublishedAssignment | undefined,
) {
  if (!assignment) return promos;
  return promos.map((promo) =>
    promo.approval_status === "published" && promo.promo_id !== assignment.promo_id
      ? { ...promo, approval_status: "unpublished" as const }
      : promo,
  );
}

function poolFor(promos: Promo[]) {
  return {
    dataset_kind: "promo_studio_export",
    approval_status: "mixed",
    demo_only: promos.every((promo) => promo.demo_only),
    replace_before_pilot: promos.some((promo) => promo.demo_only),
    note: "Экспорт Promo Studio. Промо со статусом demo_only нельзя использовать в пилоте без проверки маркетолога.",
    promos,
  };
}

function discountLabel(promo: Promo) {
  return promo.discount_type === "percent"
    ? `${promo.discount_value}%`
    : `${promo.discount_value} ₽`;
}

function promoFieldErrors(promo: Promo): Record<string, string> {
  const result = PromoSchema.safeParse(promo);
  if (result.success) return {};
  return Object.fromEntries(
    result.error.issues.map((issue) => [String(issue.path[0]), issue.message]),
  );
}

export function PromoStudio() {
  const [promos, setPromos] = useState<Promo[]>(() =>
    reconcilePublishedPromos(readStoredPromos(), readStoredAssignment()),
  );
  const [assignment, setAssignment] = useState<PublishedAssignment | undefined>(
    readStoredAssignment,
  );
  const [draft, setDraft] = useState<Promo | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("Изменения сохраняются локально в этом браузере");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<FilterStatus>("all");
  const [editorTab, setEditorTab] = useState<EditorTab>("settings");
  const importRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    window.localStorage.setItem(PROMO_STORAGE_KEY, JSON.stringify(poolFor(promos)));
  }, [promos]);

  useEffect(() => {
    const refreshFromStorage = () => {
      const storedAssignment = readStoredAssignment();
      setPromos(reconcilePublishedPromos(readStoredPromos(), storedAssignment));
      setAssignment(storedAssignment);
    };
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") refreshFromStorage();
    };
    window.addEventListener("storage", refreshFromStorage);
    window.addEventListener("focus", refreshFromStorage);
    window.addEventListener("pageshow", refreshFromStorage);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      window.removeEventListener("storage", refreshFromStorage);
      window.removeEventListener("focus", refreshFromStorage);
      window.removeEventListener("pageshow", refreshFromStorage);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, []);

  useEffect(() => {
    if (!draft) return;
    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDraft(null);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [draft]);

  const visiblePromos = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return promos.filter((promo) => {
      const matchesStatus = status === "all" || promo.approval_status === status;
      const haystack = `${promo.title} ${promo.promo_id} ${promo.category}`.toLowerCase();
      return matchesStatus && (!normalized || haystack.includes(normalized));
    });
  }, [promos, query, status]);

  const pendingCount = promos.filter(
    (promo) => promo.approval_status === "pending_marketing_review",
  ).length;
  const portfolioForecast = useMemo(
    () => promos.map(analyticsFor),
    [promos],
  );
  const totalBudget = portfolioForecast.reduce((sum, item) => sum + item.budgetRub, 0);
  const totalExpectedMargin = portfolioForecast.reduce(
    (sum, item) => sum + item.expectedIncrementalMarginRub,
    0,
  );

  const openNew = () => {
    setEditingId(null);
    setDraft(blankPromo());
    setEditorTab("settings");
    setErrors({});
  };

  const openEdit = (promo: Promo, tab: EditorTab = "settings") => {
    setEditingId(promo.promo_id);
    setDraft(structuredClone(promo));
    setEditorTab(tab);
    setErrors({});
  };

  const duplicate = (promo: Promo) => {
    const copy = {
      ...structuredClone(promo),
      promo_id: `${promo.promo_id}_copy_${Date.now()}`,
      title: `${promo.title} — копия`,
      approval_status: "draft" as const,
      demo_only: true,
    };
    setPromos((current) => [copy, ...current]);
    setNotice(`Создан черновик «${copy.title}»`);
    openEdit(copy);
  };

  const remove = (promo: Promo) => {
    if (!window.confirm(`Удалить промо «${promo.title}»?`)) return;
    setPromos((current) => current.filter((item) => item.promo_id !== promo.promo_id));
    if (editingId === promo.promo_id) setDraft(null);
    setNotice("Промо удалено");
  };

  const saveDraft = (event: FormEvent) => {
    event.preventDefault();
    if (!draft) return;
    const validation = promoFieldErrors(draft);
    const duplicateId = promos.some(
      (promo) => promo.promo_id === draft.promo_id && promo.promo_id !== editingId,
    );
    if (duplicateId) validation.promo_id = "Такой ID уже существует";
    if (Object.keys(validation).length) {
      setErrors(validation);
      setNotice("Проверьте обязательные поля");
      return;
    }

    const parsed = PromoSchema.parse(draft);
    setPromos((current) => {
      if (!editingId) return [parsed, ...current];
      return current.map((promo) => (promo.promo_id === editingId ? parsed : promo));
    });
    setDraft(null);
    setEditingId(null);
    setErrors({});
    setNotice(`Промо «${parsed.title}» сохранено`);
  };

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(poolFor(promos), null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "promo-pool.json";
    link.click();
    URL.revokeObjectURL(url);
    setNotice(`Экспортировано промо: ${promos.length}`);
  };

  const importJson = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const imported = PromoPoolSchema.parse(JSON.parse(await file.text()));
      setPromos(imported.promos);
      setDraft(null);
      setNotice(`Импортировано промо: ${imported.promos.length}`);
    } catch {
      setNotice("Файл не импортирован: проверьте структуру и обязательные поля");
    } finally {
      event.target.value = "";
    }
  };

  const resetSeed = () => {
    if (!window.confirm("Заменить текущий список исходным демо-набором?")) return;
    setPromos(seedPool.promos);
    setAssignment(undefined);
    window.localStorage.removeItem(ASSIGNMENT_STORAGE_KEY);
    setDraft(null);
    setNotice("Восстановлен исходный демо-набор");
  };

  const publishDraft = (client: (typeof DEMO_CLIENTS)[number]) => {
    if (!draft || !editingId) return;
    const savedPromo = promos.find((promo) => promo.promo_id === editingId);
    if (!savedPromo || savedPromo.approval_status !== "approved") return;
    const published: Promo = { ...savedPromo, approval_status: "published" };
    const nextPromos = promos.map((promo) => {
      if (promo.promo_id === editingId) return published;
      if (promo.approval_status === "published") {
        return { ...promo, approval_status: "unpublished" as const };
      }
      return promo;
    });
    setPromos(nextPromos);
    const nextAssignment: PublishedAssignment = {
      promo_id: published.promo_id,
      client_id: client.id,
      client_name: client.name.split(" · ")[0],
      client_description: client.description,
      published_at: new Date().toISOString(),
    };
    window.localStorage.setItem(PROMO_STORAGE_KEY, JSON.stringify(poolFor(nextPromos)));
    window.localStorage.setItem(
      ASSIGNMENT_STORAGE_KEY,
      JSON.stringify(nextAssignment),
    );
    setAssignment(nextAssignment);
    setDraft(published);
    setNotice(`Промо «${published.title}» опубликовано в X5 Рост`);
  };

  const updateDraft = <K extends keyof Promo>(key: K, value: Promo[K]) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
    setErrors((current) => ({ ...current, [key]: "" }));
  };

  const toggleArrayValue = <K extends "shopping_missions" | "channels">(
    key: K,
    value: Promo[K][number],
  ) => {
    if (!draft) return;
    const current = draft[key] as string[];
    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];
    updateDraft(key, next as Promo[K]);
  };

  return (
    <div className="promo-studio">
      <header className="ps-header">
        <div className="ps-brand">
          <a className="ps-back" href="/" aria-label="Вернуться в клиентское приложение">←</a>
          <div className="ps-brandmark">X5</div>
          <div>
            <div className="ps-eyebrow">Команда лояльности</div>
            <h1>Promo Studio</h1>
          </div>
        </div>
        <div className="ps-header-actions">
          <button className="ps-button ps-button--ghost" type="button" onClick={() => importRef.current?.click()}>
            Импорт JSON
          </button>
          <input ref={importRef} className="ps-file" type="file" accept="application/json" onChange={importJson} />
          <button className="ps-button ps-button--ghost" type="button" onClick={exportJson}>Экспорт</button>
          <button className="ps-button ps-button--primary" type="button" onClick={openNew}>+ Новое промо</button>
        </div>
      </header>

      <main className="ps-main">
        <section className="ps-warning" aria-label="Статус демо-данных">
          <span className="ps-warning__icon">!</span>
          <div>
            <strong>Демо-набор · не прошёл проверку маркетолога</strong>
            <p>Скидки и влияние на маржу сейчас иллюстративные. Перед пилотом записи demo_* нужно заменить.</p>
          </div>
          <button type="button" onClick={resetSeed}>Восстановить демо</button>
        </section>

        <section className="ps-overview" aria-label="Сводка">
          <article><span>Всего промо</span><strong>{promos.length}</strong></article>
          <article><span>На проверке</span><strong>{pendingCount}</strong></article>
          <article><span>Прогноз бюджета</span><strong>{rubles(totalBudget)}</strong></article>
          <article><span>Ожидаемая инкр. маржа</span><strong>{rubles(totalExpectedMargin)}</strong></article>
          <article className="ps-overview__wide"><span>Состояние</span><strong className="ps-notice">{notice}</strong></article>
        </section>

        <section className="ps-workspace">
          <div className="ps-list-panel">
            <div className="ps-section-head">
              <div>
                <span className="ps-eyebrow">Библиотека</span>
                <h2>Промо-механики</h2>
              </div>
              <span className="ps-result-count">{visiblePromos.length} из {promos.length}</span>
            </div>

            <div className="ps-filters">
              <label className="ps-search">
                <span>Поиск</span>
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Название, ID или категория" />
              </label>
              <label>
                <span>Статус</span>
                <select value={status} onChange={(event) => setStatus(event.target.value as FilterStatus)}>
                  <option value="all">Все статусы</option>
                  {PROMO_STATUSES.map((item) => <option key={item} value={item}>{STATUS_LABELS[item]}</option>)}
                </select>
              </label>
            </div>

            <div className="ps-promo-list">
              {visiblePromos.map((promo) => {
                const analytics = analyticsFor(promo);
                return (
                <article className="ps-promo-card" key={promo.promo_id}>
                  <div className="ps-promo-card__top">
                    <div>
                      <span className={`ps-status ps-status--${promo.approval_status}`}>{STATUS_LABELS[promo.approval_status]}</span>
                      <h3>{promo.title}</h3>
                      <code>{promo.promo_id}</code>
                    </div>
                    <strong className="ps-discount">{discountLabel(promo)}</strong>
                  </div>
                  <p>{promo.description}</p>
                  <dl className="ps-promo-meta">
                    <div><dt>Цель</dt><dd>{OBJECTIVE_LABELS[promo.objective]}</dd></div>
                    <div><dt>Категория</dt><dd>{CATEGORY_LABELS[promo.category] ?? promo.category}</dd></div>
                    <div><dt>Метрика</dt><dd>{METRIC_LABELS[promo.target_metric]}</dd></div>
                  </dl>
                  <dl className="ps-card-analytics">
                    <div><dt>Прогноз охвата</dt><dd>{compactNumber(analytics.estimatedReach)}</dd></div>
                    <div><dt>Uplift</dt><dd>+{analytics.expectedUpliftPct} п.п.</dd></div>
                    <div><dt>Бюджет</dt><dd>{rubles(analytics.budgetRub)}</dd></div>
                  </dl>
                  <div className="ps-card-actions">
                    <button className="ps-analysis-action" type="button" onClick={() => openEdit(promo, "forecast")}>Аналитика и превью</button>
                    <button type="button" onClick={() => openEdit(promo)}>Редактировать</button>
                    <button type="button" onClick={() => duplicate(promo)}>Дублировать</button>
                    <button className="ps-danger" type="button" onClick={() => remove(promo)}>Удалить</button>
                  </div>
                </article>
                );
              })}
              {!visiblePromos.length && <div className="ps-empty">По этим условиям промо не найдено</div>}
            </div>
          </div>

          {draft && (
            <button
              className="ps-editor-backdrop"
              type="button"
              aria-label="Закрыть редактор"
              onClick={() => setDraft(null)}
            />
          )}
          <aside
            className={`ps-editor ${draft ? "ps-editor--open" : ""}`}
            role={draft ? "dialog" : undefined}
            aria-modal={draft ? "true" : undefined}
            aria-label={draft ? "Редактор промо" : undefined}
          >
            {draft ? (
              <form onSubmit={saveDraft}>
                <div className="ps-section-head">
                  <div>
                    <span className="ps-eyebrow">{editingId ? "Редактирование" : "Новое промо"}</span>
                    <h2>{draft.title || "Без названия"}</h2>
                  </div>
                  <button className="ps-close" type="button" onClick={() => setDraft(null)} aria-label="Закрыть редактор">×</button>
                </div>

                <nav className="ps-editor-tabs" aria-label="Разделы промо">
                  <button type="button" aria-current={editorTab === "settings" ? "page" : undefined} onClick={() => setEditorTab("settings")}>Настройка</button>
                  <button type="button" aria-current={editorTab === "forecast" ? "page" : undefined} onClick={() => setEditorTab("forecast")}>Прогноз</button>
                  <button type="button" aria-current={editorTab === "results" ? "page" : undefined} onClick={() => setEditorTab("results")}>Результаты</button>
                  <button type="button" aria-current={editorTab === "preview" ? "page" : undefined} onClick={() => setEditorTab("preview")}>В X5 Рост</button>
                </nav>

                {editorTab === "settings" && <>
                <div className="ps-form-grid">
                  <label className="ps-field ps-field--wide">
                    <span>Название *</span>
                    <input value={draft.title} onChange={(event) => updateDraft("title", event.target.value)} placeholder="Например, Молочная неделя" />
                    {errors.title && <small>{errors.title}</small>}
                  </label>
                  <label className="ps-field ps-field--wide">
                    <span>ID промо *</span>
                    <input value={draft.promo_id} onChange={(event) => updateDraft("promo_id", event.target.value)} />
                    {errors.promo_id && <small>{errors.promo_id}</small>}
                  </label>
                  <label className="ps-field ps-field--wide">
                    <span>Описание *</span>
                    <textarea rows={3} value={draft.description} onChange={(event) => updateDraft("description", event.target.value)} placeholder="Что получает клиент и при каком поведении" />
                    {errors.description && <small>{errors.description}</small>}
                  </label>
                  <label className="ps-field">
                    <span>Продуктовая цель</span>
                    <select value={draft.objective} onChange={(event) => updateDraft("objective", event.target.value as Promo["objective"])}>
                      {PROMO_OBJECTIVES.map((item) => <option key={item} value={item}>{OBJECTIVE_LABELS[item]}</option>)}
                    </select>
                  </label>
                  <label className="ps-field">
                    <span>Категория</span>
                    <select value={draft.category} onChange={(event) => updateDraft("category", event.target.value)}>
                      {CATEGORIES.map((item) => <option key={item} value={item}>{CATEGORY_LABELS[item]}</option>)}
                    </select>
                  </label>
                  <label className="ps-field">
                    <span>Тип скидки</span>
                    <select value={draft.discount_type} onChange={(event) => updateDraft("discount_type", event.target.value as Promo["discount_type"])}>
                      <option value="percent">Процент, %</option>
                      <option value="fixed">Фиксированная, ₽</option>
                    </select>
                  </label>
                  <label className="ps-field">
                    <span>Размер скидки</span>
                    <input type="number" min="0" step="0.1" value={draft.discount_value} onChange={(event) => updateDraft("discount_value", Number(event.target.value))} />
                    {errors.discount_value && <small>{errors.discount_value}</small>}
                  </label>
                  <label className="ps-field">
                    <span>Влияние на маржу</span>
                    <input type="number" min="0" step="0.05" value={draft.margin_impact} onChange={(event) => updateDraft("margin_impact", Number(event.target.value))} />
                  </label>
                  <label className="ps-field">
                    <span>Статус</span>
                    <select value={draft.approval_status} onChange={(event) => updateDraft("approval_status", event.target.value as Promo["approval_status"])}>
                      {PROMO_STATUSES.map((item) => <option key={item} value={item}>{STATUS_LABELS[item]}</option>)}
                    </select>
                  </label>
                  <label className="ps-field ps-field--wide">
                    <span>Целевая метрика</span>
                    <select value={draft.target_metric} onChange={(event) => updateDraft("target_metric", event.target.value as Promo["target_metric"])}>
                      {TARGET_METRICS.map((item) => <option key={item} value={item}>{METRIC_LABELS[item]}</option>)}
                    </select>
                  </label>
                  <label className="ps-field ps-field--wide">
                    <span>Сегменты через запятую</span>
                    <input value={draft.eligibility_rules.segments.join(", ")} onChange={(event) => updateDraft("eligibility_rules", { segments: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="M1, M2 — пусто означает все сегменты" />
                  </label>
                </div>

                <fieldset className="ps-checks">
                  <legend>Shopping missions *</legend>
                  {SHOPPING_MISSIONS.map((item) => (
                    <label key={item}><input type="checkbox" checked={draft.shopping_missions.includes(item)} onChange={() => toggleArrayValue("shopping_missions", item)} /><span>{MISSION_LABELS[item]}</span></label>
                  ))}
                  {errors.shopping_missions && <small>{errors.shopping_missions}</small>}
                </fieldset>
                <fieldset className="ps-checks">
                  <legend>Каналы *</legend>
                  {PROMO_CHANNELS.map((item) => (
                    <label key={item}><input type="checkbox" checked={draft.channels.includes(item)} onChange={() => toggleArrayValue("channels", item)} /><span>{CHANNEL_LABELS[item]}</span></label>
                  ))}
                  {errors.channels && <small>{errors.channels}</small>}
                </fieldset>

                <section className="ps-preview">
                  <span>Как система прочитает промо</span>
                  <p><strong>{OBJECTIVE_LABELS[draft.objective]}</strong> в категории «{CATEGORY_LABELS[draft.category] ?? draft.category}» через {discountLabel(draft)}. Проверяем по метрике «{METRIC_LABELS[draft.target_metric]}».</p>
                </section>

                <div className="ps-editor-actions">
                  <button className="ps-button ps-button--ghost" type="button" onClick={() => setDraft(null)}>Отмена</button>
                  <button className="ps-button ps-button--primary" type="submit">Сохранить промо</button>
                </div>
                </>}
                {editorTab === "forecast" && <ForecastPanel promo={draft} />}
                {editorTab === "results" && <ResultsPanel promo={draft} />}
                {editorTab === "preview" && (
                  <PreviewPanel
                    promo={draft}
                    assignment={assignment?.promo_id === draft.promo_id ? assignment : undefined}
                    canPublish={Boolean(
                      editingId && promos.find((promo) => promo.promo_id === editingId)?.approval_status === "approved"
                    )}
                    onPublish={publishDraft}
                  />
                )}
              </form>
            ) : (
              <div className="ps-editor-empty">
                <span>＋</span>
                <h2>Соберите промо</h2>
                <p>Создайте новую механику или выберите существующую слева.</p>
                <button className="ps-button ps-button--primary" type="button" onClick={openNew}>Новое промо</button>
              </div>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
}
