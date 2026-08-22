import { rankMandis } from "./transport";
import type {
  ForecastRow,
  MandiMeta,
  Meta,
  PriceHistoryRow,
  RankedMandi,
} from "./types";

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const DAY_MS = 86_400_000;

function parseIsoDate(date: string): Date {
  if (!ISO_DATE_RE.test(date)) throw new Error(`Invalid ISO date: ${date}`);
  const parsed = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) throw new Error(`Invalid ISO date: ${date}`);
  return parsed;
}

export function addDaysIso(date: string, days: number): string {
  const parsed = parseIsoDate(date);
  parsed.setUTCDate(parsed.getUTCDate() + days);
  return parsed.toISOString().slice(0, 10);
}

export function daysBehind(asOfDate: string, canonicalAsOfDate: string): number {
  return Math.max(
    0,
    Math.round((parseIsoDate(canonicalAsOfDate).getTime() - parseIsoDate(asOfDate).getTime()) / DAY_MS)
  );
}

export function isStaleAsOf(asOfDate: string, canonicalAsOfDate: string): boolean {
  return daysBehind(asOfDate, canonicalAsOfDate) > 0;
}

export function haveUniformIntervalWidths(
  forecasts: ForecastRow[],
  tolerance = 0.01
): boolean {
  if (forecasts.length < 2) return false;
  const firstWidth = forecasts[0].upper_bound_inr_qtl - forecasts[0].lower_bound_inr_qtl;
  return forecasts.every(
    (row) =>
      Math.abs(row.upper_bound_inr_qtl - row.lower_bound_inr_qtl - firstWidth) <= tolerance
  );
}

export function filterForecastHistory(
  history: PriceHistoryRow[],
  marketId: number,
  asOfDate: string,
  historyDays = 90
): PriceHistoryRow[] {
  const firstDate = addDaysIso(asOfDate, -(historyDays - 1));
  return history.filter(
    (row) =>
      row.market_id === marketId &&
      row.date >= firstDate &&
      row.date <= asOfDate &&
      row.modal_price_inr_qtl !== null &&
      Number.isFinite(row.modal_price_inr_qtl)
  );
}

export interface RecommendationPolicyResult {
  rows: RankedMandi[];
  canonicalAsOfDate: string;
  eligibleAsOfCount: number;
  excludedStaleCount: number;
  excludedRadiusCount: number;
}

export function rankRecommendationCandidates(
  forecasts: ForecastRow[],
  mandis: MandiMeta[],
  farmerLatitude: number,
  farmerLongitude: number,
  meta: Meta,
  costPerKmPerQuintal: number,
  maxTransportRadiusKm = meta.ranking.max_transport_radius_km
): RecommendationPolicyResult {
  const canonicalAsOfDate = meta.candidate_policy.eligible_as_of_date || meta.as_of_date;
  const eligibleForecasts = forecasts.filter((row) => row.as_of_date === canonicalAsOfDate);
  const excludedStaleCount = forecasts.length - eligibleForecasts.length;
  const allRanked = rankMandis(eligibleForecasts, mandis, farmerLatitude, farmerLongitude, {
    ...meta.ranking,
    cost_per_km_per_quintal: costPerKmPerQuintal,
  });
  const withinRadius = allRanked.filter(
    (row) => row.road_distance_km <= maxTransportRadiusKm
  );
  const maxAlternatives = Math.max(1, Math.floor(meta.ranking.max_alternatives));
  // Re-rank after applying the radius policy so the public table's rank is a
  // contiguous 1..N list of eligible alternatives (rather than preserving
  // positions occupied by candidates that were filtered out).
  const rows = withinRadius.slice(0, maxAlternatives).map((row, index) => ({
    ...row,
    rank: index + 1,
    staleness_days: daysBehind(row.as_of_date, canonicalAsOfDate),
  }));

  return {
    rows,
    canonicalAsOfDate,
    eligibleAsOfCount: eligibleForecasts.length,
    excludedStaleCount,
    excludedRadiusCount: allRanked.length - withinRadius.length,
  };
}
