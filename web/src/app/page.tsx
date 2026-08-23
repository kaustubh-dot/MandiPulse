"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/DataState";
import RecommendationControls, { FARMER_PRESETS } from "@/components/RecommendationControls";
import SampleBanner from "@/components/SampleBanner";
import TopRecommendations from "@/components/TopRecommendations";
import { loadForecasts, loadMandis, loadMeta } from "@/lib/data";
import { rankRecommendationCandidates } from "@/lib/policy";
import type { ForecastRow, MandiMeta, Meta } from "@/lib/types";
import { useAsyncData } from "@/lib/useAsyncData";

interface HomeBundle {
  meta: Meta;
  mandis: MandiMeta[];
  forecasts: ForecastRow[];
}

function loadHomeBundle(): Promise<HomeBundle> {
  return Promise.all([loadMeta(), loadMandis(), loadForecasts()]).then(
    ([meta, mandis, forecasts]) => ({ meta, mandis, forecasts })
  );
}

export default function Home() {
  const state = useAsyncData(loadHomeBundle);
  const [presetIndex, setPresetIndex] = useState(0);
  const [quantityQtl, setQuantityQtl] = useState(100);
  const [costPerKm, setCostPerKm] = useState(4);
  const [maxRadiusKm, setMaxRadiusKm] = useState(500);
  const data = state.status === "success" ? state.data : null;

  // Adopt artifact ranking config once per loaded bundle; editable afterwards.
  const [configSource, setConfigSource] = useState<Meta | null>(null);
  if (data && data.meta !== configSource) {
    setConfigSource(data.meta);
    setCostPerKm(data.meta.ranking.cost_per_km_per_quintal);
    setMaxRadiusKm(data.meta.ranking.max_transport_radius_km);
  }

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

  if (state.status === "loading") {
    return <LoadingState label="Loading the recommendation snapshot…" />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.error} onRetry={state.retry} />;
  }

  const { meta, mandis, forecasts } = state.data;
  const noSourceData = mandis.length === 0 || forecasts.length === 0;
  const ranked = policyResult?.rows ?? [];

  return (
    <div className="space-y-6">
      <SampleBanner asOfDate={meta.snapshot_date} />

      <section aria-labelledby="home-heading" className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Maharashtra onion · 7-day decision support</p>
        <h1 id="home-heading" className="text-3xl font-bold tracking-tight text-gray-950 sm:text-4xl">
          Choose the mandi with the best transport-adjusted net price.
        </h1>
        <p className="max-w-3xl text-base leading-7 text-gray-600">
          Enter the lot and transport assumptions below. MandiPulse ranks the frozen
          snapshot by expected net price: forecast minus estimated transport cost.
          Forecast uncertainty is shown as separate evidence and does not change the order.
        </p>
      </section>

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

          <div className="mp-panel border-blue-200 bg-blue-50 text-sm text-blue-950" role="status" aria-live="polite">
            <p className="font-semibold">
              Recommendation snapshot: as-of {policyResult?.canonicalAsOfDate ?? meta.as_of_date}
            </p>
            <p className="mt-1 text-blue-900">
              {policyResult?.eligibleAsOfCount ?? 0} current candidates · {policyResult?.excludedStaleCount ?? 0}{" "}
              stale forecasts excluded · {policyResult?.excludedRadiusCount ?? 0} outside {maxRadiusKm} km excluded.
            </p>
          </div>

          {ranked.length === 0 ? (
            <EmptyState
              title="No eligible mandi candidates"
              detail="Try increasing the maximum road radius. Candidates must also match the canonical as-of date."
            />
          ) : (
            <TopRecommendations
              rows={ranked}
              forecastHorizonDays={meta.forecast_horizon_days}
              confidenceLevel={meta.confidence_level}
              quantityQtl={quantityQtl}
            />
          )}

          <section className="grid grid-cols-1 gap-4 sm:grid-cols-3" aria-label="Explore evidence">
            <Link href="/recommend" className="mp-panel transition hover:border-blue-400 hover:shadow-md">
              <span className="text-sm font-semibold text-gray-900">See all ranked mandis</span>
              <span className="mt-1 block text-sm text-gray-600">Inspect the full table, map, and backtest.</span>
            </Link>
            <Link href="/forecast" className="mp-panel transition hover:border-blue-400 hover:shadow-md">
              <span className="text-sm font-semibold text-gray-900">Inspect the forecast</span>
              <span className="mt-1 block text-sm text-gray-600">Review observed history and the uncertainty interval.</span>
            </Link>
            <Link href="/coverage" className="mp-panel transition hover:border-blue-400 hover:shadow-md">
              <span className="text-sm font-semibold text-gray-900">Check data coverage</span>
              <span className="mt-1 block text-sm text-gray-600">See which mandis have current and missing observations.</span>
            </Link>
          </section>
        </>
      )}
    </div>
  );
}
