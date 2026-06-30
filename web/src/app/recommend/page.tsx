"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import SampleBanner from "@/components/SampleBanner";
import RecommendTable from "@/components/RecommendTable";
import BacktestSummaryCard from "@/components/BacktestSummary";
import { loadMeta, loadMandis, loadForecasts, loadBacktest } from "@/lib/data";
import { rankMandis } from "@/lib/transport";
import type {
  Meta,
  MandiMeta,
  ForecastRow,
  BacktestSummary,
  RankedMandi,
} from "@/lib/types";

const MandiMap = dynamic(() => import("@/components/MandiMap"), { ssr: false });

// Named preset locations in Maharashtra for the farmer-location dropdown.
const FARMER_PRESETS = [
  { label: "Nashik (default)", lat: 19.9975, lon: 73.7898 },
  { label: "Pune", lat: 18.5204, lon: 73.8567 },
  { label: "Aurangabad", lat: 19.8762, lon: 75.3433 },
  { label: "Solapur", lat: 17.6851, lon: 75.9064 },
  { label: "Kolhapur", lat: 16.705, lon: 74.2433 },
];

export default function RecommendPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [mandis, setMandis] = useState<MandiMeta[]>([]);
  const [forecasts, setForecasts] = useState<ForecastRow[]>([]);
  const [backtest, setBacktest] = useState<BacktestSummary | null>(null);

  // Slider state
  const [presetIdx, setPresetIdx] = useState(0);
  const [costPerKm, setCostPerKm] = useState(4.0);

  useEffect(() => {
    Promise.all([loadMeta(), loadMandis(), loadForecasts(), loadBacktest()]).then(
      ([m, ms, fcs, bt]) => {
        setMeta(m);
        setMandis(ms);
        setForecasts(fcs);
        setBacktest(bt);
        // Sync slider default from config
        setCostPerKm(m.ranking.cost_per_km_per_quintal);
      }
    );
  }, []);

  const preset = FARMER_PRESETS[presetIdx];

  const ranked: RankedMandi[] = useMemo(() => {
    if (!meta || !forecasts.length || !mandis.length) return [];
    return rankMandis(forecasts, mandis, preset.lat, preset.lon, {
      ...meta.ranking,
      cost_per_km_per_quintal: costPerKm,
    });
  }, [meta, forecasts, mandis, preset, costPerKm]);

  const top1MarketId = ranked[0]?.market_id;

  return (
    <div className="space-y-6">
      {meta && <SampleBanner asOfDate={meta.as_of_date} />}

      <div>
        <h1 className="text-xl font-bold mb-1">Mandi Recommendation</h1>
        <p className="text-sm text-gray-500">
          Mandis ranked by risk-adjusted net price after transport cost. Slider
          re-ranks instantly in the browser.
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white border border-gray-200 rounded p-4 flex flex-wrap gap-6 items-end">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Farmer location</label>
          <select
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
            value={presetIdx}
            onChange={(e) => setPresetIdx(Number(e.target.value))}
          >
            {FARMER_PRESETS.map((p, i) => (
              <option key={p.label} value={i}>
                {p.label}
              </option>
            ))}
          </select>
          <div className="text-xs text-gray-400 mt-0.5">
            lat {preset.lat.toFixed(4)}, lon {preset.lon.toFixed(4)}
          </div>
        </div>

        <div className="flex-1 min-w-48">
          <label className="block text-xs text-gray-600 mb-1">
            Transport cost:{" "}
            <span className="font-semibold">{costPerKm.toFixed(1)} INR/km/qtl</span>
          </label>
          <input
            type="range"
            min={1.0}
            max={8.0}
            step={0.5}
            value={costPerKm}
            onChange={(e) => setCostPerKm(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>1.0</span>
            <span>default: {meta?.ranking.cost_per_km_per_quintal ?? 4.0}</span>
            <span>8.0</span>
          </div>
        </div>
      </div>

      {/* Recommendation table */}
      {ranked.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">
            Ranked mandis (risk-adjusted score = net price − uncertainty penalty)
          </h2>
          <RecommendTable rows={ranked} />
          <p className="text-xs text-gray-500 mt-1">
            Ranking: risk_adjusted_score DESC → net price DESC. Road km = haversine × 1.3 factor.
          </p>
        </div>
      )}

      {/* Map */}
      {mandis.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Map</h2>
          <MandiMap
            mandis={mandis}
            farmerLat={preset.lat}
            farmerLon={preset.lon}
            top1MarketId={top1MarketId}
          />
          <p className="text-xs text-gray-400 mt-1">
            Blue = farmer location. Green = top-ranked mandi.
          </p>
        </div>
      )}

      {/* Backtest summary */}
      {backtest && (
        <div className="bg-white border border-gray-200 rounded p-4">
          <BacktestSummaryCard data={backtest} />
        </div>
      )}
    </div>
  );
}
