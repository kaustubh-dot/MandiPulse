"use client";

import { Suspense, useEffect, useMemo, useReducer, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
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
import RecommendTable from "@/components/RecommendTable";
import RecommendationControls, {
  DECISION_DEFAULTS,
  type CopyState,
  type DecisionDrafts,
  type DecisionErrors,
  type DecisionField,
  parseDecisionParams,
  serializeDecisionParams,
  validateDecisionInput,
} from "@/components/RecommendationControls";
import TopRecommendations from "@/components/TopRecommendations";
import {
  EM_DASH,
  formatDateIso,
  formatInrPerQtl,
  formatInterval,
  formatKm,
  formatPct,
} from "@/lib/format";
import { loadBacktest, loadForecasts, loadMandis, loadMeta } from "@/lib/data";
import { addDaysIso, rankRecommendationCandidates } from "@/lib/policy";
import { useAsyncData } from "@/lib/useAsyncData";
import type {
  Meta,
  MandiMeta,
  ForecastRow,
  BacktestSummary,
} from "@/lib/types";

const MandiMap = dynamic(() => import("@/components/MandiMap"), {
  ssr: false,
  loading: () => <div className="h-[400px] w-full animate-pulse rounded bg-paper-2" aria-hidden="true" />,
});

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

const FIELD_ORDER: DecisionField[] = ["lat", "lon", "quantity", "rate", "radius"];

function toDecisionNumbers(drafts: DecisionDrafts): Record<DecisionField, number> {
  return {
    lat: Number(drafts.lat),
    lon: Number(drafts.lon),
    quantity: Number(drafts.quantity),
    rate: Number(drafts.rate),
    radius: Number(drafts.radius),
  };
}

interface InputState {
  drafts: DecisionDrafts;
  decision: Record<DecisionField, number>;
  errors: DecisionErrors;
  erroredOnce: Partial<Record<DecisionField, boolean>>;
  syncedSearchParamString: string;
  configSource: Meta | null;
}

type InputAction =
  | { type: "sync"; searchParamString: string; parsed: Partial<DecisionDrafts>; meta: Meta | null }
  | { type: "change"; field: DecisionField; value: string }
  | { type: "blur"; field: DecisionField; message?: string }
  | { type: "compare-errors"; errors: DecisionErrors }
  | { type: "commit"; decision: Record<DecisionField, number> };

function draftsFromParams(parsed: Partial<DecisionDrafts>, meta: Meta | null): DecisionDrafts {
  const defaults = meta
    ? {
        rate: String(meta.ranking.cost_per_km_per_quintal),
        radius: String(meta.ranking.max_transport_radius_km),
      }
    : {};
  return { ...DECISION_DEFAULTS, ...defaults, ...parsed };
}

function inputReducer(state: InputState, action: InputAction): InputState {
  switch (action.type) {
    case "sync": {
      if (
        action.searchParamString === state.syncedSearchParamString &&
        action.meta === state.configSource
      ) {
        return state;
      }
      const drafts = draftsFromParams(action.parsed, action.meta);
      return {
        ...state,
        drafts,
        decision: toDecisionNumbers(drafts),
        errors: {},
        erroredOnce: {},
        syncedSearchParamString: action.searchParamString,
        configSource: action.meta,
      };
    }
    case "change":
      return {
        ...state,
        drafts: { ...state.drafts, [action.field]: action.value },
        errors: state.erroredOnce[action.field]
          ? { ...state.errors, [action.field]: validateDecisionInput(action.field, action.value) }
          : state.errors,
      };
    case "blur":
      return {
        ...state,
        errors: { ...state.errors, [action.field]: action.message },
        erroredOnce: action.message
          ? { ...state.erroredOnce, [action.field]: true }
          : state.erroredOnce,
      };
    case "compare-errors":
      return {
        ...state,
        errors: action.errors,
        erroredOnce:
          Object.keys(action.errors).length > 0
            ? { lat: true, lon: true, quantity: true, rate: true, radius: true }
            : state.erroredOnce,
      };
    case "commit":
      return {
        ...state,
        decision: action.decision,
      };
  }
}

function formatCount(value: number): string {
  return value.toLocaleString("en-US");
}

export default function RecommendPage() {
  return (
    <Suspense fallback={null}>
      <RecommendWorkbench />
    </Suspense>
  );
}

function WorkbenchSkeleton() {
  return (
    <>
      <p className="sr-only" role="status">
        Loading recommendations, forecasts, and model evidence.
      </p>
      <div aria-hidden="true" className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="space-y-4 lg:col-span-4">
          <div className="h-4 w-32 animate-pulse rounded bg-paper-2" />
          {[0, 1, 2, 3, 4].map((index) => (
            <div key={index} className="space-y-1">
              <div className="h-3 w-24 animate-pulse rounded bg-paper-2" />
              <div className="h-11 animate-pulse rounded-control bg-paper-2" />
            </div>
          ))}
          <div className="h-11 animate-pulse rounded-control bg-paper-2" />
          <div className="h-11 animate-pulse rounded-control bg-paper-2" />
        </Panel>
        <div className="space-y-6 lg:col-span-8">
          <Panel>
            <div className="h-56 animate-pulse rounded bg-paper-2" />
          </Panel>
          <Panel>
            <div className="h-72 animate-pulse rounded bg-paper-2" />
          </Panel>
          <Panel>
            <div className="h-[400px] animate-pulse rounded bg-paper-2" />
          </Panel>
        </div>
      </div>
    </>
  );
}

function RecommendWorkbench() {
  const searchParams = useSearchParams();

  return <RecommendWorkbenchState searchParams={searchParams} />;
}

function RecommendWorkbenchState({
  searchParams,
}: {
  searchParams: ReturnType<typeof useSearchParams>;
}) {
  const state = useAsyncData(loadRecommendationBundle);
  const router = useRouter();

  const searchParamString = searchParams.toString();
  const [inputState, dispatchInput] = useReducer(
    inputReducer,
    searchParamString,
    (initialSearchParamString): InputState => {
      const parsed = parseDecisionParams(new URLSearchParams(initialSearchParamString));
      const drafts = draftsFromParams(parsed, null);
      return {
        drafts,
        decision: toDecisionNumbers(drafts),
        errors: {},
        erroredOnce: {},
        syncedSearchParamString: initialSearchParamString,
        configSource: null,
      };
    }
  );
  const { drafts, decision, errors } = inputState;
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const copyTimerRef = useRef<number | null>(null);
  const data = state.status === "success" ? state.data : null;
  const artifactMeta = data?.meta ?? null;

  useEffect(() => {
    return () => {
      if (copyTimerRef.current !== null) window.clearTimeout(copyTimerRef.current);
    };
  }, []);

  useEffect(() => {
    dispatchInput({
      type: "sync",
      searchParamString,
      parsed: parseDecisionParams(new URLSearchParams(searchParamString)),
      meta: artifactMeta,
    });
  }, [searchParamString, artifactMeta]);

  const policyResult = useMemo(
    () =>
      data
        ? rankRecommendationCandidates(
            data.forecasts,
            data.mandis,
            decision.lat,
            decision.lon,
            data.meta,
            decision.rate,
            decision.radius
          )
        : null,
    [data, decision]
  );

  function handleChange(field: DecisionField, value: string) {
    dispatchInput({ type: "change", field, value });
  }

  function handleBlurField(field: DecisionField) {
    const message = validateDecisionInput(field, drafts[field]);
    dispatchInput({ type: "blur", field, message });
  }

  function handleCompare() {
    const nextErrors: DecisionErrors = {};
    let valid = true;
    for (const field of FIELD_ORDER) {
      const message = validateDecisionInput(field, drafts[field]);
      if (message) {
        nextErrors[field] = message;
        valid = false;
      }
    }
    dispatchInput({ type: "compare-errors", errors: nextErrors });
    if (!valid) {
      return;
    }
    const numbers = toDecisionNumbers(drafts);
    const newQuery = serializeDecisionParams(numbers);
    dispatchInput({ type: "commit", decision: numbers });
    router.push(`/recommend/?${newQuery}`, { scroll: false });
  }

  async function handleCopyLink() {
    try {
      const url = `${window.location.origin}/recommend/?${serializeDecisionParams(toDecisionNumbers(drafts))}`;
      await navigator.clipboard.writeText(url);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
    if (copyTimerRef.current !== null) window.clearTimeout(copyTimerRef.current);
    copyTimerRef.current = window.setTimeout(() => setCopyState("idle"), 3000);
  }

  if (state.status === "loading") {
    return <WorkbenchSkeleton />;
  }
  if (state.status === "error") {
    return (
      <div className="space-y-6">
        <SnapshotNotice />
        <StatusNotice
          tone="danger"
          title="Snapshot failed to load"
          action={
            <button type="button" onClick={state.retry} className={buttonClass.secondary}>
              Retry
            </button>
          }
        >
          {state.error}
        </StatusNotice>
      </div>
    );
  }

  const { meta, mandis, forecasts, backtest } = state.data;
  const ranked = policyResult?.rows ?? [];
  const top = ranked[0] ?? null;
  const alternates = ranked.slice(1, 3);
  const canonicalAsOfDate = policyResult?.canonicalAsOfDate ?? meta.as_of_date;
  const targetDate = top ? addDaysIso(top.as_of_date, meta.forecast_horizon_days) : null;
  const noSourceData = mandis.length === 0 || forecasts.length === 0;
  const noEligibleRows = !noSourceData && ranked.length === 0;
  const hasFarmerCoords =
    Number.isFinite(decision.lat) && Number.isFinite(decision.lon);
  const announce =
    noSourceData || noEligibleRows || !top
      ? "No ranked candidates for the current inputs."
      : `Rankings updated for latitude ${decision.lat}, longitude ${decision.lon}. Rank 1: ${top.mandi}, ${formatInrPerQtl(top.transport_adjusted_net_price_inr_qtl)}.`;

  return (
    <div data-layout="quiet-workbench" className="space-y-12">
      <SnapshotNotice />

      <div className="relative isolate grid gap-8 border-b border-rule pb-10 lg:grid-cols-[minmax(0,0.9fr)_minmax(18rem,0.6fr)]">
        <PageHeader
          title="Compare mandis for your next sale"
          intro="Set your location, lot size, and transport assumptions. Mandis rank by transport-adjusted net expected price from a frozen seven-day forecast."
        />
      </div>

      {noSourceData ? (
        <StatusNotice tone="warning" title="No source rows">
          The snapshot loaded, but it contains no mandi or forecast rows to rank.
          Regenerate the export artifacts, then reload this page.
        </StatusNotice>
      ) : (
        <>
          <div className="grid min-w-0 grid-cols-1 gap-8 lg:grid-cols-12">
            <div className="min-w-0 lg:col-span-4">
              <RecommendationControls
                meta={meta}
                drafts={drafts}
                errors={errors}
                copyState={copyState}
                horizonDays={meta.forecast_horizon_days}
                onChange={handleChange}
                onBlurField={handleBlurField}
                onCompare={handleCompare}
                onCopyLink={handleCopyLink}
              />
            </div>

            <div className="min-w-0 space-y-10 lg:col-span-8">
              <p aria-live="polite" className="sr-only">
                {announce}
              </p>

              {noEligibleRows ? (
                <StatusNotice tone="warning" title="No eligible candidates">
                  {policyResult?.eligibleAsOfCount ?? 0} forecasts match the current
                  window; {policyResult?.excludedStaleCount ?? 0} are excluded as stale
                  by the canonical as-of policy. Of those fresh forecasts,{" "}
                  {policyResult?.excludedRadiusCount ?? 0} sit beyond{" "}
                  {formatKm(decision.radius, 0)}. Increase the maximum road radius,
                  then compare again.
                </StatusNotice>
              ) : (
                <>
                  <TopRecommendations
                    rows={ranked}
                    forecastHorizonDays={meta.forecast_horizon_days}
                    confidenceLevel={meta.confidence_level}
                    quantityQtl={decision.quantity}
                  />

                  <section aria-labelledby="all-mandis-heading" className="space-y-4">
                    <SectionHeading id="all-mandis-heading">
                      All eligible mandis
                    </SectionHeading>
                    <RecommendTable rows={ranked} canonicalAsOfDate={canonicalAsOfDate} />
                    <p className="text-xs leading-relaxed text-muted">
                      Ranking: transport-adjusted net expected
                      price, highest first; equal prices break by market identifier.
                    </p>
                  </section>

                  <section aria-labelledby="map-heading" className="space-y-4">
                    <SectionHeading id="map-heading">Candidate map</SectionHeading>
                    {!hasFarmerCoords ? (
                      <StatusNotice tone="warning" title="Map incomplete">
                        Your coordinates cannot be plotted. Every figure above and every
                        candidate marker below remains available.
                      </StatusNotice>
                    ) : null}
                    <MandiMap
                      mandis={mandis}
                      farmerLat={hasFarmerCoords ? decision.lat : undefined}
                      farmerLon={hasFarmerCoords ? decision.lon : undefined}
                      top1MarketId={top?.market_id}
                      labeledMarketIds={alternates.map((row) => row.market_id)}
                      topPopupNetPrice={
                        top
                          ? formatInrPerQtl(top.transport_adjusted_net_price_inr_qtl)
                          : undefined
                      }
                      topPopupRoadDistance={
                        top ? formatKm(top.road_distance_km) : undefined
                      }
                    />
                    <p className="text-xs leading-relaxed text-muted">
                      Ring: your location. Large labelled circle: rank-1 mandi. Smaller
                      circles: other candidates. Exact distances repeat in the table
                      above.
                    </p>
                  </section>
                </>
              )}
            </div>
          </div>

          <section aria-labelledby="method-evidence-heading" className="space-y-6">
            <SectionHeading id="method-evidence-heading">Method and evidence</SectionHeading>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <EvidenceBlock
                title="Interval method"
                rows={[
                  {
                    label: "Nominal level",
                    value: formatPct(meta.confidence_level * 100, 0),
                  },
                  {
                    label: "Empirical coverage",
                    value: formatPct(meta.empirical_coverage * 100, 1),
                  },
                  {
                    label: "Rank-1 bounds",
                    value: top
                      ? formatInterval(
                          top.lower_bound_inr_qtl,
                          top.upper_bound_inr_qtl
                        )
                      : EM_DASH,
                  },
                  { label: "Interval widths", value: "Uniform across candidates" },
                ]}
              />
              <EvidenceBlock
                title="Snapshot and horizon"
                rows={[
                  { label: "Snapshot date", value: formatDateIso(meta.snapshot_date) },
                  { label: "Forecast as-of", value: formatDateIso(canonicalAsOfDate) },
                  {
                    label: "Sale target",
                    value: targetDate ? formatDateIso(targetDate) : EM_DASH,
                  },
                  { label: "Horizon", value: `${meta.forecast_horizon_days}-day ahead` },
                  { label: "Commodity", value: `${meta.crop} \u00b7 ${meta.state}` },
                ]}
              />
              <EvidenceBlock
                title="Transport assumptions"
                rows={[
                  {
                    label: "Road estimate",
                    value: `Haversine air distance \u00d7 ${meta.ranking.road_distance_factor}`,
                  },
                  {
                    label: "Rate applied",
                    value: `${decision.rate} INR/km/quintal scenario, not a carrier quotation`,
                  },
                  { label: "Max radius", value: formatKm(decision.radius, 0) },
                  {
                    label: "Uncertainty penalty",
                    value: top
                      ? `${formatInrPerQtl(top.uncertainty_penalty_inr_qtl)} \u2014 identical across candidates; does not affect order`
                      : EM_DASH,
                  },
                ]}
              />
              <EvidenceBlock
                title="Candidate eligibility"
                rows={[
                  {
                    label: "Eligible forecasts",
                    value: formatCount(policyResult?.eligibleAsOfCount ?? 0),
                  },
                  {
                    label: "Stale excluded",
                    value: formatCount(policyResult?.excludedStaleCount ?? 0),
                  },
                  {
                    label: "Beyond radius (of fresh)",
                    value: formatCount(policyResult?.excludedRadiusCount ?? 0),
                  },
                  {
                    label: "Shown",
                    value: `${formatCount(ranked.length)} of ${formatCount(meta.ranking.max_alternatives)}`,
                  },
                ]}
              />
              <EvidenceBlock
                title="Regret evaluation"
                rows={[
                  {
                    label: "Mean regret@1",
                    value: formatInrPerQtl(backtest.mean_regret_at_1, 1),
                  },
                  {
                    label: "Nearest-mandi baseline",
                    value: formatInrPerQtl(backtest.nearest_mandi_baseline_regret, 1),
                  },
                  {
                    label: "Wins vs nearest",
                    value: formatPct(backtest.pct_beats_nearest),
                  },
                  {
                    label: "Test window",
                    value: `${formatDateIso(backtest.test_window_start)} \u2013 ${formatDateIso(backtest.test_window_end)}`,
                  },
                  {
                    label: "Dates evaluated",
                    value: formatCount(backtest.n_dates_evaluated),
                  },
                  {
                    label: "Methodology",
                    value: <TextLink href="/#method">How rankings were measured</TextLink>,
                  },
                ]}
              />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
