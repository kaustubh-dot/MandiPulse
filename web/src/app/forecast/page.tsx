"use client";

import { useEffect, useState } from "react";
import SampleBanner from "@/components/SampleBanner";
import ForecastChart from "@/components/ForecastChart";
import HonestResultsTable from "@/components/HonestResultsTable";
import {
  loadMeta,
  loadMandis,
  loadForecasts,
  loadPriceHistory,
  loadHonestResults,
} from "@/lib/data";
import type {
  Meta,
  MandiMeta,
  ForecastRow,
  PriceHistoryRow,
  HonestResult,
} from "@/lib/types";

const HISTORY_DAYS = 90;

export default function ForecastPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [mandis, setMandis] = useState<MandiMeta[]>([]);
  const [forecasts, setForecasts] = useState<ForecastRow[]>([]);
  const [priceHistory, setPriceHistory] = useState<PriceHistoryRow[]>([]);
  const [honestResults, setHonestResults] = useState<HonestResult[]>([]);
  const [selectedMarketId, setSelectedMarketId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([
      loadMeta(),
      loadMandis(),
      loadForecasts(),
      loadPriceHistory(),
      loadHonestResults(),
    ]).then(([m, ms, fcs, history, hr]) => {
      setMeta(m);
      setMandis(ms);
      setForecasts(fcs);
      setPriceHistory(history);
      setHonestResults(hr);
      if (fcs.length > 0) setSelectedMarketId(fcs[0].market_id);
    });
  }, []);

  const selectedForecast =
    forecasts.find((f) => f.market_id === selectedMarketId) ?? null;

  const cutoffDate = (() => {
    if (!meta) return "";
    const d = new Date(meta.as_of_date);
    d.setDate(d.getDate() - HISTORY_DAYS);
    return d.toISOString().slice(0, 10);
  })();

  const chartHistory = priceHistory.filter(
    (r) => r.market_id === selectedMarketId && r.date >= cutoffDate
  );

  const RISK_COLOR: Record<string, string> = {
    low: "text-green-700",
    medium: "text-yellow-700",
    high: "text-red-700",
  };

  return (
    <div className="space-y-6">
      {meta && <SampleBanner asOfDate={meta.as_of_date} />}

      <div>
        <h1 className="text-xl font-bold mb-1">7-Day Price Forecast</h1>
        <p className="text-sm text-gray-500">
          Maharashtra Onion — 90-day actual price + 7-day forecast with uncertainty interval
        </p>
      </div>

      {/* Mandi selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Select mandi:</label>
        <select
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          value={selectedMarketId ?? ""}
          onChange={(e) => setSelectedMarketId(Number(e.target.value))}
        >
          {mandis.map((m) => (
            <option key={m.market_id} value={m.market_id}>
              {m.market_name}
            </option>
          ))}
        </select>
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded p-4">
        <ForecastChart history={chartHistory} forecast={selectedForecast} />
      </div>

      {/* Forecast details */}
      {selectedForecast && meta && (
        <div className="bg-white border border-gray-200 rounded p-4 flex flex-wrap gap-6 text-sm">
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Forecast price</div>
            <div className="font-semibold text-lg">
              {selectedForecast.forecast_price_inr_qtl.toFixed(0)} INR/qtl
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">90% interval</div>
            <div className="font-semibold text-lg">
              {selectedForecast.lower_bound_inr_qtl.toFixed(0)} –{" "}
              {selectedForecast.upper_bound_inr_qtl.toFixed(0)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Empirical coverage</div>
            <div className="font-semibold text-lg">
              {(meta.empirical_coverage * 100).toFixed(1)}% (nominal 90%)
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Risk level</div>
            <div
              className={`font-semibold text-lg ${
                RISK_COLOR[selectedForecast.risk_level] ?? ""
              }`}
            >
              {selectedForecast.risk_level}
            </div>
          </div>
        </div>
      )}

      {/* Shipped model disclosure */}
      <div className="bg-blue-50 border border-blue-200 rounded px-4 py-3 text-sm text-blue-800">
        <strong>Shipped model:</strong> 7-day moving average (
        <span className="font-mono">moving_average_7d</span>). LightGBM was
        trained but did not beat this baseline on the held-out test split — the
        baseline ships. This is reported transparently.
      </div>

      {/* Honest results table */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-2">Model comparison (held-out test)</h2>
        <HonestResultsTable results={honestResults} />
      </div>
    </div>
  );
}
