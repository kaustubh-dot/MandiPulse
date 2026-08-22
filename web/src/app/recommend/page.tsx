"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { EmptyState, ErrorState, LoadingState } from "@/components/DataState";
import SampleBanner from "@/components/SampleBanner";
import RecommendTable from "@/components/RecommendTable";
import BacktestSummaryCard from "@/components/BacktestSummary";
import RecommendationControls, { FARMER_PRESETS } from "@/components/RecommendationControls";
import TopRecommendations from "@/components/TopRecommendations";
import {
  loadBacktest,
  loadForecasts,
  loadMandis,
  loadMeta,
} from "@/lib/data";
import { rankRecommendationCandidates } from "@/lib/policy";
import { useAsyncData } from "@/lib/useAsyncData";
import type {
  Meta,
  MandiMeta,
  ForecastRow,
  BacktestSummary,
} from "@/lib/types";

const MandiMap = dynamic(() => import("@/components/MandiMap"), { ssr: false });

interface RecommendationBundle {
  meta: Meta;
  mandis: MandiMeta[];
  forecasts: ForecastRow[];
  backtest: BacktestSummary;
}

function loadRecommendationBundle(): Promise<RecommendationBundle> {
  return Promise.all([loadMeta(), loadMandis(), loadForecasts(), loadBacktest()]).then(
    ([meta, mandis, forecasts, backtest]) => ({ meta, mandis, forecasts, backtest })
  );
}

export default function RecommendPage() {
  const state = useAsyncData(loadRecommendationBundle);
  const [presetIndex, setPresetIndex] = useState(0);
  const [quantityQtl, setQuantityQtl] = useState(100);
  const [costPerKm, setCostPerKm] = useState(4);
  const [maxRadiusKm, setMaxRadiusKm] = useState(500);
  const data = state.status === "success" ? state.data : null;

  useEffect(() => {
    if (!data) return;
    setCostPerKm(data.meta.ranking.cost_per_km_per_quintal);
    setMaxRadiusKm(data.meta.ranking.max_transport_radius_km);
  }, [data]);

  const preset = FARMER_PRESETS[presetIndex] ?? FARMER_PRESETS[0];
  const policyResult = useMemo(
    () =>
      data
        ? rankRecommendationCandidates(
            data.forecasts,
            data.mandis,
            preset.lat,
            preset.lon,
            data.meta,
            costPerKm,
            maxRadiusKm
          )
        : null,
    [data, preset, costPerKm, maxRadiusKm]
  );
  const ranked = policyResult?.rows ?? [];
  const top1MarketId = ranked[0]?.market_id;

  if (state.status === "loading") {
    return <LoadingState label="Loading recommendations, forecasts, and model evidence…" />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.error} onRetry={state.retry} />;
  }

  const { meta, mandis, forecasts, backtest } = state.data;
  const noSourceData = mandis.length === 0 || forecasts.length === 0;
  const noEligibleRows = !noSourceData && ranked.length === 0;

  return (
    <div className="space-y-6">
      <SampleBanner asOfDate={meta.snapshot_date} />

      <div>
        <h1 className="mb-1 text-xl font-bold">Mandi Recommendation</h1>
        <p className="text-sm text-gray-500">
          Mandis ranked by risk-adjusted net price after transport cost. Adjust the decision inputs
          to re-rank eligible candidates instantly in the browser.
        </p>
      </div>

      {noSourceData ? (
        <EmptyState
          title="No recommendation data is available"
          detail="The snapshot loaded, but it contains no mandi or forecast rows to rank."
        />
      ) : (
        <>
          <RecommendationControls
            meta={meta}
            presetIndex={presetIndex}
            onPresetIndexChange={setPresetIndex}
            quantityQtl={quantityQtl}
            onQuantityChange={setQuantityQtl}
            costPerKm={costPerKm}
            onCostPerKmChange={setCostPerKm}
            maxRadiusKm={maxRadiusKm}
            onMaxRadiusChange={setMaxRadiusKm}
          />

          <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
            <p>
              Recommendations use forecasts with <strong>as-of = {policyResult?.canonicalAsOfDate}</strong>,
              a maximum road radius of {maxRadiusKm} km, and at most{" "}
              {meta.ranking.max_alternatives} alternatives.
            </p>
            <p className="mt-1 text-xs text-blue-800">
              {policyResult?.eligibleAsOfCount ?? 0} current candidates; {policyResult?.excludedStaleCount ?? 0}{" "}
              stale forecasts and {policyResult?.excludedRadiusCount ?? 0} out-of-radius candidates excluded.
            </p>
          </div>

          {noEligibleRows ? (
            <EmptyState
              title="No eligible mandi candidates"
              detail="Forecasts loaded, but none satisfy the canonical as-of date and transport-radius policy."
            />
          ) : (
            <div>
              <TopRecommendations
                rows={ranked}
                forecastHorizonDays={meta.forecast_horizon_days}
                confidenceLevel={meta.confidence_level}
                quantityQtl={quantityQtl}
              />
              <h2 className="mb-2 mt-6 text-sm font-semibold text-gray-700">
                All eligible mandis
              </h2>
              <RecommendTable rows={ranked} canonicalAsOfDate={policyResult?.canonicalAsOfDate ?? meta.as_of_date} />
              <p className="mt-1 text-xs text-gray-500">
                Ranking: risk_adjusted_score DESC → net price DESC. Road km = haversine × 1.3 factor.
              </p>
            </div>
          )}

          <div>
            <h2 className="mb-2 text-sm font-semibold text-gray-700">Map</h2>
            <MandiMap
              mandis={mandis}
              farmerLat={preset.lat}
              farmerLon={preset.lon}
              top1MarketId={top1MarketId}
            />
            <p className="mt-1 text-xs text-gray-400">
              Blue = farmer location. Green = top-ranked eligible mandi.
            </p>
          </div>
        </>
      )}

      <div className="rounded border border-gray-200 bg-white p-4">
        <BacktestSummaryCard data={backtest} />
      </div>
    </div>
  );
}
