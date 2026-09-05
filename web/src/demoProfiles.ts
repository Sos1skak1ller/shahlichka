import type { ProfileScreenView } from "./contract/types";
import { leftProfileView, rightProfileView } from "./client";

interface DemoProfilePreset {
  userId: string;
  name: string;
  stage: 1 | 2 | 3 | 4 | 5;
  state?: "progressing" | "max_level";
  saved: number;
  currentThreshold: number;
  nextThreshold: number | null;
  progressRatio: number;
  streak: number;
  unlocked: string[];
  source?: ProfileScreenView;
}

export const DEMO_PROFILE_PRESETS: DemoProfilePreset[] = [
  {
    userId: "demo-nika",
    name: "Ника",
    stage: 1,
    saved: 240,
    currentThreshold: 0,
    nextThreshold: 500,
    progressRatio: 0.48,
    streak: 1,
    unlocked: ["starter_skin"],
    source: rightProfileView,
  },
  {
    userId: "demo-marina",
    name: "Марина",
    stage: 2,
    saved: 800,
    currentThreshold: 500,
    nextThreshold: 1500,
    progressRatio: 0.3,
    streak: 2,
    unlocked: ["starter_skin", "bronze_badge"],
    source: leftProfileView,
  },
  {
    userId: "demo-kirill",
    name: "Кирилл",
    stage: 3,
    saved: 2140,
    currentThreshold: 1500,
    nextThreshold: 3500,
    progressRatio: 0.32,
    streak: 4,
    unlocked: ["starter_skin", "bronze_badge", "silver_badge"],
  },
  {
    userId: "demo-sofia",
    name: "София",
    stage: 4,
    saved: 4820,
    currentThreshold: 3500,
    nextThreshold: 7000,
    progressRatio: 0.38,
    streak: 6,
    unlocked: ["starter_skin", "bronze_badge", "silver_badge", "gold_badge"],
  },
  {
    userId: "demo-maxim",
    name: "Максим",
    stage: 5,
    state: "max_level",
    saved: 8100,
    currentThreshold: 7000,
    nextThreshold: null,
    progressRatio: 1,
    streak: 9,
    unlocked: ["starter_skin", "bronze_badge", "silver_badge", "gold_badge", "prestige_frame"],
  },
];
