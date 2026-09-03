/**
 * T025 / SC-011 — fixture-backed клиент читает локальный JSON и он проходит
 * валидацию zod-схемой контракта. Никаких сетевых вызовов.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { fixtureClient } from "../src/client";
import { ProfileScreenViewSchema } from "../src/contract/types";

describe("fixtureClient.getProfileView", () => {
  it("возвращает объект, валидный по ProfileScreenViewSchema", () => {
    const view = fixtureClient.getProfileView();
    expect(() => ProfileScreenViewSchema.parse(view)).not.toThrow();
    expect(view.avatar.level).toBeGreaterThanOrEqual(0);
    expect(view.savings.progress_ratio).toBeGreaterThanOrEqual(0);
    expect(view.savings.progress_ratio).toBeLessThanOrEqual(1);
  });

  it("не выполняет сетевых запросов", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    fixtureClient.getProfileView();
    expect(fetchSpy).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});

describe("контракт: фикстура на диске соответствует схеме", () => {
  it("fixtures/out/profile-screen.json валиден", () => {
    const p = resolve(__dirname, "../../fixtures/out/profile-screen.json");
    const raw = JSON.parse(readFileSync(p, "utf-8"));
    expect(() => ProfileScreenViewSchema.parse(raw)).not.toThrow();
  });
});
