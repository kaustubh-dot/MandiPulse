"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import BacktestSummary from "@/components/BacktestSummary";
import ForecastChart from "@/components/ForecastChart";
import {
  PageHeader,
  Panel,
  SectionHeading,
  SelectField,
  SnapshotNotice,
  StatusNotice,
  TextLink,
  buttonClass,
} from "@/components/ui/primitives";
import {
  loadBacktest,
  loadForecasts,
  loadHonestResults,
  loadMandis,
  loadMeta,
  loadPriceHistory,
} from "@/lib/data";
import {
  EM_DASH,
  formatDateIso,
  formatInrPerQtl,
  formatInterval,
  formatPct,
} from "@/lib/format";
import { addDaysIso, daysBehind, filterForecastHistory } from "@/lib/policy";
import type {
  BacktestSummary as BacktestSummaryData,
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
  backtest: BacktestSummaryData;
}

function loadForecastBundle(): Promise<ForecastBundle> {
  return Promise.all([
    loadMeta(),
    loadMandis(),
    loadForecasts(),
    loadPriceHistory(),
    loadHonestResults(),
    loadBacktest(),
  ]).then(([meta, mandis, forecasts, history, honestResults, backtest]) => ({
    meta,
    mandis,
    forecasts,
    history,
    honestResults,
    backtest,
  }));
}

function ForecastSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">Loading forecast workbench…</span>
      <div className="h-28 max-w-2xl animate-pulse rounded-panel bg-paper-2" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-4">
          <div className="h-[74px] animate-pulse rounded-panel bg-paper-2" />
          <div className="h-56 animate-pulse rounded-panel bg-paper-2" />
          <div className="h-72 animate-pulse rounded-panel bg-paper-2" />
        </div>
        <div className="lg:col-span-8">
          <div className="h-[620px] animate-pulse rounded-panel bg-paper-2" />
        </div>
      </div>
    </div>
  );
}

