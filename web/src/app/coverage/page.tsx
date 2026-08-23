"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { EmptyState, ErrorState, LoadingState } from "@/components/DataState";
import HonestResultsTable from "@/components/HonestResultsTable";
import {
  EvidenceBlock,
  PageHeader,
  Panel,
  SectionHeading,
  SelectField,
  SnapshotNotice,
  StatusNotice,
  TextLink,
} from "@/components/ui/primitives";
import {
  loadHonestResults,
  loadMandis,
  loadMeta,
  loadPriceHistory,
} from "@/lib/data";
import { formatDateIso, formatPct } from "@/lib/format";
import { daysBehind } from "@/lib/policy";
import type { MandiMeta, Meta, PriceHistoryRow } from "@/lib/types";
import { useAsyncData } from "@/lib/useAsyncData";

const MandiMap = dynamic(() => import("@/components/MandiMap"), { ssr: false });

interface CoverageBundle {
  meta: Meta;
  mandis: MandiMeta[];
  history: PriceHistoryRow[];
}

interface MandiStats {
  market_id: number;
  market_name: string;
  first_date: string | null;
  last_date: string | null;
  active_days: number;
  total_rows: number;
  available_rows: number;
  imputed_rows: number;
  unavailable_rows: number;
  available_pct: number;
  imputed_pct: number;
  unavailable_pct: number;
}

function loadCoverageBundle(): Promise<CoverageBundle> {
  return Promise.all([loadMeta(), loadMandis(), loadPriceHistory()]).then(
    ([meta, mandis, history]) => ({ meta, mandis, history })
  );
}

function computeStats(history: PriceHistoryRow[], mandis: MandiMeta[]): MandiStats[] {
  const grouped = new Map<number, PriceHistoryRow[]>();
  for (const row of history) {
    const bucket = grouped.get(row.market_id) ?? [];
    bucket.push(row);
    grouped.set(row.market_id, bucket);
  }

  return mandis.map((mandi) => {
    const rows = grouped.get(mandi.market_id) ?? [];
    const availableRows = rows.filter(
      (row) => row.modal_price_inr_qtl !== null && Number.isFinite(row.modal_price_inr_qtl)
    );
    const dates = availableRows.map((row) => row.date).sort();
    const unavailableRows = rows.length - availableRows.length;
    const imputedRows = availableRows.filter((row) => row.is_imputed).length;
    const totalRows = rows.length;

    return {
      market_id: mandi.market_id,
      market_name: mandi.market_name,
      first_date: dates[0] ?? null,
      last_date: dates[dates.length - 1] ?? null,
      active_days: mandi.active_days,
      total_rows: totalRows,
      available_rows: availableRows.length,
      imputed_rows: imputedRows,
      unavailable_rows: unavailableRows,
      available_pct: totalRows > 0 ? (availableRows.length / totalRows) * 100 : 0,
      imputed_pct: totalRows > 0 ? (imputedRows / totalRows) * 100 : 0,
      unavailable_pct: totalRows > 0 ? (unavailableRows / totalRows) * 100 : 100,
    };
  });
}

function formatCount(value: number): string {
  return value.toLocaleString("en-US");
}

const REGEN_HINT = (
  <p className="text-sm leading-relaxed text-ink-2">
    Expected artifacts are read from <code className="numeric">web/public/data/</code>.
    Regenerate them with{" "}
    <code className="numeric">python scripts/build_web_export.py</code> from the
    repository root. Missing values are never replaced with zeros.
  </p>
);

