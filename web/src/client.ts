/**
 * Fixture-backed реализация контракта (research.md R1, SC-011).
 *
 * Клиент читает ТОЛЬКО заранее сгенерированные JSON из fixtures/out/ и валидирует
 * их zod-схемой контракта. Ни одного сетевого вызова — демо не зависит от сервера.
 * Контракты спроектированы так, что здесь позже можно подставить реальный бэкенд,
 * не трогая экраны.
 */
import challengeScreenJson from "../../fixtures/out/challenge-screen.json";
import profileScreenJson from "../../fixtures/out/profile-screen.json";
import referralScreenJson from "../../fixtures/out/referral-screen.json";
import {
  ChallengeScreenViewSchema,
  ProfileScreenViewSchema,
  ReferralScreenViewSchema,
  type ChallengeScreenView,
  type ProfileScreenView,
  type ReferralScreenView,
} from "./contract/types";

export interface GamingLayerClient {
  getProfileView(): ProfileScreenView;
  getChallengeView(): ChallengeScreenView;
  getReferralView(): ReferralScreenView;
}

export const fixtureClient: GamingLayerClient = {
  getProfileView() {
    return ProfileScreenViewSchema.parse(profileScreenJson);
  },
  getChallengeView() {
    return ChallengeScreenViewSchema.parse(challengeScreenJson);
  },
  getReferralView() {
    return ReferralScreenViewSchema.parse(referralScreenJson);
  },
};
