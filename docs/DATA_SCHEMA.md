# MandiPulse India Data Schema

## Schema Principles

- Use snake_case column names.
- Store prices as INR per quintal whenever possible.
- Use normalized crop, state, district, and mandi names.
- Preserve raw records separately from cleaned records.
- Every model row must be reproducible from source data and configuration.
- Never allow future information into lag or rolling features.

## Primary Data Source

### CEDA AGMARKNET API

The primary data source is the CEDA API, which exposes AGMARKNET commodity, geography, market, price, and quantity endpoints.

| Detail | Value |
|---|---|
| Documentation | https://api.ceda.ashoka.edu.in/documentation/ |
| API base | `https://api.ceda.ashoka.edu.in/v1` |
| Response format | JSON with `data` arrays for market, price, and quantity endpoints |
| Authentication | Bearer token in the `Authorization` header |
| Token env var | `CEDA_API_TOKEN` |

Key endpoints:

| Endpoint | Method | Use |
|---|---:|---|
| `/agmarknet/commodities` | GET | Commodity ID/name lookup |
| `/agmarknet/geographies` | GET | State and district ID/name lookup |
| `/agmarknet/markets` | POST | Market ID/name lookup |
| `/agmarknet/prices` | POST | Min, max, modal prices |
| `/agmarknet/quantities` | POST | Arrival quantities |

**To be confirmed during Day 0 API validation:**

- Token creation and auth behavior.
- Commodity, state, district, and market IDs for MVP scope.
- Rate limits and throttling behavior.
- Maximum safe date range per request.
- Historical date coverage (expected approximately 2014 to present).
- Any API downtime patterns or known instability.

### Known CEDA Field Names

Price records are expected to include:

| Source Field | Maps To |
|---|---|
| `date` | `arrival_date_raw` |
| `commodity_id` | `source_commodity_id` |
| `census_state_id` | `source_state_id` |
| `census_district_id` | `source_district_id` |
| `market_id` | `source_market_id` |
| `min_price` | `min_price_raw` |
| `max_price` | `max_price_raw` |
| `modal_price` | `modal_price_raw` |

Readable crop, state, district, and mandi names must be resolved through CEDA lookup endpoints and preserved in raw and clean tables.

### Known Data Quality Issues

These are commonly reported issues with AGMARKNET data. The current Onion/Maharashtra profile and clean-panel reports are the source of truth for the MVP.

- Inconsistent mandi name spellings across records and dates.
- Missing arrival quantity for many records.
- Occasional unit ambiguity (per quintal vs per kg).
- Gaps in reporting for weekends, holidays, and low-activity mandis.
- Duplicate records for the same crop-mandi-date.

### Fallback Data Source

Data.gov.in / AGMARKNET may be used as a fallback if registration works later. Kaggle AGMARKNET datasets or pre-cleaned historical CSV files may be used only as bootstrap data for initial EDA and historical experiments. They must not be treated as the final source of truth for the MVP pipeline.

## Raw Mandi Price Schema

Table: `raw_mandi_prices`

| Column | Type | Required | Description |
|---|---|---:|---|
| `source_record_id` | string | Yes | Unique source-level record ID if available; otherwise generated hash |
| `source_name` | string | Yes | Source system or file name |
| `source_commodity_id` | string/integer | No | Source commodity ID if provided |
| `source_state_id` | string/integer | No | Source state ID if provided |
| `source_district_id` | string/integer | No | Source district ID if provided |
| `source_market_id` | string/integer | No | Source market ID if provided |
| `arrival_date_raw` | string | Yes | Date as received from source |
| `state_raw` | string | Yes | State name as received |
| `district_raw` | string | No | District name as received |
| `mandi_raw` | string | Yes | Mandi/market name as received |
| `crop_raw` | string | Yes | Commodity/crop name as received |
| `variety_raw` | string | No | Variety if available |
| `grade_raw` | string | No | Grade if available |
| `min_price_raw` | string/float | No | Raw minimum price |
| `max_price_raw` | string/float | No | Raw maximum price |
| `modal_price_raw` | string/float | Yes | Raw modal price |
| `arrival_quantity_raw` | string/float | No | Raw arrival quantity |
| `unit_raw` | string | No | Source unit |
| `ingested_at` | datetime | Yes | Ingestion timestamp |

## Cleaned Mandi Price Schema

