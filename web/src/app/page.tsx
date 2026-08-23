"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";
import {
  EvidenceBlock,
  PageHeader,
  Panel,
  SectionHeading,
  SnapshotNotice,
  StatusNotice,
  TextLink,
  buttonClass,
} from "@/components/ui/primitives";
import TopRecommendations from "@/components/TopRecommendations";
import { ErrorState, LoadingState } from "@/components/DataState";
import {
  loadBacktest,
  loadForecasts,
  loadHonestResults,
  loadMandis,
  loadMeta,
} from "@/lib/data";
import { rankRecommendationCandidates } from "@/lib/policy";
import {
  EM_DASH,
  formatDateIso,
  formatInrPerQtl,
  formatKm,
  formatPct,
} from "@/lib/format";
import { useAsyncData } from "@/lib/useAsyncData";
import type {
  BacktestSummary,
  ForecastRow,
  HonestResult,
  MandiMeta,
  Meta,
} from "@/lib/types";

interface HomeBundle {
  meta: Meta;
  mandis: MandiMeta[];
  forecasts: ForecastRow[];
  backtest: BacktestSummary;
  honestResults: HonestResult[];
}

function loadHomeBundle(): Promise<HomeBundle> {
  return Promise.all([
    loadMeta(),
    loadMandis(),
    loadForecasts(),
    loadBacktest(),
    loadHonestResults(),
  ]).then(([meta, mandis, forecasts, backtest, honestResults]) => ({
    meta,
    mandis,
    forecasts,
    backtest,
    honestResults,
  }));
}

const DEFAULT_QUANTITY_QTL = 100;

function formatCount(value: number): string {
  return value.toLocaleString("en-US");
}

