import { useEffect, useRef, useState } from "react";
import { fixtureClient } from "./client";
import { DEMO_PROFILE_PRESETS } from "./demoProfiles";
import type {
  ChallengeScreenView,
  ProfileScreenView,
  ReferralScreenView,
} from "./contract/types";
import { Challenge } from "./screens/Challenge";
import { CategoryMap } from "./screens/CategoryMap";
import { ProfileAvatar } from "./screens/ProfileAvatar";
import { Referral } from "./screens/Referral";
import { Icon } from "./components/Icon";
import { X5Brand } from "./components/X5Brand";
import { mascotName } from "./components/Mascot";
import { PromoStudio } from "./promo/PromoStudio";
import { LandingPage } from "./landing/LandingPage";
import {
  ASSIGNMENT_STORAGE_KEY,
  CATEGORY_LABELS,
  PROMO_STORAGE_KEY,
  PromoPoolSchema,
  PublishedAssignmentSchema,
  type Promo,
  type PublishedAssignment,
} from "./promo/types";

type Tab = "profile" | "challenge" | "categories" | "referral";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "profile", label: "Главная", icon: "progress" },
  { id: "challenge", label: "Цель", icon: "target" },
  { id: "categories", label: "Категории", icon: "cart" },
  { id: "referral", label: "Друзья", icon: "friends" },
];

interface PhoneProps {
  profile: ProfileScreenView;
  challenge?: ChallengeScreenView;
  referral?: ReferralScreenView;
  interactive?: boolean;
  publishedPromo?: Promo;
}

function PublishedPromoCard({ promo }: { promo: Promo }) {
  const reward = promo.discount_type === "percent"
    ? `${promo.discount_value}%`
    : `${promo.discount_value} ₽`;
  return (
    <section className="growth-promo" aria-label="Опубликованное персональное промо">
      <div className="growth-promo__head">
        <span>Персональная цель</span>
        <b>Новая</b>
      </div>
      <h3>До следующей награды — один шаг</h3>
      <p>Совершите ещё одну покупку в категории «{CATEGORY_LABELS[promo.category] ?? promo.category}».</p>
      <div className="growth-promo__progress"><i /><span>1 из 2</span></div>
      <div className="growth-promo__reward">
        <span>Откроется</span>
        <strong>{reward} на следующую покупку</strong>
      </div>
    </section>
  );
}

interface PublishedContext {
  promo: Promo;
  assignment: PublishedAssignment;
}

function buildDemoProfiles(base: ProfileScreenView): ProfileScreenView[] {
  return DEMO_PROFILE_PRESETS.map((preset) => {
    const source = preset.source ?? base;
    const isCurrentProfile = preset.stage === 3;
    return {
      ...source,
      user_id: isCurrentProfile ? base.user_id : preset.userId,
      display_name: isCurrentProfile ? base.display_name : preset.name,
      avatar: {
        ...source.avatar,
        level: preset.stage - 1,
        visual_stage: preset.stage,
        state: preset.state ?? "progressing",
        unlocked_customizations: preset.unlocked,
      },
      savings: {
        total_saved_amount: preset.saved,
        current_threshold: preset.currentThreshold,
        next_threshold: preset.nextThreshold,
        progress_ratio: preset.progressRatio,
      },
      streak: {
        ...source.streak,
        streak_count: preset.streak,
      },
    };
  });
}

function readPublishedContext(): PublishedContext | undefined {
  try {
    const savedAssignment = window.localStorage.getItem(ASSIGNMENT_STORAGE_KEY);
    if (!savedAssignment) return undefined;
    const assignment = PublishedAssignmentSchema.parse(JSON.parse(savedAssignment));
    const saved = window.localStorage.getItem(PROMO_STORAGE_KEY);
    if (!saved) return undefined;
    const promo = PromoPoolSchema.parse(JSON.parse(saved)).promos.find(
      (promo) =>
        promo.promo_id === assignment.promo_id &&
        promo.approval_status === "published",
    );
    if (!promo) return undefined;
    return { promo, assignment };
  } catch {
    return undefined;
  }
}