Table: `clean_mandi_prices`

| Column | Type | Required | Description |
|---|---|---:|---|
| `date` | date | Yes | Market date |
| `state` | string | Yes | Normalized state |
| `district` | string | No | Normalized district |
| `mandi` | string | Yes | Normalized mandi name |
| `mandi_id` | string | Yes | Stable normalized mandi ID |
| `crop` | string | Yes | Normalized crop name |
| `crop_id` | string | Yes | Stable crop ID |
| `variety` | string | No | Normalized variety if useful |
| `min_price_inr_qtl` | float | No | Minimum price in INR/quintal |
| `max_price_inr_qtl` | float | No | Maximum price in INR/quintal |
| `modal_price_inr_qtl` | float | Yes | Main target price in INR/quintal |
| `arrival_quantity_qtl` | float | No | Arrival quantity in quintals |
| `is_imputed` | boolean | Yes | Whether target value was imputed |
| `quality_flag` | string | Yes | `ok`, `duplicate`, `missing_target`, `outlier`, `invalid_unit`, etc. |
| `source_name` | string | Yes | Original source |
| `created_at` | datetime | Yes | Processing timestamp |

Natural key:

```text
date + crop_id + mandi_id
```

## ID Generation Rules

### `mandi_id`

Format: `{slugified_state}__{slugified_mandi_name}`

Generation steps:

1. Strip leading and trailing whitespace.
2. Convert to lowercase.
3. Remove punctuation except hyphens.
4. Replace spaces with underscores.
5. Collapse consecutive underscores.
6. Concatenate state slug, double underscore separator, and mandi slug.

Example: `"  Lasalgaon "` in `"Maharashtra"` becomes `maharashtra__lasalgaon`.

### `crop_id`

Format: `{lowercase_stripped_crop_name}`

Example: `"Onion"` becomes `onion`.

### Alias Maps

Maintain alias maps in `configs/data.yaml` for known spelling variants:

- Mandi aliases: map `lasalgoan`, `lasalgaon`, `LASALGAON` to the canonical `lasalgaon`.
- Crop aliases: map `Onion`, `ONION`, `onion (nashik)` to `onion`.

The ingestion pipeline must apply alias resolution before generating IDs.

## Mandi Metadata Schema

Table: `mandi_metadata`

| Column | Type | Required | Description |
|---|---|---:|---|
| `mandi_id` | string | Yes | Stable mandi ID |
| `mandi` | string | Yes | Normalized mandi name |
| `state` | string | Yes | State |
| `district` | string | No | District |
| `latitude` | float | Yes | Mandi latitude |
| `longitude` | float | Yes | Mandi longitude |
| `is_active_mvp` | boolean | Yes | Whether included in the top 10-15 mandi MVP |
| `primary_crops` | array/string | No | Crops commonly traded |
| `data_start_date` | date | No | First usable record date |
| `data_end_date` | date | No | Latest usable record date |
| `record_count` | integer | No | Cleaned record count |
| `missing_rate` | float | No | Missing target rate in selected period |

## Weather Feature Schema

Table: `weather_features`

Weather is optional for MVP if collection or alignment becomes a blocker.

| Column | Type | Required | Description |
|---|---|---:|---|
| `date` | date | Yes | Weather date |
| `mandi_id` | string | Yes | Mandi or nearest weather point |
| `rainfall_mm` | float | No | Daily rainfall |
| `temperature_min_c` | float | No | Minimum temperature |
| `temperature_max_c` | float | No | Maximum temperature |
| `temperature_avg_c` | float | No | Average temperature |
| `humidity_avg_pct` | float | No | Average humidity |
| `weather_source` | string | No | Source name |
| `weather_missing_flag` | boolean | Yes | True if weather values are missing/imputed |

## Feature Table Schema

Table: `feature_table`

