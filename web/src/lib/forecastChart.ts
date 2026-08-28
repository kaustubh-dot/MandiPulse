import type { ForecastRow, PriceHistoryRow } from "@/lib/types";

export interface ForecastHistoryPoint {
  date: string;
  price: number;
  imputed?: number;
}

export interface ForecastTablePoint {
  date: string;
  observed?: number;
  imputed?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
}

export interface ForecastEndpoint {
  date: string;
  forecast: number;
  lower: number;
  upper: number;
  confidenceLevel: number;
}

export interface ForecastChartModel {
  historyPoints: ForecastHistoryPoint[];
  tablePoints: ForecastTablePoint[];
  endpoint: ForecastEndpoint | null;
  yDomain: [number, number];
}

function finite(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function formatForecastDateTick(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(date);
}

export function formatForecastPriceTick(value: number): string {
  return Math.round(value).toLocaleString("en-US");
}

function paddedDomain(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum;
  const padding = spread > 0 ? spread * 0.08 : Math.max(Math.abs(minimum) * 0.05, 1);

  return [Math.max(0, minimum - padding), maximum + padding];
}

export function buildForecastChartModel(
  history: PriceHistoryRow[],
  forecast: ForecastRow | null,
  forecastDate: string | null
): ForecastChartModel {
  const sortedHistory = [...history]
    .filter((row) => finite(row.modal_price_inr_qtl))
    .sort((a, b) => a.date.localeCompare(b.date));

  const historyPoints: ForecastHistoryPoint[] = sortedHistory.map((row) => ({
    date: row.date,
    price: row.modal_price_inr_qtl as number,
    ...(row.is_imputed ? { imputed: row.modal_price_inr_qtl as number } : {}),
  }));

  const tablePoints: ForecastTablePoint[] = sortedHistory.map((row) => ({
    date: row.date,
    ...(row.is_imputed
      ? { imputed: row.modal_price_inr_qtl as number }
      : { observed: row.modal_price_inr_qtl as number }),
  }));

  const endpoint =
    forecast &&
    forecastDate &&
    finite(forecast.forecast_price_inr_qtl) &&
    finite(forecast.lower_bound_inr_qtl) &&
    finite(forecast.upper_bound_inr_qtl)
      ? {
          date: forecastDate,
          forecast: forecast.forecast_price_inr_qtl,
          lower: forecast.lower_bound_inr_qtl,
          upper: forecast.upper_bound_inr_qtl,
          confidenceLevel: forecast.confidence_level,
        }
      : null;

  if (endpoint) {
    tablePoints.push({
      date: endpoint.date,
      forecast: endpoint.forecast,
      lower: endpoint.lower,
      upper: endpoint.upper,
    });
  }

  const domainValues = historyPoints.map((point) => point.price);
  if (endpoint) {
    domainValues.push(endpoint.lower, endpoint.forecast, endpoint.upper);
  }

  return {
    historyPoints,
    tablePoints,
    endpoint,
    yDomain: paddedDomain(domainValues),
  };
}
