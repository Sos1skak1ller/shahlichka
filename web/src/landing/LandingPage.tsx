import { useEffect, useRef, useState } from "react";
import { Icon } from "../components/Icon";
import { X5Brand } from "../components/X5Brand";
import { mascotAsset, mascotName } from "../components/Mascot";
import { DEMO_PROFILE_PRESETS } from "../demoProfiles";
import "./landing.css";

const PRODUCT_STEPS = [
  {
    icon: "receipt",
    title: "Покупка подтверждена",
    description: "Чек проходит проверку на повторы и подозрительные события.",
    label: "Новый чек",
    value: "+320 ₽ экономии",
  },
  {
    icon: "progress",
    title: "Экономия стала прогрессом",
    description: "Обновляются уровень аватара и недельный стрик.",
    label: "Прогресс уровня",
    value: "5 форм аватара",
  },
  {
    icon: "challenge",
    title: "Подобрана личная цель",
    description: "Один достижимый челлендж из привычных категорий клиента.",
    label: "Челлендж недели",
    value: "2 из 3",
  },
  {
    icon: "gift",
    title: "Награда прошла лимит",
    description: "Стоимость проверена относительно ожидаемой инкрементальной маржи.",
    label: "Экономический порог",
    value: "≤ 35%",
  },
  {
    icon: "analytics",
    title: "Команда видит результат",
    description: "Прогноз, A/B-контур и решение о масштабировании собраны вместе.",
    label: "Контур измерения",
    value: "Test / Control",
  },
] as const;

const TRUST_ITEMS = [
  {
    icon: "target",
    title: "Объяснимый подбор",
    text: "Цель выбирается из ограниченного пула шаблонов по истории покупок и понятным признакам.",
  },
  {
    icon: "warning",
    title: "Антифрод до награды",
    text: "Чеки и рефералы получают прозрачный статус pass, review или block до начисления.",
  },
  {
    icon: "wallet",
    title: "Экономика до запуска",
    text: "Бюджет и отношение награды к ожидаемой марже проверяются до публикации промо.",
  },
  {
    icon: "info",
    title: "Честное демо",
    text: "Профили, прогнозы и результаты синтетические. В прототипе нет реальных персональных данных.",
  },
] as const;


const EXPERIENCES = [
  { icon: "progress", title: "Экономия, которую видно", text: "Подтверждённая экономия развивает аватара. Пять форм — пять этапов вашей истории.", detail: "Прогресс" },
  { icon: "target", title: "Одна цель на неделю", text: "Понятное действие из привычной корзины. Срок и условия награды известны заранее.", detail: "Персональная цель" },
  { icon: "cart", title: "Ваша карта покупок", text: "Привычные категории складываются в личную карту. Без дополнительной денежной награды.", detail: "Категории · UI-прототип" },
  { icon: "friends", title: "Вместе — интереснее", text: "Пригласите друга. Награда появится только после его подтверждённой покупки.", detail: "Друзья" },
];

function Brand() {
  return <X5Brand className="landing-brand" />;
}

function Arrow() {
  return <span className="landing-button__arrow" aria-hidden="true">↗</span>;
}

