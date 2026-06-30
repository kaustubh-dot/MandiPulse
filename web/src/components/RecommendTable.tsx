import type { RankedMandi } from "@/lib/types";

interface Props {
  rows: RankedMandi[];
}

const RISK_BADGE: Record<string, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-red-100 text-red-800",
};

export default function RecommendTable({ rows }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left text-xs text-gray-600">
            <th className="px-2 py-2 border border-gray-200">#</th>
            <th className="px-2 py-2 border border-gray-200">Mandi</th>
            <th className="px-2 py-2 border border-gray-200 text-right">
              Forecast (INR/qtl)
            </th>
            <th className="px-2 py-2 border border-gray-200 text-right">
              Transport (INR/qtl)
            </th>
            <th className="px-2 py-2 border border-gray-200 text-right">
              Net Price (INR/qtl)
            </th>
            <th className="px-2 py-2 border border-gray-200 text-right">
              Risk-adj Score
            </th>
            <th className="px-2 py-2 border border-gray-200 text-center">Risk</th>
            <th className="px-2 py-2 border border-gray-200 text-right">
              Road km
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.market_id} className={r.rank === 1 ? "bg-green-50 font-medium" : ""}>
              <td className="px-2 py-2 border border-gray-200 text-center">{r.rank}</td>
              <td className="px-2 py-2 border border-gray-200">
                {r.mandi}
                <span className="block text-xs text-gray-400">{r.district_name}</span>
              </td>
              <td className="px-2 py-2 border border-gray-200 text-right">
                {r.forecast_price_inr_qtl.toFixed(0)}
              </td>
              <td className="px-2 py-2 border border-gray-200 text-right">
                {r.estimated_transport_cost_inr_qtl.toFixed(0)}
              </td>
              <td className="px-2 py-2 border border-gray-200 text-right font-medium">
                {r.expected_net_price_inr_qtl.toFixed(0)}
              </td>
              <td className="px-2 py-2 border border-gray-200 text-right">
                {r.risk_adjusted_score.toFixed(0)}
              </td>
              <td className="px-2 py-2 border border-gray-200 text-center">
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_BADGE[r.risk_level] ?? ""}`}
                >
                  {r.risk_level}
                </span>
              </td>
              <td className="px-2 py-2 border border-gray-200 text-right text-gray-500">
                {r.road_distance_km.toFixed(0)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
