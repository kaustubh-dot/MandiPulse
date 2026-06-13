# MandiPulse India TODO

This is the quick working checklist. Keep the detailed roadmap in `docs/TRACKER.md` as the source of task status.

## Current Gate

- [x] Planning docs created.
- [x] Pre-implementation gate fixes applied.
- [ ] Start Phase 1 Day 0.

## Phase 1 Day 0: CEDA / AGMARKNET Validation

Stop after validation. Do not build full ingestion yet.

- [x] Confirm CEDA bearer-token auth using `CEDA_API_TOKEN`.
- [x] Run `python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31`.
- [x] Fetch commodity IDs from `/agmarknet/commodities`.
- [x] Fetch state/district IDs from `/agmarknet/geographies`.
- [x] Fetch market IDs from `/agmarknet/markets` for one MVP commodity/state/district.
- [x] Test a small Onion price request.
- [x] Test a small Tomato price request.
- [x] Test at least one MVP state and district filter.
- [x] Verify response fields and casing.
- [x] Verify price fields: min, max, modal.
- [x] Verify market, commodity, state, district, and date ID mappings.
- [ ] Verify whether date ranges need chunking or rate-limit handling.
- [x] Save one small sample response under `data/raw/samples/`.
- [x] Update `docs/DATA_SOURCES.md` with findings.
- [x] Stop before full ingestion.

## Week 1 Priorities

- [x] Create project folder structure.
- [x] Add dependency/config skeleton.
- [x] Confirm raw and processed data storage conventions.
- [x] Build only the first reproducible raw data sample flow after Day 0 is complete.
- [x] Fetch full Onion/Maharashtra CEDA history from 2020-01-01 to 2026-06-13 before the key expires.
- [x] Start EDA for Onion/Maharashtra mandi coverage.
- [x] Select top 10-15 Maharashtra onion mandis based on non-empty price coverage and arrival volume.
- [ ] Add latitude/longitude for selected MVP mandis.
- [x] Build cleaned Onion/Maharashtra panel for selected mandis.
- [x] Build leakage-safe 7-day feature table.
- [ ] Implement temporal split and baseline metrics.
- [ ] Update `docs/TRACKER.md` after completed tasks.

## Scope Guardrails

- [x] Narrow MVP to Onion, Maharashtra, and 10-15 mandis.
- [x] Use temporal validation only.
- [ ] Use LightGBM as the first primary model.
- [ ] Keep CatBoost as P1 comparison only.
- [ ] Keep weather and SHAP as P1, not blockers.
- [ ] Keep 14-day and 30-day horizons out of the MVP until the 7-day system works.
- [ ] Keep FastAPI, regime/anomaly detection, and advanced monitoring out of the MVP.
- [ ] Do not add P2 endpoints or advanced modules during MVP.
- [ ] Do not add React, Kubernetes, mobile app, WhatsApp bot, deep learning, or TFT.
