"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import SampleBanner from "@/components/SampleBanner";
import { loadMeta, loadMandis, loadPriceHistory } from "@/lib/data";
import type { Meta, MandiMeta, PriceHistoryRow } from "@/lib/types";

const MandiMap = dynamic(() => import("@/components/MandiMap"), { ssr: false });

interface MandiStats {
  market_id: number;
  market_name: string;
  first_date: string;
  last_date: string;
  active_days: number;
  total_rows: number;
  imputed_rows: number;
  missing_pct: number;
}

function computeStats(
  history: PriceHistoryRow[],
  mandis: MandiMeta[]
): MandiStats[] {
  const grouped = new Map<number, PriceHistoryRow[]>();
  for (const r of history) {
    const bucket = grouped.get(r.market_id) ?? [];
    bucket.push(r);
    grouped.set(r.market_id, bucket);
  }

  return mandis.map((m) => {
    const rows = grouped.get(m.market_id) ?? [];
    const dates = rows.map((r) => r.date).sort();
    const imputedCount = rows.filter((r) => r.is_imputed).length;
    const total = rows.length;
    return {
      market_id: m.market_id,
      market_name: m.market_name,
      first_date: dates[0] ?? "–",
      last_date: dates[dates.length - 1] ?? "–",
      active_days: m.active_days,
      total_rows: total,
      imputed_rows: imputedCount,
      missing_pct: total > 0 ? parseFloat(((imputedCount / total) * 100).toFixed(1)) : 0,
    };
  });
}

export default function CoveragePage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [mandis, setMandis] = useState<MandiMeta[]>([]);
  const [stats, setStats] = useState<MandiStats[]>([]);

  useEffect(() => {
    Promise.all([loadMeta(), loadMandis(), loadPriceHistory()]).then(
      ([m, ms, history]) => {
        setMeta(m);
        setMandis(ms);
        setStats(computeStats(history, ms));
      }
    );
  }, []);

  const totalMandiDays = stats.reduce((s, r) => s + r.total_rows, 0);

  return (
    <div className="space-y-6">
      {meta && <SampleBanner asOfDate={meta.as_of_date} />}

      <div>
        <h1 className="text-xl font-bold mb-1">Data Coverage</h1>
        <p className="text-sm text-gray-500">
          Maharashtra Onion — top 15 mandis by historical coverage
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded p-4">
          <div className="text-xs text-gray-500 mb-1">Mandis tracked</div>
          <div className="text-2xl font-semibold">{mandis.length}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded p-4">
          <div className="text-xs text-gray-500 mb-1">Total mandi-days</div>
          <div className="text-2xl font-semibold">{totalMandiDays.toLocaleString()}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded p-4">
          <div className="text-xs text-gray-500 mb-1">Data as of</div>
          <div className="text-2xl font-semibold">{meta?.as_of_date ?? "–"}</div>
        </div>
      </div>

      {/* Per-mandi table */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-2">Per-mandi coverage</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100 text-left text-xs text-gray-600">
                <th className="px-3 py-2 border border-gray-200">Mandi</th>
                <th className="px-3 py-2 border border-gray-200">First date</th>
                <th className="px-3 py-2 border border-gray-200">Last date</th>
                <th className="px-3 py-2 border border-gray-200 text-right">Active days</th>
                <th className="px-3 py-2 border border-gray-200 text-right">Imputed %</th>
              </tr>
            </thead>
            <tbody>
              {stats
                .sort((a, b) => b.active_days - a.active_days)
                .map((r) => (
                  <tr key={r.market_id}>
                    <td className="px-3 py-2 border border-gray-200 font-medium">
                      {r.market_name}
                    </td>
                    <td className="px-3 py-2 border border-gray-200 text-gray-500 text-xs">
                      {r.first_date}
                    </td>
                    <td className="px-3 py-2 border border-gray-200 text-gray-500 text-xs">
                      {r.last_date}
                    </td>
                    <td className="px-3 py-2 border border-gray-200 text-right">
                      {r.active_days.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 border border-gray-200 text-right">
                      <span
                        className={
                          r.missing_pct > 20
                            ? "text-red-600 font-medium"
                            : r.missing_pct > 5
                            ? "text-yellow-600"
                            : "text-green-700"
                        }
                      >
                        {r.missing_pct}%
                      </span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Map */}
      {mandis.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Mandi locations</h2>
          <MandiMap mandis={mandis} />
        </div>
      )}
    </div>
  );
}
