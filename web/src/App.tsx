import { useState } from "react";
import { fixtureClient } from "./client";
import { Challenge } from "./screens/Challenge";
import { ProfileAvatar } from "./screens/ProfileAvatar";
import { Referral } from "./screens/Referral";

type Tab = "profile" | "challenge" | "referral";

const TABS: { id: Tab; label: string }[] = [
  { id: "profile", label: "Профиль" },
  { id: "challenge", label: "Челлендж" },
  { id: "referral", label: "Друзья" },
];

export function App() {
  const [tab, setTab] = useState<Tab>("profile");
  const profile = fixtureClient.getProfileView();
  const challenge = fixtureClient.getChallengeView();
  const referral = fixtureClient.getReferralView();

  return (
    <div className="app">
      <main className="app__body">
        {tab === "profile" && <ProfileAvatar view={profile} />}
        {tab === "challenge" && <Challenge view={challenge} />}
        {tab === "referral" && <Referral view={referral} />}
      </main>

      <nav className="app__tabbar" aria-label="Разделы">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className="app__tab"
            aria-current={tab === t.id ? "page" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
