// Types mirror web/public/data/ JSON schemas exactly.
// Columns mirror the v2.0.0 export schema (schemas/web_export/v2) and engine.py output.

export interface MetaRanking {
  cost_per_km_per_quintal: number;
  road_distance_factor: number;
  max_transport_radius_km: number;
  max_alternatives: number;
  uncertainty_penalty_weight: number;
  low_max_interval_pct: number; // ratio: 0.10
  high_min_interval_pct: number; // ratio: 0.25
  cost_variation_pct: number;
}

export interface CandidatePolicy {
  rule: "as_of_equals_bundle_max";
  eligible_as_of_date: string;
  eligible_count: number;
  excluded_stale_count: number;
}

export interface Meta {
  as_of_date: string;
  snapshot_date: string;
  forecast_horizon_days: number;
  crop: string;
  state: string;
  model_version: string;
  confidence_level: number;
  empirical_coverage: number;
  default_farmer: { latitude: number; longitude: number };
  candidate_policy: CandidatePolicy;
  ranking: MetaRanking;
}

export interface MandiMeta {
  market_id: number;
  mandi_id: string;
  market_name: string;
  district_name: string;
  latitude: number;
  longitude: number;
  active_days: number;
}

export interface ForecastRow {
  market_id: number;
  mandi_id: string;
  mandi: string;
  as_of_date: string;
  forecast_price_inr_qtl: number;
  lower_bound_inr_qtl: number;
  upper_bound_inr_qtl: number;
  confidence_level: number;
  risk_level: string;
}

export interface PriceHistoryRow {
  market_id: number;
  market_name: string;
  date: string;
  modal_price_inr_qtl: number | null;
  is_imputed: boolean;
}

export interface RecommendationRow {
  rank: number;
  market_id: number;
  mandi_id: string;
  mandi: string;
  district_name: string;
  as_of_date: string;
  forecast_price_inr_qtl: number;
  lower_bound_inr_qtl: number;
  upper_bound_inr_qtl: number;
  estimated_transport_cost_inr_qtl: number;
  expected_net_price_inr_qtl: number;
  uncertainty_penalty_inr_qtl: number;
  transport_adjusted_net_price_inr_qtl: number;
  risk_level: string;
  air_distance_km: number;
  road_distance_km: number;
  reason: string;
}

export interface BacktestSummary {
  mean_regret_at_1: number;
  nearest_mandi_baseline_regret: number;
  pct_beats_nearest: number;
  n_dates_evaluated: number;
  test_window_start: string;
  test_window_end: string;
}

export interface HonestResult {
  model: string;
  test_mae: number;
  ships: boolean;
}

// Ranked row produced by rankMandis() in transport.ts (extends ForecastRow)
export interface RankedMandi {
  rank: number;
  market_id: number;
  mandi_id: string;
  mandi: string;
  as_of_date: string;
  market_name: string;
  district_name: string;
  forecast_price_inr_qtl: number;
  lower_bound_inr_qtl: number;
  upper_bound_inr_qtl: number;
  air_distance_km: number;
  road_distance_km: number;
  estimated_transport_cost_inr_qtl: number;
  expected_net_price_inr_qtl: number;
  uncertainty_penalty_inr_qtl: number;
  transport_adjusted_net_price_inr_qtl: number;
  risk_level: string;
  staleness_days?: number;
}

export interface ArtifactManifest {
  schema_version?: string;
  artifact_version?: string;
  generated_at?: string;
  validation?: Record<string, unknown>;
  artifacts?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}
