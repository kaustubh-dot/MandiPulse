import { formatDateIso, formatInrPerQtl, formatKm } from "@/lib/format";
import type { RankedMandi } from "@/lib/types";

interface Props {
  rows: RankedMandi[];
  canonicalAsOfDate: string;
}

const RISK_TEXT: Record<string, { word: string; cls: string }> = {
  low: { word: "Low", cls: "text-success" },
  medium: { word: "Medium", cls: "text-warning" },
  high: { word: "High", cls: "text-danger" },
};

const HEAD_CLASS =
  "whitespace-nowrap px-3 py-2 text-left text-xs font-semibold text-muted";
const NUM_HEAD_CLASS =
  "whitespace-nowrap px-3 py-2 text-right text-xs font-semibold text-muted";
const CELL_CLASS = "px-3 py-2.5 align-top text-ink-2";
const NUM_CELL_CLASS = "numeric px-3 py-2.5 text-right text-ink";

export default function RecommendTable({ rows, canonicalAsOfDate }: Props) {
  return (
    <div className="space-y-4">
      {/* Mobile record list */}
      <ol
        aria-label="Eligible mandis as records"
        className="divide-y divide-rule border-y border-rule md:hidden"
      >
        {rows.map((row) => {
          const risk =
            RISK_TEXT[row.risk_level] ?? { word: "Unknown", cls: "text-ink-2" };
          const isTop = row.rank === 1;
          return (
            <li
              key={row.market_id}
              className={`py-3 ${isTop ? "bg-paper-2 -mx-4 px-4" : ""}`}
            >
              <div className="flex items-baseline justify-between gap-2">
                <div>
                  <span className="numeric text-xs font-semibold text-muted">
                    #{row.rank}
                  </span>{" "}
                  <span className="font-semibold text-ink">{row.mandi}</span>
                  <span className="ml-2 text-xs text-muted">{row.district_name}</span>
                </div>
                <span className={`text-xs font-semibold ${risk.cls}`}>
                  {risk.word}
                </span>
              </div>
              <div className="mt-1 flex items-baseline justify-between text-xs text-muted">
                <span>
                  Forecast {formatInrPerQtl(row.forecast_price_inr_qtl)} &middot; {formatKm(row.road_distance_km, 0)} road
                </span>
                <span className="numeric text-sm font-semibold text-ink">
                  {formatInrPerQtl(row.transport_adjusted_net_price_inr_qtl)}
                </span>
              </div>
            </li>
          );
        })}
      </ol>

      {/* Desktop comparison table */}
      <div
        role="region"
        aria-label="All eligible mandis, ranked comparison"
        tabIndex={0}
        className="hidden md:block overflow-x-auto border-y border-rule bg-transparent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <table className="w-full min-w-[840px] border-collapse text-sm">
          <caption className="sr-only">
            Eligible mandis ranked by transport-adjusted net expected price for the
            forecast as-of date {formatDateIso(canonicalAsOfDate)}. The shaded row is the
            rank-1 recommendation.
          </caption>
          <thead>
            <tr className="border-b border-rule bg-paper-2">
              <th scope="col" className={NUM_HEAD_CLASS}>
                Rank
              </th>
              <th scope="col" className={HEAD_CLASS}>
                Mandi
              </th>
              <th scope="col" className={HEAD_CLASS}>
                District
              </th>
              <th scope="col" className={HEAD_CLASS}>
                As-of
              </th>
              <th scope="col" className={NUM_HEAD_CLASS}>
                Forecast (INR/qtl)
              </th>
              <th scope="col" className={NUM_HEAD_CLASS}>
                Transport (INR/qtl)
              </th>
              <th scope="col" className={NUM_HEAD_CLASS}>
                Net price (INR/qtl)
              </th>
              <th scope="col" className={NUM_HEAD_CLASS}>
                Distance (road, km)
              </th>
              <th scope="col" className={HEAD_CLASS}>
                Risk
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {rows.map((row) => {
              const risk =
                RISK_TEXT[row.risk_level] ?? { word: "Unknown", cls: "text-ink-2" };
              return (
                <tr key={row.market_id} className={row.rank === 1 ? "bg-paper-2" : undefined}>
                  <td className={`${NUM_CELL_CLASS} font-semibold`}>{row.rank}</td>
                  <td className={`${CELL_CLASS} font-semibold text-ink`}>{row.mandi}</td>
                  <td className={CELL_CLASS}>{row.district_name}</td>
                  <td className={`${NUM_CELL_CLASS} whitespace-nowrap`}>
                    {formatDateIso(row.as_of_date)}
                  </td>
                  <td className={NUM_CELL_CLASS}>
                    {formatInrPerQtl(row.forecast_price_inr_qtl)}
                  </td>
                  <td className={NUM_CELL_CLASS}>
                    {formatInrPerQtl(row.estimated_transport_cost_inr_qtl)}
                  </td>
                  <td className={`${NUM_CELL_CLASS} font-semibold text-accent`}>
                    {formatInrPerQtl(row.transport_adjusted_net_price_inr_qtl)}
                  </td>
                  <td className={NUM_CELL_CLASS}>{formatKm(row.road_distance_km, 0)}</td>
                  <td className={CELL_CLASS}>
                    <span className={`text-xs font-semibold ${risk.cls}`}>
                      {risk.word}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
