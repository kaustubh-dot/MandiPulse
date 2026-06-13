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
| MVP crops to test first | Onion, Tomato |
| MVP states to test first | Maharashtra, Karnataka, Uttar Pradesh |

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

- [ ] Confirm bearer-token auth using `CEDA_API_TOKEN`.
- [ ] Fetch and save a small commodity lookup sample.
- [ ] Fetch and save a small geography lookup sample.
- [ ] Fetch and save market IDs for one MVP commodity/state/district.
- [ ] Test a small Onion price request.
- [ ] Test a small Tomato price request.
- [ ] Test at least one MVP state and district filter.
- [ ] Verify response fields and casing.
- [ ] Verify date format.
- [ ] Verify price fields: min, max, modal.
- [ ] Verify market, commodity, state, district, and date ID mappings.
- [ ] Verify whether long date ranges need chunking.
- [ ] Record 401, 429, 500, downtime, or rate-limit behavior.
- [ ] Save one small sample response under `data/raw/samples/`.
- [ ] Record the sample filename and request payload in this file.
- [ ] Stop before full ingestion.

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
| Auth behavior | TBD |
| Onion request status | TBD |
| Tomato request status | TBD |
| Date-range behavior | TBD |
| Sample response path | `data/raw/samples/day0_ceda_summary.json` after running the validation script |
| Historical coverage | TBD |
| Rate limits or API quirks | TBD |

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