| Column | Type | Required | Description |
|---|---|---:|---|
| `date` | date | Yes | Feature date |
| `crop_id` | string | Yes | Crop ID |
| `crop` | string | Yes | Crop name |
| `mandi_id` | string | Yes | Mandi ID |
| `mandi` | string | Yes | Mandi name |
| `state` | string | Yes | State |
| `district` | string | No | District |
| `target_price_inr_qtl` | float | Yes | Modal price known on the current as-of date |
| `arrival_quantity_qtl` | float | No | Arrival quantity |
| `price_lag_1` | float | Yes | Price lagged 1 day |
| `price_lag_3` | float | Yes | Price lagged 3 days |
| `price_lag_7` | float | Yes | Price lagged 7 days |
| `price_lag_14` | float | Yes | Price lagged 14 days |
| `price_lag_30` | float | Yes | Price lagged 30 days |
| `rolling_mean_7` | float | Yes | 7-day rolling mean using past data only |
| `rolling_median_7` | float | Yes | 7-day rolling median using past data only |
| `rolling_std_7` | float | Yes | 7-day rolling standard deviation |
| `rolling_mean_30` | float | Yes | 30-day rolling mean |
| `rolling_std_30` | float | Yes | 30-day rolling standard deviation |
| `price_return_1d` | float | Yes | 1-day price return |
| `price_return_7d` | float | Yes | 7-day price return |
| `volatility_7d` | float | Yes | Rolling volatility |
| `day_of_week` | integer | Yes | 0-6 |
| `month` | integer | Yes | 1-12 |
| `season` | string | No | Season label |
| `is_holiday_or_festival` | boolean | No | Optional indicator |
| `rainfall_mm` | float | No | Optional weather feature |
| `temperature_avg_c` | float | No | Optional weather feature |
| `humidity_avg_pct` | float | No | Optional weather feature |
| `history_length_days` | integer | Yes | Usable history count |
| `feature_quality_flag` | string | Yes | `ok`, `insufficient_history`, `missing_lags`, etc. |

Training targets for horizons should be generated explicitly:

| Column | Type | Required | Description |
|---|---|---:|---|
| `target_price_t_plus_7` | float | Yes | Price 7 days ahead |
| `target_price_t_plus_14` | float | No | Deferred post-MVP target |
| `target_price_t_plus_30` | float | No | Deferred post-MVP target |

### Target Leakage Prevention

When training a model for forecast horizon H:

- **Target variable**: `target_price_t_plus_{H}` (the price H days in the future).
- **Allowed features**: current-day modal price plus lag, rolling, calendar, and arrival columns computed strictly from data on or before `date`.
- **Forbidden as feature**: any price, arrival, rolling statistic, imputation signal, or target derived from rows after `date`.
- **Exclusion rule**: rows where `target_price_t_plus_{H}` is null must be excluded from training and evaluation for that horizon.
- **Validation**: automated tests must verify that no column in the feature vector contains future price information.

## Forecast Output Schema

Table or artifact: `forecast_outputs`

| Column | Type | Required | Description |
|---|---|---:|---|
| `forecast_id` | string | Yes | Unique forecast ID |
| `generated_at` | datetime | Yes | Forecast timestamp |
| `as_of_date` | date | Yes | Latest data date used |
| `crop` | string | Yes | Crop |
| `crop_id` | string | Yes | Crop ID |
| `state` | string | Yes | State |
| `mandi` | string | Yes | Mandi |
| `mandi_id` | string | Yes | Mandi ID |
| `horizon_days` | integer | Yes | 7 for MVP; 14 and 30 are post-MVP |
| `forecast_price_inr_qtl` | float | Yes | Predicted modal price |
| `lower_bound_inr_qtl` | float | Yes | Lower uncertainty bound |
| `upper_bound_inr_qtl` | float | Yes | Upper uncertainty bound |
| `confidence_level` | float | Yes | Example: 0.90 |
| `market_regime` | string | No | Post-MVP only |
| `model_name` | string | Yes | Model family |
| `model_version` | string | Yes | MLflow run/model version |
| `top_drivers` | array/string | No | Human-readable forecast drivers |

## Recommendation Output Schema

Table or artifact: `recommendation_outputs`

