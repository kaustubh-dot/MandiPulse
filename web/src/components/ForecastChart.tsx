"use client";

import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { buttonClass } from "@/components/ui/primitives";
import { EM_DASH, formatDateIso, formatInrPerQtl, formatInterval } from "@/lib/format";
import type { ForecastRow, PriceHistoryRow } from "@/lib/types";

const TABLE_ROW_CAP = 15;

// Recharts cannot resolve utility classes, so tokens are passed as CSS custom
// properties that resolve at runtime (theme-aware, light and dark).
const NUMERIC_TICK = {
  fontSize: 11,
  fontFamily: "var(--font-numeric), ui-monospace, monospace",
  fill: "var(--mp-muted)",
};

const SERIES_META: Record<string, { label: string; order: number }> = {
  observed: { label: "Observed", order: 0 },
  imputed: { label: "Imputed", order: 1 },
  forecast: { label: "Forecast", order: 2 },
};

interface ChartPoint {
  date: string;
  observed?: number;
  imputed?: number;
  forecast?: number;
  band?: [number, number];
}

interface TooltipPayloadEntry {
  dataKey?: string | number;
  value?: unknown;
  name?: string;
}

function SeriesTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string | number;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const seriesEntries = payload
    .filter(
      (entry): entry is TooltipPayloadEntry & { dataKey: string; value: number } =>
        typeof entry.dataKey === "string" &&
        entry.dataKey in SERIES_META &&
        typeof entry.value === "number" &&
        Number.isFinite(entry.value)
    )
    .sort(
      (a, b) => SERIES_META[a.dataKey].order - SERIES_META[b.dataKey].order
    );

  const rawBand = payload.find((entry) => entry.dataKey === "band");
  const bandValue =
    rawBand && Array.isArray(rawBand.value)
      ? (rawBand.value as [number, number])
      : null;

  return (
    <div
      className="max-w-[17rem] text-xs"
      style={{
        background: "var(--mp-surface)",
        border: "1px solid var(--mp-rule-strong)",
        borderRadius: "var(--radius-panel)",
        padding: "0.5rem 0.625rem",
      }}
    >
      <p className="numeric font-semibold text-ink">{formatDateIso(String(label))}</p>
      <dl className="mt-1 space-y-1">
        {seriesEntries.map((entry) => (
          <div key={entry.dataKey} className="flex items-baseline justify-between gap-3">
            <dt className="text-ink-2">{SERIES_META[entry.dataKey].label}</dt>
            <dd className="numeric text-ink">{formatInrPerQtl(entry.value)}</dd>
          </div>
        ))}
        {bandValue ? (
          <div className="flex items-baseline justify-between gap-3 border-t border-rule pt-1">
            <dt className="text-ink-2">Prediction interval</dt>
            <dd className="numeric text-ink">
              {formatInterval(bandValue[0], bandValue[1])}
            </dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}

function NumericCell({ value }: { value: number | undefined }) {
  return (
    <td className="numeric px-3 py-1.5 text-right text-xs text-ink">
      {typeof value === "number" && Number.isFinite(value)
        ? value.toLocaleString("en-US")
        : EM_DASH}
    </td>
  );
}

interface Props {
  history: PriceHistoryRow[]; // filtered to the selected mandi, capped to the 90-day window ending at as-of
  forecast: ForecastRow | null;
  forecastDate: string | null;
}

export default function ForecastChart({ history, forecast, forecastDate }: Props) {
  const [view, setView] = useState<"chart" | "table">("chart");

  const points = useMemo<ChartPoint[]>(() => {
    const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
    const built: ChartPoint[] = sorted.map((row) => {
      const value = Number(row.modal_price_inr_qtl);
      return row.is_imputed
        ? { date: row.date, imputed: value }
        : { date: row.date, observed: value };
    });

    if (forecast && forecastDate) {
      // Flat band across the forecast window (as-of -> target); the bounds
      // themselves apply to the target date only. Stated in caption + tooltip.
      const band: [number, number] = [
        forecast.lower_bound_inr_qtl,
        forecast.upper_bound_inr_qtl,
      ];
      const bridge = built.find((point) => point.date === forecast.as_of_date);
      if (bridge) {
        bridge.forecast = forecast.forecast_price_inr_qtl;
        bridge.band = band;
      } else {
        built.push({
          date: forecast.as_of_date,
          forecast: forecast.forecast_price_inr_qtl,
          band,
        });
      }
      built.push({
        date: forecastDate,
        forecast: forecast.forecast_price_inr_qtl,
        band,
      });
    }

    return built;
  }, [history, forecast, forecastDate]);

  if (points.length === 0) return null;

  const observedCount = points.filter((point) => point.observed !== undefined).length;
  const imputedCount = points.filter((point) => point.imputed !== undefined).length;
  const hasImputed = imputedCount > 0;
  const tablePoints = points.slice(-TABLE_ROW_CAP);

  const intervalPart =
    forecast && forecastDate
      ? `, ending in a dashed forecast segment for ${formatDateIso(forecastDate)} at ${formatInrPerQtl(forecast.forecast_price_inr_qtl)} with a shaded prediction interval of ${formatInterval(forecast.lower_bound_inr_qtl, forecast.upper_bound_inr_qtl)}`
      : "";
  const chartAriaLabel = `Price line chart: ${observedCount} observed daily prices${hasImputed ? `, ${imputedCount} imputed fills drawn as hollow markers` : ""}${intervalPart}. Select \u201cView as table\u201d for exact figures.`;

  return (
    <div className="min-w-0 space-y-3">
      <div className="flex justify-end">
        <button
          type="button"
          className={buttonClass.secondary}
          aria-pressed={view === "table"}
          onClick={() =>
            setView((current) => (current === "chart" ? "table" : "chart"))
          }
        >
          {view === "chart" ? "View as table" : "View as chart"}
        </button>
      </div>

      {view === "chart" ? (
        <div
          className="h-[320px] w-full min-w-0"
          role="img"
          aria-label={chartAriaLabel}
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
            initialDimension={{ width: 600, height: 320 }}
          >
            <ComposedChart data={points} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
              <CartesianGrid
                stroke="var(--mp-rule)"
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tickFormatter={formatDateIso}
                tick={NUMERIC_TICK}
                tickLine={false}
                axisLine={{ stroke: "var(--mp-rule-strong)" }}
                interval="preserveStartEnd"
                minTickGap={32}
              />
              <YAxis
                tick={NUMERIC_TICK}
                tickLine={false}
                axisLine={false}
                width={56}
                label={{
                  value: "INR/quintal",
                  angle: -90,
                  position: "insideLeft",
                  style: { fontSize: 11, fill: "var(--mp-muted)" },
                }}
              />
              <Area
                dataKey="band"
                name="Prediction interval"
                stroke="none"
                fill="var(--mp-accent)"
                fillOpacity={0.35}
                legendType="rect"
                activeDot={false}
                isAnimationActive={false}
              />
              <Line
                dataKey="observed"
                name="Observed"
                stroke="var(--mp-ink)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "var(--mp-ink)" }}
                isAnimationActive={false}
              />
              {hasImputed ? (
                <Line
                  dataKey="imputed"
                  name="Imputed"
                  stroke="var(--mp-ink-2)"
                  strokeWidth={0}
                  dot={{
                    r: 3.5,
                    fill: "var(--mp-surface-raised)",
                    stroke: "var(--mp-ink)",
                    strokeWidth: 1.5,
                  }}
                  activeDot={false}
                  legendType="circle"
                  isAnimationActive={false}
                />
              ) : null}
              <Line
                dataKey="forecast"
                name="Forecast"
                stroke="var(--mp-accent)"
                strokeWidth={2.5}
                strokeDasharray="7 4"
                dot={{
                  r: 5,
                  fill: "var(--mp-accent)",
                  stroke: "var(--mp-accent-ink)",
                  strokeWidth: 1,
                }}
                activeDot={{
                  r: 6,
                  fill: "var(--mp-accent)",
                  stroke: "var(--mp-accent-ink)",
                  strokeWidth: 1,
                }}
                isAnimationActive={false}
              />
              <Tooltip
                content={<SeriesTooltip />}
                cursor={{ stroke: "var(--mp-rule-strong)", strokeDasharray: "3 3" }}
              />
              <Legend iconSize={10} wrapperStyle={{ fontSize: "0.75rem" }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div
          className="overflow-x-auto border-y border-rule bg-transparent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
          role="region"
          aria-label="Chart series as a data table"
          tabIndex={0}
        >
          <table className="w-full min-w-[620px] border-collapse text-sm">
            <caption className="border-b border-rule px-3 py-2 text-left text-xs text-muted">
              Daily prices underlying the chart, most recent {tablePoints.length} of{" "}
              {points.length} days. Values are INR/qtl; interval bounds apply to the
              forecast target date.
            </caption>
            <thead>
              <tr className="bg-paper-2 text-left text-xs text-ink-2">
                <th scope="col" className="px-3 py-2 font-bold">
                  Date
                </th>
                <th scope="col" className="px-3 py-2 text-right font-bold">
                  Observed (INR/qtl)
                </th>
                <th scope="col" className="px-3 py-2 text-right font-bold">
                  Imputed (INR/qtl)
                </th>
                <th scope="col" className="px-3 py-2 text-right font-bold">
                  Forecast (INR/qtl)
                </th>
                <th scope="col" className="px-3 py-2 text-right font-bold">
                  Lower bound (INR/qtl)
                </th>
                <th scope="col" className="px-3 py-2 text-right font-bold">
                  Upper bound (INR/qtl)
                </th>
              </tr>
            </thead>
            <tbody>
              {tablePoints.map((point) => (
                <tr key={point.date} className="border-t border-rule">
                  <td className="numeric whitespace-nowrap px-3 py-1.5 text-left text-xs text-ink-2">
                    {formatDateIso(point.date)}
                  </td>
                  <NumericCell value={point.observed} />
                  <NumericCell value={point.imputed} />
                  <NumericCell value={point.forecast} />
                  <NumericCell value={point.band?.[0]} />
                  <NumericCell value={point.band?.[1]} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