export default function CoveragePage() {
  const state = useAsyncData(loadCoverageBundle);
  const honestState = useAsyncData(loadHonestResults);
  const [focusId, setFocusId] = useState("");
  const stats = useMemo(
    () => (state.status === "success" ? computeStats(state.data.history, state.data.mandis) : []),
    [state]
  );

  if (state.status === "loading") {
    return <LoadingState label="Loading coverage, mandi metadata, and price history…" />;
  }
  if (state.status === "error") {
    return (
      <ErrorState message={state.error} onRetry={state.retry} hint={REGEN_HINT} />
    );
  }

  const { meta, mandis } = state.data;
  const totalMandiDays = stats.reduce((sum, row) => sum + row.available_rows, 0);
  const isEmpty = mandis.length === 0 || stats.length === 0 || totalMandiDays === 0;

  const observedDates = stats
    .flatMap((row) => [row.first_date, row.last_date])
    .filter((date): date is string => date !== null)
    .sort();
  const earliestDate = observedDates[0] ?? null;
  const latestDate = observedDates[observedDates.length - 1] ?? null;
  const daysBehindSnapshot =
    latestDate !== null ? daysBehind(latestDate, meta.snapshot_date) : null;

  const sortedStats = [...stats].sort((a, b) => b.active_days - a.active_days);
  const worstUnavailablePct = stats.reduce(
    (max, row) => Math.max(max, row.unavailable_pct),
    0
  );

  const focusOptions = [...stats]
    .sort((a, b) => a.market_name.localeCompare(b.market_name))
    .map((row) => ({
      value: String(row.market_id),
      label: `${row.market_name} — ${mandis.find((m) => m.market_id === row.market_id)?.district_name ?? ""}`,
    }));
  const activeFocusId = focusOptions.some((option) => option.value === focusId)
    ? focusId
    : focusOptions[0]?.value ?? "";
  const focusedStat = stats.find((row) => String(row.market_id) === activeFocusId);
  const focusedMandi = mandis.find((mandi) => String(mandi.market_id) === activeFocusId);
  const focusedObservedRows = focusedStat
    ? focusedStat.available_rows - focusedStat.imputed_rows
    : 0;
  const focusedMissingPct = focusedStat ? focusedStat.unavailable_pct : 0;

  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="Coverage provenance"
        title="What the snapshot actually contains"
        intro={
          <>
            Every figure elsewhere in this app traces back to one fixed data bundle.
            This page shows how much of that bundle exists, where the gaps sit, and
            which artifacts produced each number. Absence is reported as absence:
            missing mandi-days are never filled with zeros.
          </>
        }
      />

      <SnapshotNotice />

      {isEmpty ? (
        <EmptyState
          title="No coverage data is available in this snapshot"
          detail="The bundle loaded, but it contains no finite historical price observations, so per-mandi coverage cannot be computed. Reporting this as absence keeps zero values out of the evidence."
          nextAction={<TextLink href="/#method">Read the method summary</TextLink>}
        />
      ) : (
        <div className="grid items-start gap-10 lg:grid-cols-12">
          <div className="space-y-10 lg:col-span-4">
            <section aria-labelledby="snapshot-range" className="space-y-3">
              <SectionHeading id="snapshot-range">Snapshot range</SectionHeading>
              <Panel>
                <p className="text-xs font-bold uppercase tracking-wide text-muted">
                  Last available observation
                </p>
                <p className="numeric mt-1 text-4xl leading-none text-ink">
                  {latestDate !== null ? formatDateIso(latestDate) : "Not observed"}
                </p>
                <dl className="mt-4 space-y-2 text-sm">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                    <dt className="text-ink-2">Earliest available observation</dt>
                    <dd className="numeric text-ink">
                      {earliestDate !== null ? formatDateIso(earliestDate) : "Not observed"}
                    </dd>
                  </div>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                    <dt className="text-ink-2">Snapshot date</dt>
                    <dd className="numeric text-ink">{formatDateIso(meta.snapshot_date)}</dd>
                  </div>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                    <dt className="text-ink-2">Latest vs snapshot</dt>
                    <dd className="numeric text-ink">
                      {daysBehindSnapshot === null
                        ? "No observations"
                        : daysBehindSnapshot === 0
                          ? "Matches the snapshot date"
                          : `${formatCount(daysBehindSnapshot)} days behind`}
                    </dd>
                  </div>
                </dl>
                <p className="mt-4 border-t border-rule pt-3 text-xs leading-relaxed text-muted">
                  Range reflects dates present in web/public/data/price_history.json.
                </p>
              </Panel>
            </section>

            <section aria-labelledby="scope-facts" className="space-y-3">
              <SectionHeading id="scope-facts">Scope and row definitions</SectionHeading>
              <EvidenceBlock
                title="Scope facts"
                rows={[
                  {
                    label: "Mandis in scope",
                    value: `${mandis.length} selected mandis (top 15 by historical coverage)`,
                  },
                  {
                    label: "Clean panel rows",
                    value: `${formatCount(31950)} mandi-day rows in the cleaned research panel`,
                  },
                  {
                    label: "Displayed window",
                    value: "180 days ending at the snapshot date",
                  },
                  {
                    label: "Observed row",
                    value: "Price present in the source records; not filled by any process",
                  },
                  {
                    label: "Imputed row",
                    value: "Gap filled by the pipeline; flagged is_imputed in the export",
                  },
                  {
                    label: "Missing row",
                    value:
                      "No observation exists for that mandi-day; treated as absence, never as a zero price",
                  },
                  {
                    label: "Trainable row",
                    value:
                      "Row usable for modeling once the lookback window before it is satisfied",
                  },
                ]}
              />
            </section>
          </div>

          <div className="space-y-10 lg:col-span-8">
            <section aria-labelledby="comparability" className="space-y-3">
              <SectionHeading id="comparability">Per-mandi comparability</SectionHeading>
              <p className="max-w-3xl text-base leading-7 text-ink-2">
                Sorted by active days. Shares are computed over all rows in the displayed
                window for each mandi. The largest unavailability gaps are called out in
                place rather than hidden in averages.
              </p>
              <p className="text-xs text-muted">
                Narrow screens: scroll horizontally to see every column.
              </p>
              <div
                role="region"
                aria-label="Per-mandi data coverage"
                tabIndex={0}
                className="overflow-x-auto rounded-panel border border-rule"
              >
                <table className="w-full min-w-[760px] border-collapse text-sm">
                  <caption className="sr-only">
                    First seen, last seen, active days, and observed, imputed, and
                    unavailable shares for each mandi
                  </caption>
                  <thead>
                    <tr className="border-b border-rule-strong text-left">
                      <th
                        scope="col"
                        className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Mandi
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        First seen
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Last seen
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Active days
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Available
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Imputed
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
                      >
                        Unavailable
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedStats.map((row) => {
                      const isWorstGap =
                        row.unavailable_pct > 0 &&
                        row.unavailable_pct === worstUnavailablePct;
                      return (
                        <tr key={row.market_id} className="border-b border-rule last:border-b-0">
                          <td className="px-3 py-2 font-bold text-ink">{row.market_name}</td>
                          <td className="numeric px-3 py-2 text-right text-ink-2">
                            {row.first_date !== null ? (
                              formatDateIso(row.first_date)
                            ) : (
                              <span className="text-muted">Not observed</span>
                            )}
                          </td>
                          <td className="numeric px-3 py-2 text-right text-ink-2">
                            {row.last_date !== null ? (
                              formatDateIso(row.last_date)
                            ) : (
                              <span className="text-muted">Not observed</span>
                            )}
                          </td>
                          <td className="numeric px-3 py-2 text-right text-ink">
                            {formatCount(row.active_days)}
                          </td>
                          <td className="numeric px-3 py-2 text-right text-ink">
                            {formatPct(row.available_pct)}
                          </td>
                          <td className="numeric px-3 py-2 text-right text-ink-2">
                            {formatPct(row.imputed_pct)}
                          </td>
                          <td className="px-3 py-2 text-right">
                            <span
                              className={`numeric ${
                                isWorstGap ? "font-bold text-warning" : "text-ink-2"
                              }`}
                            >
                              {formatPct(row.unavailable_pct)} unavailable
                              {isWorstGap ? " — largest gap" : ""}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            <section aria-labelledby="mandi-focus" className="space-y-3">
              <SectionHeading id="mandi-focus">Mandi focus</SectionHeading>
              <SelectField
                id="mandi-focus-select"
                label="Choose a mandi"
                hint="Switches the focused coverage record and availability bar below."
                value={activeFocusId}
                onChange={setFocusId}
                options={focusOptions}
              />
              {focusedStat && focusedMandi ? (
                <div className="space-y-4">
                  <EvidenceBlock
                    title={`${focusedStat.market_name} — ${focusedMandi.district_name}`}
                    rows={[
                      {
                        label: "First seen",
                        value:
                          focusedStat.first_date !== null
                            ? formatDateIso(focusedStat.first_date)
                            : "Not observed",
                      },
                      {
                        label: "Last seen",
                        value:
                          focusedStat.last_date !== null
                            ? formatDateIso(focusedStat.last_date)
                            : "Not observed",
                      },
                      { label: "Active days", value: formatCount(focusedStat.active_days) },
                      { label: "Window rows", value: formatCount(focusedStat.total_rows) },
                      {
                        label: "Observed rows",
                        value: `${formatCount(focusedObservedRows)} (${formatPct(
                          focusedStat.available_pct - focusedStat.imputed_pct
                        )})`,
                      },
                      {
                        label: "Imputed rows",
                        value: `${formatCount(focusedStat.imputed_rows)} (${formatPct(
                          focusedStat.imputed_pct
                        )})`,
                      },
                      {
                        label: "Missing rows",
                        value: `${formatCount(focusedStat.unavailable_rows)} (${formatPct(
                          focusedMissingPct
                        )})`,
                      },
                    ]}
                  />
                  <div className="rounded-panel border border-rule bg-surface p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-muted">
                      Availability bar — share of window rows
                    </p>
                    <div
                      aria-hidden="true"
                      className="mt-3 flex h-4 overflow-hidden rounded-control border border-rule bg-surface-raised"
                    >
                      <div
                        className="bg-success"
                        style={{
                          width: `${Math.max(0, focusedStat.available_pct - focusedStat.imputed_pct)}%`,
                        }}
                      />
                      <div
                        className="bg-warning"
                        style={{ width: `${focusedStat.imputed_pct}%` }}
                      />
                      <div
                        className="bg-surface-raised"
                        style={{ width: `${focusedMissingPct}%` }}
                      />
                    </div>
                    <ul className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
                      <li className="flex items-center gap-2 text-ink-2">
                        <span
                          aria-hidden="true"
                          className="inline-block h-3 w-3 shrink-0 rounded-sm border border-rule bg-success"
                        />
                        <span>
                          Observed {formatPct(focusedStat.available_pct - focusedStat.imputed_pct)}
                        </span>
                      </li>
                      <li className="flex items-center gap-2 text-ink-2">
                        <span
                          aria-hidden="true"
                          className="inline-block h-3 w-3 shrink-0 rounded-sm border border-rule bg-warning"
                        />
                        <span>Imputed {formatPct(focusedStat.imputed_pct)}</span>
                      </li>
                      <li className="flex items-center gap-2 text-ink-2">
                        <span
                          aria-hidden="true"
                          className="inline-block h-3 w-3 shrink-0 rounded-sm border border-rule-strong bg-surface-raised"
                        />
                        <span>Missing {formatPct(focusedMissingPct)}</span>
                      </li>
                    </ul>
                    <p className="mt-3 text-xs leading-relaxed text-muted">
                      Imputed segments are pipeline-filled gaps flagged is_imputed; missing
                      segments are absences with no recorded price.
                    </p>
                  </div>
                </div>
              ) : null}
            </section>

            <section aria-labelledby="model-honesty" className="space-y-3">
              <SectionHeading id="model-honesty">Model selection honesty</SectionHeading>
              <p className="max-w-3xl text-base leading-7 text-ink-2">
                Held-out test error decides what ships. The 7-day moving-average baseline
                beats every learned candidate on the test split, so only the baseline
                ships to the forecast route.
              </p>
              {honestState.status === "error" ? (
                <StatusNotice tone="danger" title="Model metrics did not load">
                  <p className="break-words">
                    Expected artifact web/public/data/honest_results.json failed to load
                    ({honestState.error}). The comparison below is omitted entirely rather
                    than shown as zeros.
                  </p>
                  {REGEN_HINT}
                </StatusNotice>
              ) : honestState.status === "loading" ? (
                <div role="status" aria-busy="true">
                  <span className="sr-only">Loading held-out model comparison…</span>
                  <div
                    aria-hidden="true"
                    className="h-40 w-full animate-pulse rounded-panel bg-paper-2"
                  />
                </div>
              ) : (
                <>
                  <HonestResultsTable results={honestState.data} />
                  <p className="text-sm leading-relaxed text-ink-2">
                    LightGBM variants did not beat the moving-average baseline on the
                    held-out split, so they are not shipped.
                  </p>
                </>
              )}
            </section>

            <section aria-labelledby="mandi-locations" className="space-y-3">
              <SectionHeading id="mandi-locations">Mandi locations</SectionHeading>
              <p className="max-w-3xl text-base leading-7 text-ink-2">
                Geographic spread of the in-scope mandis. Distances used elsewhere in the
                app apply the road-distance factor described in the method summary.
              </p>
              <Panel className="overflow-hidden p-2 sm:p-3">
                <MandiMap mandis={mandis} />
              </Panel>
            </section>

            <section aria-labelledby="provenance-links" className="space-y-3">
              <SectionHeading id="provenance-links">Where these numbers come from</SectionHeading>
              <ul className="space-y-3 text-sm leading-relaxed text-ink-2">
                <li>
                  <TextLink href="/#method">Method summary</TextLink> — how source prices
                  become forecasts, intervals, and rankings.
                </li>
                <li>
                  Modeling reports are committed in this repository under{" "}
                  <code className="numeric">reports/modeling/</code>, including{" "}
                  <code className="numeric">baseline_metrics_7d.md</code> and{" "}
                  <code className="numeric">lightgbm_metrics_7d.md</code>.
                </li>
                <li>
                  <TextLink href="/recommend/">Decision workbench</TextLink> — apply the
                  transport-adjusted ranking to a delivery decision.
                </li>
              </ul>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
