"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { buttonClass } from "@/components/ui/primitives";
import {
  buildForecastChartModel,
  formatForecastDateTick,
  formatForecastPriceTick,
} from "@/lib/forecastChart";
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
  price: { label: "Observed", order: 0 },
  imputed: { label: "Imputed", order: 1 },
};

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

  const typedEntries = payload
    .filter(
      (entry): entry is TooltipPayloadEntry & { dataKey: string; value: number } =>
        typeof entry.dataKey === "string" &&
        entry.dataKey in SERIES_META &&
        typeof entry.value === "number" &&
        Number.isFinite(entry.value)
    );
  const hasImputedEntry = typedEntries.some((entry) => entry.dataKey === "imputed");
  const seriesEntries = typedEntries
    .filter((entry) => !(hasImputedEntry && entry.dataKey === "price"))
    .sort(
      (a, b) => SERIES_META[a.dataKey].order - SERIES_META[b.dataKey].order
    );

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
      </dl>
    </div>
  );
}

function domainPosition(value: number, domain: [number, number]): number {
  const [minimum, maximum] = domain;
  if (maximum <= minimum) return 50;
  return Math.min(100, Math.max(0, ((value - minimum) / (maximum - minimum)) * 100));
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

  const model = useMemo(
    () => buildForecastChartModel(history, forecast, forecastDate),
    [history, forecast, forecastDate]
  );

  if (model.historyPoints.length === 0 && !model.endpoint) return null;

  const observedCount = model.historyPoints.filter(
    (point) => point.imputed === undefined
  ).length;
  const imputedCount = model.historyPoints.filter(
    (point) => point.imputed !== undefined
  ).length;
  const hasImputed = imputedCount > 0;
  const tablePoints = model.tablePoints.slice(-TABLE_ROW_CAP);

  const intervalPart =
    model.endpoint
      ? `. A separate forecast endpoint lane shows ${formatDateIso(model.endpoint.date)} at ${formatInrPerQtl(model.endpoint.forecast)} with a target-date prediction interval of ${formatInterval(model.endpoint.lower, model.endpoint.upper)}`
      : "";
  const chartAriaLabel = `Price line chart: ${observedCount} observed daily prices${hasImputed ? `, ${imputedCount} imputed fills drawn as hollow markers` : ""}${intervalPart}. Select \u201cView as table\u201d for exact figures.`;

  const lowerPosition = model.endpoint
    ? domainPosition(model.endpoint.lower, model.yDomain)
    : 0;
  const upperPosition = model.endpoint
    ? domainPosition(model.endpoint.upper, model.yDomain)
    : 0;
  const forecastPosition = model.endpoint
    ? domainPosition(model.endpoint.forecast, model.yDomain)
    : 0;

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
        <div className="space-y-3">
          <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-ink-2">
            <span className="inline-flex items-center gap-2">
              <span className="w-5 border-t-2 border-ink" aria-hidden="true" />
              Observed price
            </span>
            {hasImputed ? (
              <span className="inline-flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full border-2 border-ink bg-surface"
                  aria-hidden="true"
                />
                Imputed value
              </span>
            ) : null}
            {model.endpoint ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-4 w-px bg-accent" aria-hidden="true" />
                Forecast and interval
              </span>
            ) : null}
          </div>

          <div
            className={
              model.endpoint
                ? "grid min-w-0 gap-5 md:grid-cols-[minmax(0,4fr)_minmax(9.5rem,1fr)]"
                : "min-w-0"
            }
          >
            <div className="min-w-0">
              <p className="mb-2 text-xs text-muted">Observed and imputed history</p>
              <div
                className="h-[320px] w-full min-w-0"
                role="img"
                aria-label={chartAriaLabel}
              >
                {model.historyPoints.length > 0 ? (
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                    initialDimension={{ width: 600, height: 320 }}
                  >
                    <ComposedChart
                      data={model.historyPoints}
                      margin={{ top: 8, right: 20, bottom: 4, left: 0 }}
                    >
                      <CartesianGrid stroke="var(--mp-rule)" vertical={false} />
                      <XAxis
                        dataKey="date"
                        tickFormatter={formatForecastDateTick}
                        tick={NUMERIC_TICK}
                        tickLine={false}
                        tickMargin={8}
                        axisLine={{ stroke: "var(--mp-rule-strong)" }}
                        interval="preserveStartEnd"
                        minTickGap={32}
                        padding={{ left: 8, right: 8 }}
                      />
                      <YAxis
                        domain={model.yDomain}
                        allowDataOverflow
                        tickFormatter={formatForecastPriceTick}
                        tick={NUMERIC_TICK}
                        tickLine={false}
                        axisLine={false}
                        width={58}
                      />
                      <Line
                        dataKey="price"
                        name="Observed and imputed history"
                        stroke="var(--mp-ink)"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4, fill: "var(--mp-ink)" }}
                        isAnimationActive={false}
                      />
                      {hasImputed ? (
                        <Line
                          dataKey="imputed"
                          name="Imputed value"
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
                      <Tooltip
                        content={<SeriesTooltip />}
                        cursor={{
                          stroke: "var(--mp-rule-strong)",
                          strokeDasharray: "3 3",
                        }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center border-y border-rule px-5 text-center text-sm text-muted">
                    No finite history is available in this window.
                  </div>
                )}
              </div>
            </div>

            {model.endpoint ? (
              <div
                className="min-w-0"
                role="group"
                aria-label={`Forecast endpoint for ${formatDateIso(model.endpoint.date)}`}
              >
                <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2 text-xs">
                  <span className="font-semibold text-ink">Forecast target</span>
                  <span className="numeric text-muted">
                    {formatDateIso(model.endpoint.date)}
                  </span>
                </div>
                <div className="relative h-[210px] border border-rule-strong bg-surface md:h-[320px]">
                  <p className="sr-only">
                    {Math.round(model.endpoint.confidenceLevel * 100)}% Prediction interval
                  </p>

                  <div
                    className="absolute left-1/2 w-8 -translate-x-1/2 bg-accent-soft"
                    style={{
                      bottom: `${lowerPosition}%`,
                      height: `${Math.max(0, upperPosition - lowerPosition)}%`,
                      background: "var(--mp-accent-soft)",
                    }}
                    aria-hidden="true"
                  />
                  <div
                    className="absolute left-1/2 w-px -translate-x-1/2 bg-accent"
                    style={{
                      bottom: `${lowerPosition}%`,
                      height: `${Math.max(0, upperPosition - lowerPosition)}%`,
                      background: "var(--mp-accent)",
                    }}
                    aria-hidden="true"
                  />
                  <div
                    className="absolute left-1/2 h-px w-6 -translate-x-1/2 bg-accent"
                    style={{ bottom: `${lowerPosition}%` }}
                    aria-hidden="true"
                  />
                  <div
                    className="absolute left-1/2 h-px w-6 -translate-x-1/2 bg-accent"
                    style={{ bottom: `${upperPosition}%` }}
                    aria-hidden="true"
                  />
                  <div
                    className="absolute left-1/2 h-3 w-3 -translate-x-1/2 translate-y-1/2 rounded-full bg-accent ring-2 ring-surface"
                    style={{
                      bottom: `${forecastPosition}%`,
                      background: "var(--mp-accent)",
                    }}
                    aria-hidden="true"
                  />

                  <p
                    className="numeric absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-semibold text-accent"
                    style={{ bottom: `calc(${forecastPosition}% + 0.75rem)` }}
                  >
                    {formatInrPerQtl(model.endpoint.forecast)}
                  </p>
                  <p
                    className="numeric absolute right-2 whitespace-nowrap text-[0.7rem] text-muted"
                    style={{ bottom: `calc(${upperPosition}% - 0.45rem)` }}
                  >
                    {formatInrPerQtl(model.endpoint.upper)}
                  </p>
                  <p
                    className="numeric absolute right-2 whitespace-nowrap text-[0.7rem] text-muted"
                    style={{ bottom: `calc(${lowerPosition}% - 0.45rem)` }}
                  >
                    {formatInrPerQtl(model.endpoint.lower)}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
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
              {model.tablePoints.length} rows. Values are INR/qtl; interval bounds
              apply to the forecast target date.
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
              {tablePoints.map((point, index) => (
                <tr key={`${point.date}-${index}`} className="border-t border-rule">
                  <td className="numeric whitespace-nowrap px-3 py-1.5 text-left text-xs text-ink-2">
                    {formatDateIso(point.date)}
                  </td>
                  <NumericCell value={point.observed} />
                  <NumericCell value={point.imputed} />
                  <NumericCell value={point.forecast} />
                  <NumericCell value={point.lower} />
                  <NumericCell value={point.upper} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
