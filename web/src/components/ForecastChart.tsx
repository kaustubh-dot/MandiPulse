"use client";

import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { PriceHistoryRow, ForecastRow } from "@/lib/types";

interface Props {
  history: PriceHistoryRow[]; // filtered to selected mandi, last 90 days
  forecast: ForecastRow | null;
}

interface ChartPoint {
  date: string;
  actual?: number;
  imputed?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
}

export default function ForecastChart({ history, forecast }: Props) {
  const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));

  const points: ChartPoint[] = sorted.map((r) => ({
    date: r.date.slice(5), // MM-DD display
    actual: r.is_imputed ? undefined : r.modal_price_inr_qtl,
    imputed: r.is_imputed ? r.modal_price_inr_qtl : undefined,
  }));

  if (forecast) {
    points.push({
      date: "Forecast",
      forecast: forecast.forecast_price_inr_qtl,
      lower: forecast.lower_bound_inr_qtl,
      upper: forecast.upper_bound_inr_qtl,
    });
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={points} margin={{ top: 4, right: 16, bottom: 4, left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11 }}
          label={{ value: "INR/qtl", angle: -90, position: "insideLeft", fontSize: 11 }}
        />
        <Tooltip formatter={(v) => (typeof v === "number" ? v.toFixed(0) : v)} />
        <Legend />
        {/* Uncertainty band — only visible on the forecast point */}
        <Area
          dataKey="upper"
          stroke="none"
          fill="#bfdbfe"
          fillOpacity={0.6}
          name="Upper bound"
          legendType="none"
        />
        <Area
          dataKey="lower"
          stroke="none"
          fill="#ffffff"
          fillOpacity={1}
          name="Lower bound"
          legendType="none"
        />
        <Line
          dataKey="actual"
          stroke="#1d4ed8"
          dot={false}
          name="Actual (observed)"
          strokeWidth={1.5}
        />
        <Line
          dataKey="imputed"
          stroke="#93c5fd"
          dot={{ r: 3, fill: "#93c5fd" }}
          activeDot={false}
          name="Imputed"
          strokeWidth={0}
        />
        <Line
          dataKey="forecast"
          stroke="#dc2626"
          strokeDasharray="6 3"
          dot={{ r: 5, fill: "#dc2626" }}
          name="7-day forecast"
          strokeWidth={2}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
