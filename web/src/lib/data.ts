"use client";

import type {
  Meta,
  MandiMeta,
  ForecastRow,
  PriceHistoryRow,
  RecommendationRow,
  BacktestSummary,
  HonestResult,
} from "./types";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export const loadMeta = () => fetchJson<Meta>("/data/meta.json");
export const loadMandis = () => fetchJson<MandiMeta[]>("/data/mandis.json");
export const loadForecasts = () => fetchJson<ForecastRow[]>("/data/forecasts.json");
export const loadPriceHistory = () => fetchJson<PriceHistoryRow[]>("/data/price_history.json");
export const loadRecommendations = () =>
  fetchJson<RecommendationRow[]>("/data/recommendations.json");
export const loadBacktest = () => fetchJson<BacktestSummary>("/data/backtest.json");
export const loadHonestResults = () => fetchJson<HonestResult[]>("/data/honest_results.json");