function ForecastView() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const state = useAsyncData(loadForecastBundle);
  const data = state.status === "success" ? state.data : null;

  const [selectedMarketId, setSelectedMarketId] = useState<number | null>(null);

  // Auto-select a default mandi once per loaded bundle; URL param and prior
  // user selection win afterwards.
  const [autoSelectSource, setAutoSelectSource] = useState<ForecastBundle | null>(null);
  if (data && data !== autoSelectSource) {
    setAutoSelectSource(data);
    const currentValid =
      selectedMarketId !== null &&
      data.forecasts.some((row) => row.market_id === selectedMarketId);
    if (!currentValid) {
      const rawParam = searchParams.get("mandi");
      const paramValue = rawParam === null ? Number.NaN : Number(rawParam);
      const paramValid =
        Number.isFinite(paramValue) &&
        data.forecasts.some((row) => row.market_id === paramValue);
      const preferred =
        data.forecasts.find(
          (row) =>
            row.as_of_date === data.meta.candidate_policy.eligible_as_of_date
        ) ?? data.forecasts[0];
      setSelectedMarketId(
        paramValid ? paramValue : (preferred?.market_id ?? null)
      );
    }
  }

  function handleMandiChange(value: string) {
    setSelectedMarketId(Number(value));
    router.replace(`/forecast?mandi=${encodeURIComponent(value)}`, {
      scroll: false,
    });
  }

  const mandiById = useMemo(
    () => new Map((data?.mandis ?? []).map((mandi) => [mandi.market_id, mandi])),
    [data]
  );
  const selectedForecast =
    data?.forecasts.find((row) => row.market_id === selectedMarketId) ?? null;
  const selectedMandi = selectedForecast
    ? (mandiById.get(selectedForecast.market_id) ?? null)
    : null;
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

  // Missingness over the raw window (filterForecastHistory drops nulls by
  // design, so counts come straight from the bundle).
  const windowQuality = useMemo(() => {
      if (!data || !selectedForecast) {
        return { total: 0, nullCount: 0, imputedCount: 0 };
      }
      const firstDate = addDaysIso(selectedForecast.as_of_date, -(HISTORY_DAYS - 1));
      let total = 0;
      let nullCount = 0;
      let imputedCount = 0;
      for (const row of data.history) {
        if (row.market_id !== selectedForecast.market_id) continue;
        if (row.date < firstDate || row.date > selectedForecast.as_of_date) continue;
        total += 1;
        if (row.modal_price_inr_qtl === null || !Number.isFinite(row.modal_price_inr_qtl)) {
          nullCount += 1;
        } else if (row.is_imputed) {
          imputedCount += 1;
        }
      }
      return { total, nullCount, imputedCount };
    }, [data, selectedForecast]);

  if (state.status === "loading") {
    return <ForecastSkeleton />;
  }

  if (state.status === "error") {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Forecast"
          title="Price forecast"
          intro="Maharashtra onion mandi price outlook."
        />
        <StatusNotice
          tone="danger"
          title="Problem"
          action={
            <button
              type="button"
              onClick={state.retry}
              className={buttonClass.secondary}
            >
              Retry
            </button>
          }
        >
          {state.error}
        </StatusNotice>
      </div>
    );
  }

  const { meta, forecasts, honestResults, backtest } = state.data;
  const nominalPct = Math.round(meta.confidence_level * 100);
  const canonicalAsOf = meta.candidate_policy.eligible_as_of_date;

  if (forecasts.length === 0 || !selectedForecast) {
    return (
      <div className="space-y-6">
        <SnapshotNotice />
        <PageHeader
          eyebrow="Forecast"
          title={`${meta.forecast_horizon_days}-day price forecast`}
          intro="Maharashtra onion."
        />
        <StatusNotice tone="info" title="No forecasts">
          The snapshot loaded successfully, but it contains no mandi forecast rows.
          See the coverage route for data provenance.
        </StatusNotice>
      </div>
    );
  }

  const forecastDate = addDaysIso(selectedForecast.as_of_date, meta.forecast_horizon_days);
  const staleDays = daysBehind(selectedForecast.as_of_date, canonicalAsOf);
  const mandiName =
    selectedMandi?.market_name ?? selectedForecast.mandi ?? EM_DASH;

  const pickerOptions = forecasts.map((forecast) => {
    const optionStaleDays = daysBehind(forecast.as_of_date, canonicalAsOf);
    const name = mandiById.get(forecast.market_id)?.market_name ?? forecast.mandi;
    return {
      value: String(forecast.market_id),
      label: `${name} \u2014 as of ${forecast.as_of_date}${
        optionStaleDays > 0 ? ` (${optionStaleDays}d behind)` : ""
      }`,
    };
  });

  return (
    <div className="space-y-6">
      <SnapshotNotice />

      <PageHeader
        eyebrow="Forecast"
        title={`${meta.forecast_horizon_days}-day price forecast`}
        intro={
          <>
            Maharashtra onion — up to {HISTORY_DAYS} days of observed prices per
            mandi and one {meta.forecast_horizon_days}-day-ahead target. The{" "}
            <strong>as-of date</strong> is the latest market date behind a forecast;
            the target date is {meta.forecast_horizon_days} days later. Prices are
            wholesale modal prices in INR/quintal.
          </>
        }
      />

      {staleDays > 0 ? (
        <StatusNotice tone="warning" title="Stale as-of date">
          This mandi’s forecast is <span className="numeric">{staleDays}</span>{" "}
          {staleDays === 1 ? "day" : "days"} behind the canonical as-of date (
          {formatDateIso(canonicalAsOf)}). It stays visible for transparency but is
          excluded from recommendations.
        </StatusNotice>
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Context column */}
        <div className="space-y-6 lg:col-span-4">
          <SelectField
            id="forecast-mandi"
            label="Mandi"
            value={String(selectedMarketId ?? "")}
            onChange={handleMandiChange}
            options={pickerOptions}
            hint={`“Nd behind” marks an as-of date earlier than the canonical snapshot date (${formatDateIso(canonicalAsOf)}). Changing the selection updates the page address.`}
          />

          <Panel className="space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-muted">
                Selected mandi
              </p>
              <h2 className="font-display text-2xl leading-tight text-ink">
                {mandiName}
              </h2>
              <p className="text-sm text-ink-2">
                {selectedMandi?.district_name ?? EM_DASH} district, Maharashtra
              </p>
            </div>

            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <div>
                <dt className="text-xs text-muted">As-of date</dt>
                <dd className="numeric text-ink">
                  {formatDateIso(selectedForecast.as_of_date)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Target date</dt>
                <dd className="numeric text-ink">{formatDateIso(forecastDate)}</dd>
              </div>
            </dl>

            <p
              className={`text-xs font-bold ${
                staleDays > 0 ? "text-warning" : "text-success"
              }`}
            >
              {staleDays > 0
                ? `As-of sits ${staleDays} days behind the canonical snapshot date`
                : "As-of matches the canonical snapshot date"}
            </p>
          </Panel>

          <section className="space-y-3">
            <SectionHeading>Model evidence</SectionHeading>
            <BacktestSummary
              models={honestResults}
              nDatesEvaluated={backtest.n_dates_evaluated}
              testWindowStart={backtest.test_window_start}
              testWindowEnd={backtest.test_window_end}
            />
            <p className="text-xs text-muted">
              Shipped artifact:{" "}
              <span className="numeric">{meta.model_version}</span>.
            </p>
          </section>

          <p className="text-sm leading-relaxed text-ink-2">
            Compare net-of-transport options before selling.{" "}
            <TextLink href="/recommend">Use the decision workbench</TextLink>
          </p>
        </div>

        {/* Chart column */}
        <div className="lg:col-span-8">
          <Panel className="space-y-4">
            <SectionHeading>
              Price history and {meta.forecast_horizon_days}-day forecast
            </SectionHeading>

            {chartHistory.length > 0 ? (
              <ForecastChart
                history={chartHistory}
                forecast={selectedForecast}
                forecastDate={forecastDate}
              />
            ) : (
              <StatusNotice tone="info" title="No plotted history">
                No finite observed prices exist in the {HISTORY_DAYS}-day window
                ending {formatDateIso(selectedForecast.as_of_date)}. Missing records
                remain in the bundle as nulls; see the coverage route for provenance.
              </StatusNotice>
            )}

            <div className="border-t border-rule pt-4">
              <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-muted">
                    Forecast for {formatDateIso(forecastDate)}
                  </p>
                  <p className="numeric mt-1 text-4xl font-bold leading-tight text-ink">
                    {formatInrPerQtl(selectedForecast.forecast_price_inr_qtl)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold uppercase tracking-wide text-muted">
                    {nominalPct}% prediction interval
                  </p>
                  <p className="numeric mt-1 text-lg text-ink">
                    {formatInterval(
                      selectedForecast.lower_bound_inr_qtl,
                      selectedForecast.upper_bound_inr_qtl
                    )}
                  </p>
                </div>
              </div>

              <p className="mt-3 text-xs leading-relaxed text-muted">
                Method: split-conformal, observed coverage 90.91% on internal Phase 3
                population; on this snapshot’s held-out dates, coverage was{" "}
                {formatPct(meta.empirical_coverage * 100, 1)} against the{" "}
                {formatPct(nominalPct, 0)} nominal level. As-of{" "}
                {formatDateIso(selectedForecast.as_of_date)}, target{" "}
                {formatDateIso(forecastDate)} (as-of +{" "}
                {meta.forecast_horizon_days} days);{" "}
                {staleDays > 0
                  ? `as-of sits ${staleDays} days behind the canonical snapshot date`
                  : "as-of matches the canonical snapshot date"}
                . A prediction interval is a calibrated range, not a certainty.
              </p>

              {windowQuality.total > 0 ? (
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  Data quality:{" "}
                  {windowQuality.nullCount > 0
                    ? `${windowQuality.nullCount} of ${windowQuality.total} daily records in the ${HISTORY_DAYS}-day window ending ${formatDateIso(selectedForecast.as_of_date)} are missing (null) and omitted from the chart.`
                    : `all ${windowQuality.total} daily records in the ${HISTORY_DAYS}-day window ending ${formatDateIso(selectedForecast.as_of_date)} carry finite prices.`}
                  {windowQuality.imputedCount > 0
                    ? ` ${windowQuality.imputedCount} ${
                        windowQuality.imputedCount === 1 ? "value is" : "values are"
                      } imputed fills, drawn as hollow markers.`
                    : ""}
                </p>
              ) : null}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

export default function ForecastPage() {
  // useSearchParams needs a Suspense boundary for the static export.
  return (
    <Suspense fallback={<ForecastSkeleton />}>
      <ForecastView />
    </Suspense>
  );
}
