"use client";

import { useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/DataState";
import ForecastChart from "@/components/ForecastChart";
import HonestResultsTable from "@/components/HonestResultsTable";
import SampleBanner from "@/components/SampleBanner";
import {
  loadForecasts,
  loadHonestResults,
  loadMandis,
  loadMeta,
  loadPriceHistory,
} from "@/lib/data";
import { addDaysIso, daysBehind, filterForecastHistory } from "@/lib/policy";
import type {
  ForecastRow,
  HonestResult,
  MandiMeta,
  Meta,
  PriceHistoryRow,
} from "@/lib/types";
import { useAsyncData } from "@/lib/useAsyncData";

const HISTORY_DAYS = 90;

interface ForecastBundle {
  meta: Meta;
  mandis: MandiMeta[];
  forecasts: ForecastRow[];
  history: PriceHistoryRow[];
  honestResults: HonestResult[];
}

function loadForecastBundle(): Promise<ForecastBundle> {
  return Promise.all([
    loadMeta(),
    loadMandis(),
    loadForecasts(),
    loadPriceHistory(),
    loadHonestResults(),
  ]).then(([meta, mandis, forecasts, history, honestResults]) => ({
    meta,
    mandis,
    forecasts,
    history,
    honestResults,
  }));
}

const RISK_COLOR: Record<string, string> = {
  low: "text-green-700",
  medium: "text-amber-700",
  high: "text-red-700",
};

export default function ForecastPage() {
  const state = useAsyncData(loadForecastBundle);
  const [selectedMarketId, setSelectedMarketId] = useState<number | null>(null);
  const data = state.status === "success" ? state.data : null;

  // Auto-select a default mandi once per loaded bundle; user selection wins afterwards.
  const [autoSelectSource, setAutoSelectSource] = useState<ForecastBundle | null>(null);
  if (data && data !== autoSelectSource) {
    setAutoSelectSource(data);
    if (!data.forecasts.some((row) => row.market_id === selectedMarketId)) {
      const preferred =
        data.forecasts.find(
          (row) => row.as_of_date === data.meta.candidate_policy.eligible_as_of_date
        ) ?? data.forecasts[0];
      if (preferred) setSelectedMarketId(preferred.market_id);
    }
  }

  const mandiById = useMemo(
    () => new Map((data?.mandis ?? []).map((mandi) => [mandi.market_id, mandi])),
    [data]
  );
  const selectedForecast =
    data?.forecasts.find((row) => row.market_id === selectedMarketId) ?? null;
  const chartHistory = useMemo(
    () =>
      data && selectedForecast
        ? filterForecastHistory(
            data.history,
            selectedForecast.market_id,
            selectedForecast.as_of_date,
            HISTORY_DAYS
          )
        : [],
    [data, selectedForecast]
  );

  if (state.status === "loading") {
    return <LoadingState label="Loading forecast, history, and model evidence…" />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.error} onRetry={state.retry} />;
  }

  const { meta, forecasts, honestResults } = state.data;
  if (forecasts.length === 0) {
    return (
      <div className="space-y-6">
        <SampleBanner asOfDate={meta.snapshot_date} />
        <div>
          <h1 className="mb-1 text-xl font-bold">{meta.forecast_horizon_days}-Day Price Forecast</h1>
          <p className="text-sm text-gray-500">Maharashtra Onion</p>
        </div>
        <EmptyState
          title="No forecasts are available"
          detail="The bundle loaded successfully, but it contains no mandi forecast rows."
        />
      </div>
    );
  }

  const forecastDate = selectedForecast
    ? addDaysIso(selectedForecast.as_of_date, meta.forecast_horizon_days)
    : null;
  const staleDays = selectedForecast
    ? daysBehind(selectedForecast.as_of_date, meta.candidate_policy.eligible_as_of_date)
    : 0;
  const intervalLabel = `${(meta.confidence_level * 100).toFixed(0)}% interval`;

  return (
    <div className="space-y-6">
      <SampleBanner asOfDate={meta.snapshot_date} />

      <div>
        <h1 className="mb-1 text-xl font-bold">{meta.forecast_horizon_days}-Day Price Forecast</h1>
        <p className="text-sm text-gray-500">
          Maharashtra Onion — up to {HISTORY_DAYS} days of price history, capped at each forecast’s
          as-of date
        </p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <label htmlFor="forecast-mandi" className="text-sm font-medium text-gray-700">
          Select mandi
        </label>
        <select
          id="forecast-mandi"
          className="max-w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
          value={selectedMarketId ?? ""}
          onChange={(event) => setSelectedMarketId(Number(event.target.value))}
        >
          {forecasts.map((forecast) => {
            const optionStaleDays = daysBehind(
              forecast.as_of_date,
              meta.candidate_policy.eligible_as_of_date
            );
            const name = mandiById.get(forecast.market_id)?.market_name ?? forecast.mandi;
            return (
              <option key={forecast.market_id} value={forecast.market_id}>
                {name} — as of {forecast.as_of_date}
                {optionStaleDays > 0 ? ` (${optionStaleDays}d behind)` : " (current)"}
              </option>
            );
          })}
        </select>
      </div>

      {selectedForecast && staleDays > 0 && (
        <div
          className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800"
          role="status"
        >
          This mandi’s forecast is {staleDays} days behind the canonical as-of date {meta.candidate_policy.eligible_as_of_date}. It remains visible for coverage, but it is
          excluded from recommendations.
        </div>
      )}

      {selectedForecast && chartHistory.length > 0 ? (
        <div className="min-w-0 rounded border border-gray-200 bg-white p-2 sm:p-4">
          <ForecastChart
            history={chartHistory}
            forecast={selectedForecast}
            forecastDate={forecastDate}
          />
        </div>
      ) : (
        <EmptyState
          title="No usable history for this mandi"
          detail="Missing historical prices are retained as nulls in the bundle and omitted from the chart."
        />
      )}

      {selectedForecast && forecastDate && (
        <div className="grid grid-cols-1 gap-4 rounded border border-gray-200 bg-white p-4 text-sm sm:grid-cols-2 lg:grid-cols-6">
          <div>
            <div className="mb-0.5 text-xs text-gray-500">Forecast as of</div>
            <div className="font-semibold">{selectedForecast.as_of_date}</div>
            <div className={staleDays > 0 ? "text-xs text-amber-700" : "text-xs text-green-700"}>
              {staleDays > 0 ? `${staleDays}d behind` : "Current snapshot"}
            </div>
          </div>
          <div>
            <div className="mb-0.5 text-xs text-gray-500">Forecast target</div>
            <div className="font-semibold">{forecastDate}</div>
            <div className="text-xs text-gray-500">as-of + {meta.forecast_horizon_days} days</div>
          </div>
          <div>
            <div className="mb-0.5 text-xs text-gray-500">Forecast price</div>
            <div className="text-lg font-semibold">
              {selectedForecast.forecast_price_inr_qtl.toFixed(0)} INR/qtl
            </div>
          </div>
          <div>
            <div className="mb-0.5 text-xs text-gray-500">{intervalLabel}</div>
            <div className="text-lg font-semibold">
              {selectedForecast.lower_bound_inr_qtl.toFixed(0)} – {selectedForecast.upper_bound_inr_qtl.toFixed(0)}
            </div>
          </div>
          <div>
            <div className="mb-0.5 text-xs text-gray-500">Empirical coverage</div>
            <div className="text-lg font-semibold">
              {(meta.empirical_coverage * 100).toFixed(1)}% (nominal {(meta.confidence_level * 100).toFixed(0)}%)
            </div>
          </div>
          <div>
            <div className="mb-0.5 text-xs text-gray-500">Risk level</div>
            <div className={`text-lg font-semibold ${RISK_COLOR[selectedForecast.risk_level] ?? ""}`}>
              {selectedForecast.risk_level}
            </div>
          </div>
        </div>
      )}

      <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
        <strong>Shipped model:</strong> {meta.forecast_horizon_days}-day moving average (
        <span className="font-mono">{meta.model_version}</span>). LightGBM was trained but did not
        beat this baseline on the held-out test split, so the baseline ships.
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold text-gray-700">
          Model comparison (held-out test)
        </h2>
        {honestResults.length > 0 ? (
          <HonestResultsTable results={honestResults} />
        ) : (
          <EmptyState
            title="No model comparison is available"
            detail="Forecasts are present, but the held-out model-results artifact is empty."
          />
        )}
      </div>
    </div>
  );
}
