# MandiPulse India

MandiPulse India is a transport-cost-aware mandi decision intelligence system. The MVP is deliberately narrow: an offline Onion/Maharashtra showcase that forecasts a 7-day price, subtracts transparent distance-based transport cost, and ranks nearby mandis.

## Current Implementation Path

The primary mandi data path is AGMARKNET data through the CEDA API.

- Documentation: `https://api.ceda.ashoka.edu.in/documentation/`
- API base: `https://api.ceda.ashoka.edu.in/v1`
- Auth env var: `CEDA_API_TOKEN`
- Fallback: Data.gov.in / AGMARKNET only if registration becomes available later

CEDA uses numeric IDs. Day 0 validation has confirmed Onion (`commodity_id=23`) and Maharashtra (`state_id=27`). The static historical dump has been saved locally, so modeling work no longer depends on a live API key.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

For simple runtime-only installs, such as basic deployment environments:

```powershell
python -m pip install -r requirements.txt
```

Create a local `.env` from `.env.example` and set:

```text
CEDA_API_TOKEN=your_ceda_token
```

Do not commit `.env`, raw datasets, model artifacts, or MLflow runs.

## Day 0 Validation

Run the CEDA validation script before writing full ingestion:

```powershell
python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31
```

The script writes small reproducibility samples under `data/raw/samples/`, which is intentionally ignored by git.

Day 0 is complete when `docs/DATA_SOURCES.md` contains:

- Confirmed auth behavior
- Commodity, state, district, and market ID findings
- Onion/Maharashtra sample status
- Date-range and rate-limit notes
- Sample response paths

## MVP Data Pipeline

The raw CEDA dump has already been captured locally. Re-run only if you need to refresh it:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
```

Build the cleaned panel and 7-day feature table:

```powershell
python scripts\build_clean_onion_panel.py
python scripts\build_feature_table.py
```

Raw and processed CSVs are ignored by Git. Reproducible scripts and small reports are committed.

## Project Docs

- Product scope: `docs/PRD.md`
- Architecture: `docs/ARCHITECTURE.md`
- Data-source contract: `docs/DATA_SOURCES.md`
- Data schema: `docs/DATA_SCHEMA.md`
- Implementation plan: `docs/IMPLEMENTATION_PLAN.md`
- Tracker: `docs/TRACKER.md`
- Development rules: `docs/RULES.md`