export default function Home() {
  const state = useAsyncData(loadHomeBundle);
  const data = state.status === "success" ? state.data : null;

  const policyResult = useMemo(() => {
    if (!data) return null;
    const { meta, mandis, forecasts } = data;
    if (mandis.length === 0 || forecasts.length === 0) return null;
    return rankRecommendationCandidates(
      forecasts,
      mandis,
      meta.default_farmer.latitude,
      meta.default_farmer.longitude,
      meta,
      meta.ranking.cost_per_km_per_quintal,
      meta.ranking.max_transport_radius_km
    );
  }, [data]);

  // Cross-route links target /#method; the section exists only after the
  // bundle loads, so scroll to the hash once content is committed.
  useEffect(() => {
    if (state.status !== "success") return;
    const hash = window.location.hash;
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView();
  }, [state.status]);

  if (state.status === "loading") {
    return <LoadingState label="Loading the overview snapshot…" />;
  }
  if (state.status === "error") {
    return (
      <ErrorState
        message={state.error}
        onRetry={state.retry}
        hint={
          <p className="text-sm leading-relaxed text-ink-2">
            Expected artifacts are read from{" "}
            <code className="numeric">web/public/data/</code>. Regenerate them
            with <code className="numeric">python scripts/build_web_export.py</code>{" "}
            from the repository root.
          </p>
        }
      />
    );
  }

  const { meta, mandis, forecasts, backtest, honestResults } = state.data;
  const noSourceData = mandis.length === 0 || forecasts.length === 0;

  const defaultLat = meta.default_farmer.latitude;
  const defaultLon = meta.default_farmer.longitude;
  const defaultRate = meta.ranking.cost_per_km_per_quintal;
  const defaultRadius = meta.ranking.max_transport_radius_km;

  const ranked = policyResult?.rows ?? [];
  const top = ranked[0] ?? null;
  const shippedModel = honestResults.find((row) => row.ships) ?? null;
  const unshippedModels = honestResults.filter((row) => !row.ships);
  const canonicalAsOfDate = policyResult?.canonicalAsOfDate ?? meta.as_of_date;

  return (
    <div className="space-y-8">
      <SnapshotNotice />

      <PageHeader
        eyebrow="Market Atlas overview"
        title={`Sell where the transport-adjusted net price is strongest.`}
        intro={
          <>
            MandiPulse ranks {formatCount(mandis.length)} supported Maharashtra
            onion mandis by expected net price after estimated transport, using a
            frozen seven-day forecast. Every figure traces to a committed
            artifact; nothing is live.
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <Link href="/recommend" className={buttonClass.primary}>
          Compare mandis
        </Link>
        <Link href="#method" className={buttonClass.secondary}>
          Read the method
        </Link>
        <p className="text-xs text-muted">
          Defaults below come from the artifact configuration and stay editable in
          the workbench.
        </p>
      </div>

      {noSourceData ? (
        <StatusNotice tone="warning" title="No source rows">
          The snapshot loaded, but it contains no mandi or forecast rows. The
          decision preview cannot be rendered until the export artifacts are
          regenerated.
        </StatusNotice>
      ) : (
        <section aria-labelledby="preview-heading" className="space-y-4">
          <SectionHeading id="preview-heading">
            Decision preview at default assumptions
          </SectionHeading>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
            <EvidenceBlock
              title="Input summary"
              rows={[
                {
                  label: "Location",
                  value: `Default farmer · ${defaultLat.toFixed(4)}, ${defaultLon.toFixed(4)}`,
                },
                { label: "Quantity", value: `${DEFAULT_QUANTITY_QTL} qtl` },
                {
                  label: "Transport rate",
                  value: `${defaultRate} INR/km/quintal scenario`,
                },
                { label: "Road radius", value: formatKm(defaultRadius, 0) },
                { label: "Forecast as-of", value: formatDateIso(canonicalAsOfDate) },
              ]}
            />
            <Panel className="lg:col-span-8">
              <p className="text-sm leading-relaxed text-ink-2">
                This preview ranks candidates for the default location without any
                configuration. Open the workbench to set your own coordinates, lot
                size, rate, and radius.
              </p>
              <p className="mt-2 numeric text-xs text-muted">
                Eligible forecasts: {formatCount(policyResult?.eligibleAsOfCount ?? 0)}{" "}
                · stale excluded: {formatCount(policyResult?.excludedStaleCount ?? 0)} ·
                beyond radius excluded:{" "}
                {formatCount(policyResult?.excludedRadiusCount ?? 0)}
              </p>
            </Panel>
          </div>

          {top ? (
            <TopRecommendations
              rows={ranked}
              forecastHorizonDays={meta.forecast_horizon_days}
              confidenceLevel={meta.confidence_level}
              quantityQtl={DEFAULT_QUANTITY_QTL}
            />
          ) : (
            <StatusNotice tone="warning" title="No eligible candidates">
              No forecast matches the canonical as-of window or road radius for
              the default inputs. The full table in the{" "}
              <TextLink href="/recommend">decision workbench</TextLink> shows the
              exclusion counts.
            </StatusNotice>
          )}

          <p className="text-xs leading-relaxed text-muted">
            Ranking: expected net price minus estimated transport, highest first;
            equal prices break by market identifier. Forecast uncertainty is shown
            as separate evidence and does not change the order.
          </p>
        </section>
      )}

      <section aria-labelledby="evaluation-heading" className="space-y-4">
        <SectionHeading id="evaluation-heading">Evaluation facts</SectionHeading>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <EvidenceBlock
            title="Scope"
            rows={[
              { label: "Commodity", value: `${meta.crop} · ${meta.state}` },
              { label: "Supported mandis", value: formatCount(mandis.length) },
              { label: "Horizon", value: `${meta.forecast_horizon_days}-day ahead` },
              { label: "Snapshot end", value: formatDateIso(meta.snapshot_date) },
            ]}
          />
          <EvidenceBlock
            title="Shipped forecaster"
            rows={[
              {
                label: "Policy",
                value: shippedModel ? shippedModel.model : EM_DASH,
              },
              {
                label: "Held-out test MAE",
                value: shippedModel
                  ? formatInrPerQtl(shippedModel.test_mae)
                  : EM_DASH,
              },
              ...unshippedModels.map((row) => [
                {
                  label: `Not shipped: ${row.model}`,
                  value: `${formatInrPerQtl(row.test_mae)} — did not beat baseline`,
                },
              ]).flat(),
            ]}
          />
          <EvidenceBlock
            title="Prediction interval"
            rows={[
              {
                label: "Nominal level",
                value: formatPct(meta.confidence_level * 100, 0),
              },
              {
                label: "Observed coverage",
                value: formatPct(meta.empirical_coverage * 100, 1),
              },
              {
                label: "Reading",
                value: "Below nominal — not conservative",
              },
            ]}
          />
          <EvidenceBlock
            title="Ranking evaluation"
            rows={[
              {
                label: "Mean regret@1",
                value: formatInrPerQtl(backtest.mean_regret_at_1, 1),
              },
              {
                label: "Nearest-mandi baseline",
                value: formatInrPerQtl(backtest.nearest_mandi_baseline_regret, 1),
              },
              { label: "Wins vs nearest", value: formatPct(backtest.pct_beats_nearest) },
              {
                label: "Test window",
                value: `${formatDateIso(backtest.test_window_start)} – ${formatDateIso(backtest.test_window_end)}`,
              },
            ]}
          />
        </div>
        <p className="text-xs leading-relaxed text-muted">
          Evaluation uses temporal splits with a purge gap of at least the
          seven-day horizon; three rolling origins precede an untouched final
          holdout. Full definitions live in the{" "}
          <TextLink href="/coverage">coverage route</TextLink>.
        </p>
      </section>

      <section aria-labelledby="flow-heading" className="space-y-4">
        <SectionHeading id="flow-heading">How a ranking is produced</SectionHeading>
        <ol className="space-y-3">
          {[
            {
              title: "Frozen data snapshot",
              body: `A cleaned daily onion-price panel ending ${formatDateIso(meta.snapshot_date)} feeds every surface. Imputed and unavailable days are flagged, never silently filled.`,
            },
            {
              title: "Seven-day forecast with interval",
              body: `Each mandi receives a ${meta.forecast_horizon_days}-day-ahead price estimate plus a ${formatPct(meta.confidence_level * 100, 0)} prediction interval from the shipped policy above.`,
            },
            {
              title: "Transport estimate",
              body: `Straight-line distance times the documented road factor (${meta.ranking.road_distance_factor}) times your scenario rate approximates cost per quintal. It is not a route quote.`,
            },
            {
              title: "Transport-adjusted comparison",
              body: "Forecast minus transport gives expected net price per quintal; mandis rank highest-first with deterministic tie-breaks.",
            },
          ].map((step, index) => (
            <li key={step.title} className="flex gap-4">
              <span className="numeric mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-pill border border-rule-strong text-sm font-bold text-ink">
                {index + 1}
              </span>
              <div>
                <p className="font-bold text-ink">{step.title}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-ink-2">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="text-sm text-ink-2">
          Run the flow with your own inputs in the{" "}
          <TextLink href="/recommend">decision workbench</TextLink>, inspect a
          single mandi in <TextLink href="/forecast">forecast</TextLink>, or audit
          the underlying data in <TextLink href="/coverage">coverage</TextLink>.
        </p>
      </section>

      <section id="method" aria-labelledby="method-heading" className="space-y-4 scroll-mt-6">
        <SectionHeading id="method-heading">Method and limitations</SectionHeading>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          <Panel className="space-y-3 text-sm leading-relaxed text-ink-2 lg:col-span-7">
            <p>
              <strong className="text-ink">Scope.</strong> One commodity (onion),
              one state (Maharashtra), {formatCount(mandis.length)} mandis, a
              seven-day horizon, and a frozen snapshot ending{" "}
              {formatDateIso(meta.snapshot_date)}. Nothing outside that boundary is
              estimated.
            </p>
            <p>
              <strong className="text-ink">Temporal evaluation.</strong> Splits
              advance forward in time with a purge gap of at least the horizon so
              no target leaks into training. Three rolling origins precede an
              untouched final holdout; reported metrics come from held-out dates
              only.
            </p>
            <p>
              <strong className="text-ink">Forecasting policy.</strong>{" "}
              {shippedModel
                ? `The shipped forecaster (${shippedModel.model}) holds a held-out test MAE of ${formatInrPerQtl(shippedModel.test_mae)}.`
                : ""}{" "}
              A stronger model family was trained and evaluated honestly; it did
              not beat this baseline, so it does not ship.
            </p>
            <p>
              <strong className="text-ink">Uncertainty.</strong> Intervals use the
              split-conformal method. Observed coverage was{" "}
              {formatPct(meta.empirical_coverage * 100, 1)} against the{" "}
              {formatPct(meta.confidence_level * 100, 0)} nominal level — below
              nominal, and stated as such rather than described as conservative.
            </p>
            <p>
              <strong className="text-ink">Why uncertainty sits beside the rank,
              not inside it.</strong> The shipped interval width is identical for
              every candidate in a snapshot, so subtracting it would shift all
              prices equally and change no order. It is displayed as evidence per
              candidate instead.
            </p>
          </Panel>
          <Panel className="space-y-3 text-sm leading-relaxed text-ink-2 lg:col-span-5">
            <p className="text-xs font-bold uppercase tracking-wide text-muted">
              What this product does not do
            </p>
            <ul className="list-disc space-y-1.5 pl-5">
              <li>No live prices, market feed, or real-time freshness of any kind.</li>
              <li>No guaranteed, optimal, or risk-adjusted outcome claims.</li>
              <li>
                Transport figures are scenario estimates from air distance ×{" "}
                {meta.ranking.road_distance_factor} × your rate — not navigation or
                carrier quotations.
              </li>
              <li>
                Coordinates are expert input; there is no geocoding search.
              </li>
              <li>
                No booking, payment, trade execution, accounts, or messaging.
              </li>
              <li>
                No additional crops, states, horizons, or models beyond the frozen
                scope.
              </li>
            </ul>
          </Panel>
        </div>
      </section>
    </div>
  );
}
