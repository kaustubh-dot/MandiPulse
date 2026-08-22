import { addDaysIso } from "@/lib/policy";
import type { RankedMandi } from "@/lib/types";

interface Props {
  rows: RankedMandi[];
  forecastHorizonDays: number;
  confidenceLevel: number;
  quantityQtl: number;
}

const RISK_BADGE: Record<string, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-red-100 text-red-800",
};

function rankReason(rank: number): string {
  if (rank === 1) {
    return "Rank 1: highest risk-adjusted net price among the eligible mandis.";
  }
  return `Rank ${rank}: next-best risk-adjusted net price after transport and uncertainty penalties.`;
}

export default function TopRecommendations({
  rows,
  forecastHorizonDays,
  confidenceLevel,
  quantityQtl,
}: Props) {
  const topRows = rows.slice(0, 3);
  if (topRows.length === 0) return null;

  return (
    <section
      aria-labelledby="top-recommendations-heading"
      aria-live="polite"
      className="space-y-3"
    >
      <div>
        <h2 id="top-recommendations-heading" className="text-lg font-semibold text-gray-900">
          Top recommendations
        </h2>
        <p className="mt-1 text-sm text-gray-600">
          Ranked by expected net price minus an uncertainty penalty. Prices are per quintal;
          lot estimates use {quantityQtl.toLocaleString()} qtl.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {topRows.map((row) => {
          const targetDate = addDaysIso(row.as_of_date, forecastHorizonDays);
          return (
            <article
              key={row.market_id}
              className={`mp-panel ${row.rank === 1 ? "border-green-400 ring-1 ring-green-200" : ""}`}
              aria-label={`Recommendation ${row.rank}: ${row.mandi}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    #{row.rank} recommendation
                  </p>
                  <h3 className="mt-1 text-base font-semibold text-gray-900">{row.mandi}</h3>
                  <p className="text-xs text-gray-500">{row.district_name}</p>
                </div>
                <span
                  className={`rounded-full px-2 py-1 text-xs font-semibold ${RISK_BADGE[row.risk_level] ?? "bg-gray-100 text-gray-800"}`}
                >
                  {row.risk_level} risk
                </span>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <div>
                  <dt className="text-xs text-gray-500">Forecast</dt>
                  <dd className="font-semibold">{row.forecast_price_inr_qtl.toFixed(0)} INR/qtl</dd>
                  <dd className="text-xs text-gray-500">
                    target {targetDate} · as-of {row.as_of_date}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">{(confidenceLevel * 100).toFixed(0)}% interval</dt>
                  <dd className="font-semibold">
                    {row.lower_bound_inr_qtl.toFixed(0)}–{row.upper_bound_inr_qtl.toFixed(0)}
                  </dd>
                  <dd className="text-xs text-gray-500">not a guarantee</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Transport</dt>
                  <dd className="font-semibold">{row.estimated_transport_cost_inr_qtl.toFixed(0)} INR/qtl</dd>
                  <dd className="text-xs text-gray-500">{row.road_distance_km.toFixed(0)} road km</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Net estimate</dt>
                  <dd className="font-semibold">{row.expected_net_price_inr_qtl.toFixed(0)} INR/qtl</dd>
                  <dd className="text-xs text-gray-500">
                    {Math.round(row.expected_net_price_inr_qtl * quantityQtl).toLocaleString()} INR/lot
                  </dd>
                </div>
                <div className="col-span-2 border-t border-gray-100 pt-3">
                  <dt className="text-xs text-gray-500">Uncertainty penalty</dt>
                  <dd className="font-semibold">{row.uncertainty_penalty_inr_qtl.toFixed(0)} INR/qtl</dd>
                </div>
              </dl>
              <p className="mt-4 text-xs leading-5 text-gray-600">{rankReason(row.rank)}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
