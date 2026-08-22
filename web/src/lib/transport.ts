// Port of src/mandipulse/recommend/engine.py
// Formula: atan2 (NOT asin), radius 6371.0, road = air * road_distance_factor.
// Ranking: expected_net_price_inr_qtl DESC, then market_id ASC tie-break.
// transport_adjusted_net_price_inr_qtl is numerically equal to
//   expected_net_price_inr_qtl (forecast minus transport cost).
// Thresholds: low_max_interval_pct and high_min_interval_pct are ratios (0.10, 0.25),
//   matching the /100 division in build_recommendations_7d.py:63,69.

import type { ForecastRow, MandiMeta, MetaRanking, RankedMandi } from "./types";

const RADIUS_KM = 6371.0;

export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const dPhi = ((lat2 - lat1) * Math.PI) / 180;
  const dLambda = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) ** 2;
  return 2 * RADIUS_KM * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function riskLevel(
  relWidth: number,
  lowMax: number,
  highMin: number
): string {
  if (relWidth <= lowMax) return "low";
  if (relWidth < highMin) return "medium";
  return "high";
}

export function rankMandis(
  forecasts: ForecastRow[],
  mandis: MandiMeta[],
  farmerLat: number,
  farmerLon: number,
  p: MetaRanking
): RankedMandi[] {
  const mandiMap = new Map(mandis.map((m) => [m.market_id, m]));

  const scored = forecasts
    .map((f) => {
      const m = mandiMap.get(f.market_id);
      if (!m) return null;

      const airKm = haversineKm(farmerLat, farmerLon, m.latitude, m.longitude);
      const roadKm = airKm * p.road_distance_factor;
      const transport = roadKm * p.cost_per_km_per_quintal;
      const netPrice = f.forecast_price_inr_qtl - transport;
      // Evidence-only penalty: forecast interval widths are uniform across the
      // candidate set, so width * uncertainty_penalty_weight is a constant term
      // that cancels in pairwise comparison and never affects rank. It is kept
      // for display only; ranking uses expected_net_price_inr_qtl directly.
      const width = f.upper_bound_inr_qtl - f.lower_bound_inr_qtl;
      const penalty = width * p.uncertainty_penalty_weight;
      const transportAdjustedNetPrice = netPrice;
      const relWidth = width / Math.max(f.forecast_price_inr_qtl, 1.0);

      return {
        rank: 0,
        market_id: f.market_id,
        mandi_id: f.mandi_id,
        mandi: f.mandi,
        as_of_date: f.as_of_date,
        market_name: m.market_name,
        district_name: m.district_name,
        forecast_price_inr_qtl: f.forecast_price_inr_qtl,
        lower_bound_inr_qtl: f.lower_bound_inr_qtl,
        upper_bound_inr_qtl: f.upper_bound_inr_qtl,
        air_distance_km: airKm,
        road_distance_km: roadKm,
        estimated_transport_cost_inr_qtl: transport,
        expected_net_price_inr_qtl: netPrice,
        uncertainty_penalty_inr_qtl: penalty,
        transport_adjusted_net_price_inr_qtl: transportAdjustedNetPrice,
        risk_level: riskLevel(relWidth, p.low_max_interval_pct, p.high_min_interval_pct),
      } as Omit<RankedMandi, "rank"> & { rank: number };
    })
    .filter((r): r is RankedMandi => r !== null)
    .sort(
      (a, b) =>
        b.expected_net_price_inr_qtl - a.expected_net_price_inr_qtl ||
        a.market_id - b.market_id
    )
    .map((r, i) => ({ ...r, rank: i + 1 }));

  return scored;
}
