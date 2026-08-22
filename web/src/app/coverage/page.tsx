"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import { EmptyState, ErrorState, LoadingState } from "@/components/DataState";
import SampleBanner from "@/components/SampleBanner";
import { loadMandis, loadMeta, loadPriceHistory } from "@/lib/data";
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
  available_rows: number;
  imputed_rows: number;
  unavailable_rows: number;
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

    return {
      market_id: mandi.market_id,
      market_name: mandi.market_name,
      first_date: dates[0] ?? null,
      last_date: dates[dates.length - 1] ?? null,
      active_days: mandi.active_days,
      available_rows: availableRows.length,
      imputed_rows: availableRows.filter((row) => row.is_imputed).length,
      unavailable_rows: unavailableRows,
      unavailable_pct: rows.length > 0 ? (unavailableRows / rows.length) * 100 : 100,
    };
  });
}

export default function CoveragePage() {
  const state = useAsyncData(loadCoverageBundle);
  const stats = useMemo(
    () => (state.status === "success" ? computeStats(state.data.history, state.data.mandis) : []),
    [state]
  );

  if (state.status === "loading") {
    return <LoadingState label="Loading coverage, mandi metadata, and price history…" />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.error} onRetry={state.retry} />;
  }

  const { meta, mandis, history } = state.data;
  const totalMandiDays = stats.reduce((sum, row) => sum + row.available_rows, 0);
  const isEmpty = mandis.length === 0 || history.length === 0 || totalMandiDays === 0;

  return (
    <div className="space-y-6">
      <SampleBanner asOfDate={meta.snapshot_date} />

      <div>
        <h1 className="mb-1 text-xl font-bold">Data Coverage</h1>
        <p className="text-sm text-gray-500">
          Maharashtra Onion — top 15 mandis by historical coverage
        </p>
      </div>

      {isEmpty ? (
        <EmptyState
          title="No coverage data is available"
          detail="The snapshot loaded, but it contains no finite historical price observations."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
            <div className="rounded border border-gray-200 bg-white p-4">
              <div className="mb-1 text-xs text-gray-500">Mandis tracked</div>
              <div className="text-2xl font-semibold">{mandis.length}</div>
            </div>
            <div className="rounded border border-gray-200 bg-white p-4">
              <div className="mb-1 text-xs text-gray-500">Available mandi-days</div>
              <div className="text-2xl font-semibold">{totalMandiDays.toLocaleString()}</div>
            </div>
            <div className="rounded border border-gray-200 bg-white p-4">
              <div className="mb-1 text-xs text-gray-500">Snapshot date</div>
              <div className="break-words text-2xl font-semibold">{meta.snapshot_date}</div>
            </div>
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold text-gray-700">Per-mandi coverage</h2>
            <div
              className="overflow-x-auto rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
              role="region"
              aria-label="Per-mandi data coverage"
              tabIndex={0}
            >
              <table className="min-w-[760px] w-full border-collapse text-sm">
                <caption className="sr-only">
                  Available and unavailable historical price coverage for each mandi
                </caption>
                <thead>
                  <tr className="bg-gray-100 text-left text-xs text-gray-600">
                    <th className="border border-gray-200 px-3 py-2">Mandi</th>
                    <th className="border border-gray-200 px-3 py-2">First available date</th>
                    <th className="border border-gray-200 px-3 py-2">Last available date</th>
                    <th className="border border-gray-200 px-3 py-2">Freshness</th>
                    <th className="border border-gray-200 px-3 py-2 text-right">Active days</th>
                    <th className="border border-gray-200 px-3 py-2 text-right">Unavailable %</th>
                  </tr>
                </thead>
                <tbody>
                  {[...stats]
                    .sort((a, b) => b.active_days - a.active_days)
                    .map((row) => {
                      const staleDays = row.last_date
                        ? daysBehind(row.last_date, meta.snapshot_date)
                        : null;
                      return (
                        <tr key={row.market_id}>
                          <td className="border border-gray-200 px-3 py-2 font-medium">
                            {row.market_name}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-xs text-gray-500">
                            {row.first_date ?? "Unavailable"}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-xs text-gray-500">
                            {row.last_date ?? "Unavailable"}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-xs">
                            {staleDays === null ? (
                              <span className="font-medium text-red-700">No observations</span>
                            ) : staleDays === 0 ? (
                              <span className="font-medium text-green-700">Current snapshot</span>
                            ) : (
                              <span className="font-medium text-amber-700">{staleDays}d behind</span>
                            )}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-right">
                            {row.active_days.toLocaleString()}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-right">
                            <span
                              className={
                                row.unavailable_pct > 20
                                  ? "font-medium text-red-700"
                                  : row.unavailable_pct > 5
                                    ? "text-amber-700"
                                    : "text-green-700"
                              }
                            >
                              {row.unavailable_pct.toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold text-gray-700">Mandi locations</h2>
            <MandiMap mandis={mandis} />
          </div>
        </>
      )}
    </div>
  );
}
