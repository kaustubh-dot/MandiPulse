import { addDaysIso } from "@/lib/policy";
import {
  formatDateIso,
  formatInr,
  formatInrPerQtl,
  formatInterval,
  formatKm,
  formatPct,
  formatQuantity,
} from "@/lib/format";
import { SectionHeading } from "@/components/ui/primitives";
import type { RankedMandi } from "@/lib/types";

interface Props {
  rows: RankedMandi[];
  forecastHorizonDays: number;
  confidenceLevel: number;
  quantityQtl: number;
}

const RISK_TEXT: Record<string, { word: string; cls: string }> = {
  low: { word: "Low", cls: "text-success" },
  medium: { word: "Medium", cls: "text-warning" },
  high: { word: "High", cls: "text-danger" },
};

const FALLBACK_RISK = { word: "Uncertain", cls: "text-ink-2" };

export default function TopRecommendations({
  rows,
  forecastHorizonDays,
  confidenceLevel,
  quantityQtl,
}: Props) {
  const top = rows[0];
  if (!top) return null;

  const alternates = rows.slice(1, 3);
  const targetDate = addDaysIso(top.as_of_date, forecastHorizonDays);
  const netPerQtl = top.transport_adjusted_net_price_inr_qtl;
  const lotNet = netPerQtl * quantityQtl;
  const staleDays = top.staleness_days ?? 0;
  const risk = RISK_TEXT[top.risk_level] ?? FALLBACK_RISK;
  const intervalLabel = `${formatPct(confidenceLevel * 100, 0)} interval`;

  return (
    <section aria-labelledby="recommended-mandi-heading" className="space-y-6">
      <SectionHeading id="recommended-mandi-heading">Recommended mandi</SectionHeading>

      <article aria-label="Rank 1 recommendation" className="border-y border-rule py-6">
        <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="numeric text-sm text-muted">Rank 1 of {rows.length}</p>
              <span className="text-muted" aria-hidden="true">&middot;</span>
              <span className={`text-sm font-semibold ${risk.cls}`}>
                {risk.word} risk
              </span>
            </div>
            <h3 className="mt-2 font-display text-5xl font-normal leading-none text-ink">
              {top.mandi}
            </h3>
            <p className="mt-2 text-sm text-ink-2">{top.district_name}</p>
          </div>
          <div className="md:text-right">
            <p className="text-sm text-muted">Transport-adjusted net price</p>
            <p className="numeric mt-1 text-3xl font-semibold text-accent">
              {formatInrPerQtl(netPerQtl)}
            </p>
          </div>
        </div>

        <dl className="mt-6 flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div>
            <dt className="text-xs text-muted">Sale target date</dt>
            <dd className="numeric font-semibold text-ink">{formatDateIso(targetDate)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Forecast as-of</dt>
            <dd className="numeric font-semibold text-ink">{formatDateIso(top.as_of_date)}</dd>
          </div>
        </dl>

        {staleDays > 0 ? (
          <p className="mt-4 text-sm font-semibold text-warning">
            This forecast is {staleDays} {staleDays === 1 ? "day" : "days"} behind the
            current snapshot window.
          </p>
        ) : null}

        <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-rule pt-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted">Forecast price</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatInrPerQtl(top.forecast_price_inr_qtl)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">{intervalLabel}</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatInterval(top.lower_bound_inr_qtl, top.upper_bound_inr_qtl)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Transport cost</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatInrPerQtl(top.estimated_transport_cost_inr_qtl)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Expected net price</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatInrPerQtl(top.expected_net_price_inr_qtl)}
            </dd>
            <dd className="text-xs text-muted">Forecast minus transport cost</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Transport-adjusted net price</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatInrPerQtl(netPerQtl)}
            </dd>
            <dd className="text-xs text-muted">Basis of the ranking</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Lot net estimate</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">{formatInr(lotNet, 0)}</dd>
            <dd className="text-xs text-muted">For {formatQuantity(quantityQtl)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Road distance</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatKm(top.road_distance_km)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Air distance</dt>
            <dd className="numeric mt-0.5 font-semibold text-ink">
              {formatKm(top.air_distance_km)}
            </dd>
          </div>
        </dl>

        <p className="mt-4 border-t border-rule pt-3 text-sm leading-relaxed text-ink-2">
          Highest expected price after subtracting estimated transport from the frozen
          forecast.
        </p>
      </article>

      {alternates.length > 0 ? (
        <div className="space-y-3">
          <h3 className="font-display text-2xl font-normal text-ink">Alternative recommendations</h3>
          <ol aria-label="Alternative recommendations" className="divide-y divide-rule border-y border-rule">
            {alternates.map((alt) => {
              const diff = alt.transport_adjusted_net_price_inr_qtl - netPerQtl;
              const altRisk = RISK_TEXT[alt.risk_level] ?? FALLBACK_RISK;
              return (
                <li
                  key={alt.market_id}
                  className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-3"
                >
                  <div>
                    <p className="text-base font-semibold text-ink">
                      <span className="numeric mr-2 text-muted">#{alt.rank}</span>
                      {alt.mandi}
                    </p>
                    <p className="text-xs text-muted">{alt.district_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="numeric text-base font-semibold text-ink">
                      {formatInrPerQtl(alt.transport_adjusted_net_price_inr_qtl)}
                    </p>
                    <p className="text-xs text-muted">
                      {formatInrPerQtl(diff)} vs rank 1 &middot;{" "}
                      {formatKm(alt.road_distance_km, 0)} road &middot;{" "}
                      <span className={`font-semibold ${altRisk.cls}`}>{altRisk.word} risk</span>
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      ) : null}
    </section>
  );
}
