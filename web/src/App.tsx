import { useState, type ReactElement } from "react";
import { fixtureClient } from "./client";
import { Challenge } from "./screens/Challenge";
import { ProfileAvatar } from "./screens/ProfileAvatar";
import { Referral } from "./screens/Referral";

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

export function App() {
  const [tab, setTab] = useState<Tab>("profile");
  const profile = fixtureClient.getProfileView();
  const challenge = fixtureClient.getChallengeView();
  const referral = fixtureClient.getReferralView();

  const hi = (profile.display_name ?? "друг").split(/[\s·]+/)[0];

  return (
    <div className="page">
      <div className="device">
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
            {tab === "profile" && <ProfileAvatar view={profile} />}
            {tab === "challenge" && <Challenge view={challenge} />}
            {tab === "referral" && <Referral view={referral} />}
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
                aria-current={tab === t.id ? "page" : undefined}
                onClick={() => setTab(t.id)}
              >
                <Icon />
                <span>{t.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