function Phone({ profile, challenge, referral, interactive = false, publishedPromo }: PhoneProps) {
  const [tab, setTab] = useState<Tab>("profile");
  const activeTab: Tab = interactive ? tab : "profile";
  const hi = (profile.display_name ?? "друг").split(/[\s·]+/)[0];

  return (
    <div className="device device--main">
      <div className="device__scroll">
        <header className="topbar">
          <div>
            <div className="topbar__eyebrow"><X5Brand className="client-brand" compact /><span>демо</span></div>
            <div className="topbar__hi">Привет, {hi}</div>
          </div>
          <div className="topbar__ava" aria-hidden>
            {hi.slice(0, 1).toUpperCase()}
          </div>
        </header>

        <main>
          {activeTab === "profile" && (
            <>
              <ProfileAvatar
                view={profile}
                challenge={challenge}
                onOpenGoal={() => setTab("challenge")}
                onOpenCategories={() => setTab("categories")}
              />
              {interactive && publishedPromo && <PublishedPromoCard promo={publishedPromo} />}
            </>
          )}
          {interactive && activeTab === "challenge" && challenge && (
            <Challenge view={challenge} />
          )}
          {interactive && activeTab === "categories" && (
            <CategoryMap view={profile} />
          )}
          {interactive && activeTab === "referral" && referral && (
            <Referral view={referral} />
          )}
        </main>
      </div>

      <nav className="tabbar" aria-label="Разделы">
        {TABS.map((t) => {
          return (
            <button
              key={t.id}
              type="button"
              className="tab"
              disabled={!interactive}
              aria-current={activeTab === t.id ? "page" : undefined}
              onClick={interactive ? () => setTab(t.id) : undefined}
            >
              <Icon name={t.icon} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}

function GrowthApp() {
  const fixtureProfile = fixtureClient.getProfileView();
  const challenge = fixtureClient.getChallengeView();
  const referral = fixtureClient.getReferralView();
  const [published, setPublished] = useState<PublishedContext | undefined>(
    readPublishedContext,
  );
  const [profileIndex, setProfileIndex] = useState(() => {
    const account = new URLSearchParams(window.location.search).get("account");
    const index = DEMO_PROFILE_PRESETS.findIndex((preset) => preset.userId === account);
    return index >= 0 ? index : 2;
  });
  const swipeStart = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const refreshPublishedContext = () => setPublished(readPublishedContext());
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") refreshPublishedContext();
    };
    refreshPublishedContext();
    window.addEventListener("storage", refreshPublishedContext);
    window.addEventListener("focus", refreshPublishedContext);
    window.addEventListener("pageshow", refreshPublishedContext);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      window.removeEventListener("storage", refreshPublishedContext);
      window.removeEventListener("focus", refreshPublishedContext);
      window.removeEventListener("pageshow", refreshPublishedContext);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, []);

  const baseProfile: ProfileScreenView = published
    ? {
        ...fixtureProfile,
        user_id: published.assignment.client_id,
        display_name: published.assignment.client_name,
      }
    : fixtureProfile;
  const profiles = buildDemoProfiles(baseProfile);
  const profile = profiles[profileIndex];

  const selectProfile = (nextIndex: number) => {
    setProfileIndex((nextIndex + profiles.length) % profiles.length);
  };

  const changeProfile = (direction: -1 | 1) => {
    setProfileIndex((current) => (current + direction + profiles.length) % profiles.length);
  };

  const finishSwipe = (clientX: number, clientY: number) => {
    if (swipeStart.current === null) return;
    const distance = clientX - swipeStart.current.x;
    const verticalDistance = clientY - swipeStart.current.y;
    swipeStart.current = null;
    if (Math.abs(distance) < 42 || Math.abs(distance) <= Math.abs(verticalDistance)) return;
    changeProfile(distance < 0 ? 1 : -1);
  };

  return (
    <div className="page">
      <div className="demo-shell">
        <aside className="demo-context" aria-label="Контекст демонстрации">
          <X5Brand className="demo-brand" />
          <a href="/landing" className="demo-context__back"><Icon name="arrow-left" /> На лендинг</a>
          <span className="demo-context__eyebrow">Клиентский сценарий</span>
          <h1>Экономия становится видимым прогрессом</h1>
          <p>Покупатель видит одну следующую цель, развитие аватара и карту привычных категорий.</p>
          <ul>
            <li><Icon name="receipt" /><span>Прогресс только от проверенных чеков</span></li>
            <li><Icon name="target" /><span>Одна достижимая цель на неделю</span></li>
            <li><Icon name="info" /><span>Все данные в сценарии синтетические</span></li>
          </ul>
          <a href="/promo-studio" className="demo-context__studio">Открыть Promo Studio <span aria-hidden="true">↗</span></a>
        </aside>
        <section className="phone-carousel" aria-label="Демо-аккаунты">
          <div className="account-switcher">
            <button type="button" onClick={() => changeProfile(-1)} aria-label="Предыдущий аккаунт">
              <span aria-hidden="true">←</span>
            </button>
            <div className="account-switcher__current" aria-live="polite">
              <span>Аккаунт {profileIndex + 1} из {profiles.length}</span>
              <strong>{profile.display_name} · {mascotName(profile.avatar.visual_stage)}</strong>
            </div>
            <button type="button" onClick={() => changeProfile(1)} aria-label="Следующий аккаунт">
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <div
            className="phone-carousel__viewport"
            tabIndex={0}
            aria-label="Телефон с аккаунтом; листайте влево или вправо"
            onKeyDown={(event) => {
              if (event.key === "ArrowLeft" || event.key === "ArrowRight") event.preventDefault();
              if (event.key === "ArrowLeft") changeProfile(-1);
              if (event.key === "ArrowRight") changeProfile(1);
            }}
            onTouchStart={(event) => {
              const touch = event.changedTouches[0];
              swipeStart.current = touch ? { x: touch.clientX, y: touch.clientY ?? 0 } : null;
            }}
            onTouchCancel={() => { swipeStart.current = null; }}
            onTouchEnd={(event) => finishSwipe(event.changedTouches[0]?.clientX ?? 0, event.changedTouches[0]?.clientY ?? 0)}
          >
            <Phone
              key={profile.user_id}
              profile={profile}
              challenge={{ ...challenge, user_id: profile.user_id }}
              referral={{ ...referral, user_id: profile.user_id }}
              publishedPromo={profileIndex === 2 ? published?.promo : undefined}
              interactive
            />
          </div>

          <div className="account-dots" aria-label="Выбор демо-аккаунта">
            {profiles.map((item, index) => (
              <button
                key={item.user_id}
                type="button"
                aria-label={`${item.display_name}, этап ${item.avatar.visual_stage}`}
                aria-current={index === profileIndex ? "true" : undefined}
                onClick={() => selectProfile(index)}
              />
            ))}
          </div>
          <p className="phone-carousel__hint">Листайте аккаунты — от почки до апельсинки</p>
        </section>
      </div>
    </div>
  );
}

export function App() {
  if (window.location.pathname.startsWith("/landing")) {
    return <LandingPage />;
  }
  if (window.location.pathname.startsWith("/promo-studio")) {
    return <PromoStudio />;
  }
  return <GrowthApp />;
}
