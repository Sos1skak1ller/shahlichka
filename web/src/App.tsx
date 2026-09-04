import { useEffect, useState, type ReactElement } from "react";
import {
  fixtureClient,
  leftProfileView,
  rightProfileView,
} from "./client";
import type {
  ChallengeScreenView,
  ProfileScreenView,
  ReferralScreenView,
} from "./contract/types";
import { Challenge } from "./screens/Challenge";
import { ProfileAvatar } from "./screens/ProfileAvatar";
import { Referral } from "./screens/Referral";
import { PromoStudio } from "./promo/PromoStudio";
import {
  ASSIGNMENT_STORAGE_KEY,
  CATEGORY_LABELS,
  PROMO_STORAGE_KEY,
  PromoPoolSchema,
  PublishedAssignmentSchema,
  type Promo,
  type PublishedAssignment,
} from "./promo/types";

type Tab = "profile" | "challenge" | "referral";

const IconSprout = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 21v-8" />
    <path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z" />
    <path d="M12 15c0-3-2.5-5-6-5 0 3 2.5 5 6 5z" />
  </svg>
);
const IconFlag = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 21V4" />
    <path d="M6 4h11l-2.5 4L17 12H6" />
  </svg>
);
const IconGift = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="9" width="16" height="11" rx="1.6" />
    <path d="M2.5 6.5h19V9h-19z" />
    <path d="M12 6.5V20" />
    <path d="M12 6.5S10.5 3 8.6 3.6 8 6.5 12 6.5z" />
    <path d="M12 6.5s1.5-3.5 3.4-2.9S16 6.5 12 6.5z" />
  </svg>
);

const TABS: { id: Tab; label: string; icon: () => ReactElement }[] = [
  { id: "profile", label: "Прогресс", icon: IconSprout },
  { id: "challenge", label: "Челлендж", icon: IconFlag },
  { id: "referral", label: "Друзья", icon: IconGift },
];

interface PhoneProps {
  profile: ProfileScreenView;
  challenge?: ChallengeScreenView;
  referral?: ReferralScreenView;
  interactive?: boolean;
  variant: "main" | "side";
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

function Phone({ profile, challenge, referral, interactive = false, variant, publishedPromo }: PhoneProps) {
  const [tab, setTab] = useState<Tab>("profile");
  const activeTab: Tab = interactive ? tab : "profile";
  const hi = (profile.display_name ?? "друг").split(/[\s·]+/)[0];

  return (
    <div className={`device device--${variant}`}>
      <div className="device__scroll">
        <header className="topbar">
          <div>
            <div className="topbar__eyebrow">Х5 Клуб · Рост</div>
            <div className="topbar__hi">Привет, {hi}</div>
          </div>
          <div className="topbar__ava" aria-hidden>
            {hi.slice(0, 1).toUpperCase()}
          </div>
        </header>

        <main>
          {activeTab === "profile" && (
            <>
              <ProfileAvatar view={profile} />
              {interactive && publishedPromo && <PublishedPromoCard promo={publishedPromo} />}
            </>
          )}
          {interactive && activeTab === "challenge" && challenge && (
            <Challenge view={challenge} />
          )}
          {interactive && activeTab === "referral" && referral && (
            <Referral view={referral} />
          )}
        </main>
      </div>

      <nav className="tabbar" aria-label="Разделы">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              type="button"
              className="tab"
              disabled={!interactive}
              aria-current={activeTab === t.id ? "page" : undefined}
              onClick={interactive ? () => setTab(t.id) : undefined}
            >
              <Icon />
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

  const profile: ProfileScreenView = published
    ? {
        ...fixtureProfile,
        user_id: published.assignment.client_id,
        display_name: published.assignment.client_name,
      }
    : fixtureProfile;

  return (
    <div className="page">
      <div className="gallery">
        <Phone profile={leftProfileView} variant="side" />
        <Phone
          profile={profile}
          challenge={challenge}
          referral={referral}
          publishedPromo={published?.promo}
          interactive
          variant="main"
        />
        <Phone profile={rightProfileView} variant="side" />
      </div>
    </div>
  );
}

export function App() {
  if (window.location.pathname.startsWith("/promo-studio")) {
    return <PromoStudio />;
  }
  return <GrowthApp />;
}
