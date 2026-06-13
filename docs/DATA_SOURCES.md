# MandiPulse India Data Sources

## Purpose

This file records the data-source contract for Phase 1. It must be updated during Day 0 API validation before full ingestion work begins.

## Primary Source

Use the CEDA API as the primary AGMARKNET source because Data.gov.in account registration is currently blocking access.

| Item | Value |
|---|---|
| Source | CEDA / AGMARKNET |
| Provider | Centre for Economic Data and Analysis, Ashoka University |
| Documentation | `https://api.ceda.ashoka.edu.in/documentation/` |
| API base | `https://api.ceda.ashoka.edu.in/v1` |
| Auth | Bearer token in the `Authorization` header |
| API token env var | `CEDA_API_TOKEN` |
| Expected format | JSON response with a `data` array for market, price, and quantity endpoints |
| MVP crop | Onion |
| MVP state | Maharashtra |

## Confirmed CEDA Endpoints

The Swagger documentation currently exposes AGMARKNET endpoints only.

| Endpoint | Method | Purpose |
|---|---:|---|
| `/agmarknet/commodities` | GET | List commodity IDs and names |
| `/agmarknet/geographies` | GET | List state IDs and nested district IDs |
| `/agmarknet/markets` | POST | List markets for a commodity, state, district, and indicator |
| `/agmarknet/prices` | POST | Fetch min, max, and modal prices |
| `/agmarknet/quantities` | POST | Fetch arrival quantities |

CEDA uses numeric IDs, so Day 0 should first build a small lookup table for commodities, states, districts, and markets.

## Day 0 Validation Checklist

Day 0 is a verification task only. Stop before building full ingestion.

- [x] Confirm bearer-token auth using `CEDA_API_TOKEN`.
- [x] Fetch and save a small commodity lookup sample.
- [x] Fetch and save a small geography lookup sample.
- [x] Fetch and save market IDs for one MVP commodity/state/district.
- [x] Test a small Onion price request.
- [x] Test a small Tomato price request before narrowing scope; Tomato is deferred from MVP.
- [x] Test at least one MVP state and district filter.
- [x] Verify response fields and casing.
- [x] Verify date format.
- [x] Verify price fields: min, max, modal.
- [x] Verify market, commodity, state, district, and date ID mappings.
- [ ] Verify whether long date ranges need chunking.
- [ ] Record 401, 429, 500, downtime, or rate-limit behavior.
- [x] Save one small sample response under `data/raw/samples/`.
- [x] Record the sample filename and request payload in this file.
- [x] Stop before full ingestion.

## Day 0 Query Templates

Prefer the validation script because it saves the lookup and sample files consistently:

```powershell
python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31
```

The script fetches commodity and geography lookups, searches the MVP crop/state scope from `configs/data.yaml`, fetches a market sample, and then fetches a small price sample. It writes outputs under `data/raw/samples/`.

Manual request templates are below for debugging.

Set the token locally:

```text
CEDA_API_TOKEN=your_token_here
```

Commodities:

```bash
curl -H "Authorization: Bearer ${CEDA_API_TOKEN}" \
  https://api.ceda.ashoka.edu.in/v1/agmarknet/commodities
```

Geographies:

```bash
curl -H "Authorization: Bearer ${CEDA_API_TOKEN}" \
  https://api.ceda.ashoka.edu.in/v1/agmarknet/geographies
```

Markets:

```bash
curl -X POST https://api.ceda.ashoka.edu.in/v1/agmarknet/markets \
  -H "Authorization: Bearer ${CEDA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"commodity_id":3,"state_id":3,"district_id":41,"indicator":"price"}'
```

Prices:

```bash
curl -X POST https://api.ceda.ashoka.edu.in/v1/agmarknet/prices \
  -H "Authorization: Bearer ${CEDA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"commodity_id":1,"state_id":8,"district_id":[104],"market_id":[255,3149],"from_date":"2025-03-01","to_date":"2025-06-01"}'
```

Replace IDs after validating CEDA lookup values for the MVP crops and states. Do not hardcode guessed IDs in ingestion code.

## Field Mapping To Confirm

| CEDA Source Field | Target Raw Column |
|---|---|
| `date` | `arrival_date_raw` |
| `commodity_id` | `source_commodity_id` |
| `census_state_id` | `source_state_id` |
| `census_district_id` | `source_district_id` |
| `market_id` | `source_market_id` |
| `min_price` | `min_price_raw` |
| `max_price` | `max_price_raw` |
| `modal_price` | `modal_price_raw` |

Lookup responses must be joined back to preserve readable commodity, state, district, and market names.

## Day 0 Findings

Fill this section after validation.

| Item | Finding |
|---|---|
| Confirmed endpoint URL | `https://api.ceda.ashoka.edu.in/v1` |
| Auth behavior | Bearer token accepted; key is time-limited and should be refreshed before future data pulls |
| Onion request status | Success: `commodity_id=23`; non-empty Maharashtra/Dhule sample saved with 20 records for 2025-03-01 to 2025-03-31 |
| Tomato request status | Success: `commodity_id=78`; deferred from MVP after brutal scope review |
| Date-range behavior | One-month market-level sample requests succeeded |
| Sample response path | `data/raw/samples/day0_ceda_summary.json` after running the validation script |
| Historical coverage | CEDA portal states agri-market data spans from 2000/present; project-specific coverage still needs full MVP pull |
| Rate limits or API quirks | Commodity/geography responses use nested `output.data`; geographies are flat district rows, not nested state objects |

## Narrowed MVP Data Grab

The project is now an offline Onion/Maharashtra MVP. Fetch raw historical data before the temporary key expires:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
```

Smoke-tested command:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2025-03-01 --to-date 2025-03-31 --max-districts 2
```

Smoke-test result: 2 districts, 7 markets, 26 flattened price rows, written under `data/raw/ceda/onion_maharashtra/`.

Full narrowed-MVP fetch result:

| Item | Result |
|---|---|
| Command | `python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13 --chunk-days 366 --market-batch-size 50 --request-sleep-seconds 2` |
| Raw flat CSV | `data/raw/ceda/onion_maharashtra/onion_maharashtra_prices_raw.csv` |
| Requested date range | 2020-01-01 to 2026-06-13 |
| Returned row date range | 2020-01-01 to 2025-10-30 |
| Price rows | 86,052 |
| Markets with rows | 125 |
| Districts with rows | 25 |
| Raw markets discovered | 169 |
| Raw districts discovered | 35 |
| Profile report | `reports/data_quality/onion_maharashtra_profile.md` |
| Candidate mandi list | `data/external/mvp_mandis.csv` |

The mismatch between requested end date and returned latest date must be treated as a data freshness limitation, not hidden or patched with imputation.

## Fallback Source

Data.gov.in / AGMARKNET remains the preferred government-origin fallback if registration works later.

| Item | Value |
|---|---|
| Source | Data.gov.in / AGMARKNET |
| Dataset name | Current Daily Price of Various Commodities from Various Markets (Mandi) |
| Portal | `https://data.gov.in` |
| API base pattern | `https://api.data.gov.in/resource/{RESOURCE_ID}` |
| Auth | API key passed as `api-key` query parameter |
| API key env var | `DATA_GOV_IN_API_KEY` |

Kaggle AGMARKNET datasets or pre-cleaned historical CSV files may be used only as bootstrap data for EDA and historical experiments if both API paths are inaccessible or severely rate-limited.

Fallback data must not silently replace the primary source. If fallback data is used:

- Document the dataset URL and license.
- Record download date.
- Record available date range.
- Record field mapping.
- Clearly mark it as fallback/bootstrap data.