export function LandingPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [accountIndex, setAccountIndex] = useState(2);
  const swipe = useRef<{ x: number; y: number } | null>(null);
  const menuRef = useRef<HTMLDetailsElement>(null);
  const selectedStep = PRODUCT_STEPS[activeStep];
  const account = DEMO_PROFILE_PRESETS[accountIndex];
  const changeAccount = (delta: number) => setAccountIndex((index) =>
    (index + delta + DEMO_PROFILE_PRESETS.length) % DEMO_PROFILE_PRESETS.length);
  const money = (value: number) => new Intl.NumberFormat("ru-RU").format(value) + " ₽";

  useEffect(() => {
    const previousTitle = document.title;
    const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    const previousDescription = description?.content;
    document.title = "X5 Клуб · Рост — экономия, которая становится прогрессом";
    if (description) description.content = "Концепция X5 Клуба: подтверждённая экономия, пять форм аватара и одна персональная цель на неделю.";
    return () => {
      document.title = previousTitle;
      if (description && previousDescription !== undefined) description.content = previousDescription;
    };
  }, []);

  return (
    <div className="landing-page">
      <a className="landing-skip" href="#product">К содержанию</a>
      <header className="landing-header">
        <Brand />
        <nav className="landing-nav" aria-label="Основная навигация">
          <a href="#product">О продукте</a><a href="#avatars">Аватары</a>
          <a href="#how-it-works">Как работает</a><a href="#team">Для команды</a>
        </nav>
        <div className="landing-header__actions">
          <a className="landing-button landing-button--primary" href="/">Демо клиента <Arrow /></a>
          <details className="landing-menu" ref={menuRef} onKeyDown={(event) => {
            if (event.key === "Escape" && menuRef.current) {
              menuRef.current.open = false;
              menuRef.current.querySelector("summary")?.focus();
            }
          }}>
            <summary aria-label="Открыть меню"><span /><span /></summary>
            <nav aria-label="Мобильная навигация" onClick={() => { if (menuRef.current) menuRef.current.open = false; }}>
              <a href="#product">О продукте</a><a href="#avatars">Аватары</a>
              <a href="#how-it-works">Как работает</a><a href="#team">Для команды</a>
              <a href="#pilot">Условия пилота</a><a href="/promo-studio">Promo Studio</a>
            </nav>
          </details>
        </div>
      </header>
      <main>
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero__copy">
            <span className="landing-eyebrow">Повседневные покупки. Личная история.</span>
            <h1 id="landing-title">Экономия, которая растёт вместе с вами</h1>
            <p>Подтверждённая экономия развивает аватара. Привычные покупки открывают новые категории и цели.</p>
            <a className="landing-button landing-button--primary landing-button--large" href="/">Открыть демо клиента <Arrow /></a>
          </div>
          <div className="landing-hero__visual">
            <span className="landing-hero__caption">От первого листика<br />до большого результата</span>
            <img className="landing-hero__avatar" src={mascotAsset(2)} alt="Листик — вторая форма аватара Рост" loading="eager" width="1024" height="1536" />
            <a className="landing-hero__next" href="#avatars">
              <img src={mascotAsset(5)} alt="" width="1024" height="1536" />
              <span>Впереди —<br /><strong>новая форма</strong></span><span aria-hidden="true">↗</span>
            </a>
          </div>
          <div className="landing-hero__foot">
            <span><Icon name="receipt" /> Прогресс только от подтверждённой экономии</span>
            <span>Концепция · синтетические данные</span>
          </div>
        </section>

        <section className="landing-section landing-experience" id="product" aria-labelledby="experience-title">
          <div className="landing-section-heading landing-section-heading--split">
            <h2 id="experience-title">Привычные покупки.<br />Больше смысла.</h2>
            <p>Не игра ради кликов. Понятный результат того, что вы и так делаете каждый день.</p>
          </div>
          <div className="landing-feature-grid">
            {EXPERIENCES.map((item, index) => <article className="landing-feature-card" key={item.title}>
              <div className="landing-feature-card__top"><Icon name={item.icon} /><span>0{index + 1}</span></div>
              <h3>{item.title}</h3><p>{item.text}</p><span className="landing-card-kicker">{item.detail}</span>
            </article>)}
          </div>
        </section>

        <section className="landing-evolution landing-section" id="avatars" aria-labelledby="avatar-title">
          <div className="landing-section-heading landing-section-heading--split">
            <div><span className="landing-eyebrow">Один персонаж. Пять этапов.</span><h2 id="avatar-title">Растёт экономия.<br />Меняется герой.</h2></div>
            <p>От почки до апельсинки. Переключайте демоаккаунты и знакомьтесь с каждой формой.</p>
          </div>
          <div className="landing-evolution__layout">
            <div className="landing-stages" aria-label="Выбор этапа аватара">
              {DEMO_PROFILE_PRESETS.map((preset, index) => <button type="button" key={preset.userId}
                aria-label={preset.name + ", " + mascotName(preset.stage) + ", этап " + preset.stage}
                aria-pressed={index === accountIndex} onClick={() => setAccountIndex(index)}>
                <img src={mascotAsset(preset.stage)} alt="" width="1024" height="1536" loading="lazy" />
                <span><small>Этап {preset.stage}</small><strong>{mascotName(preset.stage)}</strong></span>
                <span className="landing-stages__threshold">{money(preset.currentThreshold)}<span aria-hidden="true"> ↗</span></span>
              </button>)}
              <p className="landing-data-note">Демонстрационные пороги. Пропуск недели не отнимает накопленный прогресс.</p>
            </div>
            <div className="landing-account-carousel" role="region" aria-roledescription="карусель" aria-label="Демоаккаунты" tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
                  event.preventDefault(); changeAccount(event.key === "ArrowRight" ? 1 : -1);
                }
              }}
              onTouchStart={(event) => { swipe.current = { x: event.touches[0].clientX, y: event.touches[0].clientY }; }}
              onTouchCancel={() => { swipe.current = null; }}
              onTouchEnd={(event) => {
                if (!swipe.current) return;
                const dx = event.changedTouches[0].clientX - swipe.current.x;
                const dy = event.changedTouches[0].clientY - swipe.current.y;
                if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) changeAccount(dx < 0 ? 1 : -1);
                swipe.current = null;
              }}>
              <div className="landing-phone" aria-live="polite" aria-atomic="true">
                <div className="landing-phone__top"><span>Рост</span><small>Демо · {accountIndex + 1} из 5</small></div>
                <h3>Привет, {account.name}</h3>
                <img key={account.stage} className="landing-phone__avatar" src={mascotAsset(account.stage)} alt={mascotName(account.stage) + ", этап " + account.stage + " из 5"} width="1024" height="1536" loading="lazy" />
                <div className="landing-phone__stage"><strong>{mascotName(account.stage)}</strong><span>Этап {account.stage}</span></div>
                <div className="landing-phone__savings"><span>Накопленная экономия</span><strong>{money(account.saved)}</strong>
                  <progress max={100} value={Math.round(account.progressRatio * 100)} aria-label="Прогресс до следующей формы" />
                  <small>{account.nextThreshold === null ? "Максимальная форма открыта" : "Ещё " + money(account.nextThreshold - account.saved) + " до новой формы"}</small>
                </div>
                <div className="landing-phone__streak"><Icon name="sparkles" /><span>Недель подряд с покупками: {account.streak}</span></div>
                <a className="landing-button landing-button--primary" href={"/?account=" + account.userId}>Открыть аккаунт <Arrow /></a>
              </div>
              <div className="landing-carousel-controls">
                <button type="button" onClick={() => changeAccount(-1)} aria-label="Предыдущий аккаунт">←</button>
                <span>{String(accountIndex + 1).padStart(2, "0")} / 05</span>
                <button type="button" onClick={() => changeAccount(1)} aria-label="Следующий аккаунт">→</button>
              </div>
              <p className="landing-data-note">Листайте стрелками или свайпом. Это разные демопрофили, не рост за клики.</p>
            </div>
          </div>
        </section>

        <section className="landing-loop landing-section" id="how-it-works" aria-labelledby="loop-title">
          <div className="landing-section-heading landing-section-heading--split">
            <h2 id="loop-title">За ростом —<br />реальная покупка.</h2>
            <p>От подтверждённого чека до следующего действия. Награда проходит проверку до начисления.</p>
          </div>
          <div className="landing-loop__layout">
            <ol className="landing-loop__steps" aria-label="Этапы продуктового цикла">
              {PRODUCT_STEPS.map((step, index) => <li key={step.title}>
                <button type="button" aria-pressed={activeStep === index} onClick={() => setActiveStep(index)}>
                  <span className="landing-loop__number">0{index + 1}</span>
                  <span><strong>{step.title}</strong><small>{step.description}</small></span>
                  <span aria-hidden="true">↗</span>
                </button>
              </li>)}
            </ol>
            <div className="landing-loop__preview" aria-live="polite">
              <span className="landing-card-kicker">Шаг {activeStep + 1} из {PRODUCT_STEPS.length}</span>
              <Icon name={selectedStep.icon} />
              <strong>{selectedStep.value}</strong><span>{selectedStep.label}</span>
              <p>{selectedStep.description}</p>
              <small>Иллюстрация механики на синтетических данных</small>
            </div>
          </div>
        </section>

        <section className="landing-studio" id="team" aria-labelledby="studio-title">
          <div className="landing-studio__inner">
            <div className="landing-studio__copy">
              <span className="landing-eyebrow">Для продуктовой команды · Promo Studio</span>
              <h2 id="studio-title">Понятно клиенту.<br />Управляемо командой.</h2>
              <p>Кому показать промо, почему оно подходит и сколько может стоить — в одном кабинете.</p>
              <a className="landing-button landing-button--inverse landing-button--large" href="/promo-studio">Открыть Promo Studio <Arrow /></a>
              <a className="landing-text-link" href="#pilot">Посмотреть условия пилота ↗</a>
            </div>
            <div className="landing-studio__workflow">
              <span className="landing-card-kicker">Контур решения</span>
              {[
                ["01", "Подобрать", "Сегмент, категория и объяснение выбора"],
                ["02", "Проверить", "Бюджет, ожидаемая маржа и антифрод"],
                ["03", "Показать", "Публикация промо в клиентский демопрофиль"],
                ["04", "Измерить", "Синтетическая симуляция, затем реальный A/B-пилот"],
              ].map(([number, title, text]) => <div key={number}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div><span aria-hidden="true">↗</span></div>)}
              <p className="landing-studio__boundary">Не предлагаем более дорогой товар под видом экономии.</p>
            </div>
          </div>
        </section>

        <section className="landing-targets" id="pilot" aria-labelledby="targets-title">
          <div className="landing-targets__heading">
            <span className="landing-section-index">Условия пилота</span>
            <h2 id="targets-title">Цели видны. Ограничения тоже.</h2>
          </div>
          <div className="landing-targets__grid">
            <article>
              <span>North Star</span>
              <strong>+5 п.п.</strong>
              <p>покупки в ≥ 3 из 4 недель, к контрольной группе</p>
            </article>
            <article>
              <span>Средний чек</span>
              <strong>≥ −2%</strong>
              <p>допустимая динамика среднего чека к контролю</p>
            </article>
            <article>
              <span>Экономика</span>
              <strong>≤ 35%</strong>
              <p>награды к инкрементальной марже</p>
            </article>
            <article>
              <span>Антифрод</span>
              <strong>≤ 3%</strong>
              <p>бюджета наград может уйти во фрод</p>
            </article>
          </div>
          <div className="landing-drivers" aria-label="Драйверы продуктовой гипотезы">
            <strong>Что двигаем</strong>
            <span>Категорийная широта</span>
            <span>Новая категория</span>
            <span>Покупка категории в срок</span>
            <span>Позиций в чеке</span>
          </div>
          <p className="landing-targets__note">
            <Icon name="info" />
            Целевые условия пилота — не фактические показатели X5. Рабочий сегмент M2 — регулярные, но неполные покупатели. Частота, маржа и удержание не должны падать.
          </p>
        </section>


        <section className="landing-trust landing-section" aria-labelledby="trust-title">
          <div className="landing-section-heading"><h2 id="trust-title">Доверие — часть механики.</h2></div>
          <div className="landing-trust__grid">
            {TRUST_ITEMS.map((item) => <article key={item.title}><Icon name={item.icon} /><h3>{item.title}</h3><p>{item.text}</p></article>)}
          </div>
          <p className="landing-data-note">Карта категорий — UI-прототип. Расчёт категорийных интервалов и детектор обрыва привычки не представлены как готовый расчётный контур.</p>
        </section>
        <section className="landing-final-cta" aria-labelledby="final-cta-title">
          <div><span className="landing-eyebrow">X5 Клуб · Рост</span><h2 id="final-cta-title">Ваша следующая<br />история начинается здесь.</h2></div>
          <div className="landing-final-cta__actions">
            <a className="landing-button landing-button--primary landing-button--large" href="/">Я покупатель <Arrow /></a>
            <a className="landing-text-link" href="/promo-studio">Я в продуктовой команде ↗</a>
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <Brand />
        <nav aria-label="Навигация в подвале"><a href="#product">Продукт</a><a href="#pilot">Пилот</a><a href="/">Демо клиента</a><a href="/promo-studio">Promo Studio</a></nav>
        <p>Проектная концепция. Только синтетические данные, без подключения к системам X5. Не является официально запущенным продуктом или фактическими результатами X5.</p>
      </footer>
    </div>
  );
}