| Column | Type | Required | Description |
|---|---|---:|---|
| `recommendation_id` | string | Yes | Unique recommendation ID |
| `generated_at` | datetime | Yes | Recommendation timestamp |
| `crop` | string | Yes | Crop |
| `horizon_days` | integer | Yes | 7 for MVP; 14 and 30 are post-MVP |
| `quantity_quintal` | float | Yes | User quantity |
| `farmer_latitude` | float | Yes | Input latitude |
| `farmer_longitude` | float | Yes | Input longitude |
| `candidate_states` | array/string | Yes | Candidate state filters |
| `rank` | integer | Yes | Rank of mandi |
| `mandi_id` | string | Yes | Candidate mandi ID |
| `mandi` | string | Yes | Candidate mandi |
| `state` | string | Yes | Candidate state |
| `forecast_price_inr_qtl` | float | Yes | Forecast price |
| `lower_bound_inr_qtl` | float | Yes | Lower forecast bound |
| `upper_bound_inr_qtl` | float | Yes | Upper forecast bound |
| `estimated_transport_cost_inr_qtl` | float | Yes | Transport cost per quintal |
| `expected_net_price_inr_qtl` | float | Yes | Forecast minus transport cost |
| `uncertainty_penalty_inr_qtl` | float | Yes | Risk penalty |
| `risk_adjusted_score` | float | Yes | Ranking score |
| `risk_level` | string | Yes | `low`, `medium`, `high` |
| `market_regime` | string | No | Post-MVP only |
| `reason` | string | No | Recommendation explanation |

## Post-MVP Monitoring / Logging Schema

The following schemas are retained as future reference only. They are not required for the offline Streamlit MVP.

Table: `monitoring_metrics`

| Column | Type | Required | Description |
|---|---|---:|---|
| `metric_timestamp` | datetime | Yes | Metric timestamp |
| `metric_date` | date | Yes | Business date |
| `metric_name` | string | Yes | Metric name |
| `metric_value` | float/string | Yes | Metric value |
| `metric_unit` | string | No | Unit |
| `crop` | string | No | Optional crop scope |
| `state` | string | No | Optional state scope |
| `mandi_id` | string | No | Optional mandi scope |
| `model_version` | string | No | Model version |
| `severity` | string | No | `info`, `warning`, `critical` |

Table: `api_request_logs`

| Column | Type | Required | Description |
|---|---|---:|---|
| `request_id` | string | Yes | Request identifier |
| `timestamp` | datetime | Yes | Request timestamp |
| `endpoint` | string | Yes | Endpoint path |
| `status_code` | integer | Yes | HTTP status |
| `latency_ms` | float | Yes | Response latency |
| `success` | boolean | Yes | Whether request succeeded |
| `error_code` | string | No | Error code if failed |
| `model_version` | string | No | Model version used |

## Data Validation Rules

### Raw Data

- `arrival_date_raw` must parse to a valid date.
- `state_raw`, `mandi_raw`, and `crop_raw` must be non-empty.
- `modal_price_raw` must be numeric or convertible to numeric.
- Duplicate source records must be identified.

### Cleaned Data

- `modal_price_inr_qtl` must be positive.
- `min_price_inr_qtl <= modal_price_inr_qtl <= max_price_inr_qtl` when all are available.
- `arrival_quantity_qtl` must be non-negative when available.
- `date + crop_id + mandi_id` should be unique after cleaning.
- Only Onion/Maharashtra rows should enter MVP model training.
- Mandis with insufficient history should be flagged before modeling.

### Feature Table

- Lag and rolling features must use past observations only.
- Rows with insufficient history must be excluded or flagged.
- Training rows must have target for the selected horizon.
- No feature may directly or indirectly include target future price.
- Temporal split boundaries must be recorded, and training rows must be purged by the forecast horizon before validation/test windows.

## Missing Data Handling Rules

| Missing Data Type | Rule |
|---|---|
| Missing modal price | Do not train on the row unless imputed with documented method and flagged |
| Short single-day gaps | Forward fill/interpolate only within same crop-mandi series if justified |
| Long gaps | Keep as missing, flag mandi as low quality, possibly exclude |
| Missing arrival quantity | Add missing flag; impute median or leave absent depending on model |
| Missing weather | Use missing flag; weather must not block MVP |
| Missing coordinates | Exclude mandi from recommendation until coordinates are fixed |
| Duplicate crop-mandi-date records | Aggregate deterministically or keep best quality record |
| Outliers | Flag, inspect, and use robust handling; do not silently delete |

## MVP Data Scope Checklist

- [x] Exactly 1 selected crop: Onion.
- [x] Exactly 1 selected state: Maharashtra.
- [x] 10-15 active Maharashtra onion mandis selected.
- [x] Forecast horizon limited to 7 days for MVP.
- [x] All model features reproducible from cleaned tables.
- [x] Missingness and exclusions documented in data-quality reports.
- [x] Mandi latitude/longitude completed before recommendation work.
- [x] Temporal split dates documented before modeling.
