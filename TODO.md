# MandiPulse India TODO

This is the quick working checklist. Keep the detailed roadmap in `docs/TRACKER.md` as the source of task status.

## Current Gate

- [x] Planning docs created.
- [x] Pre-implementation gate fixes applied.
- [ ] Start Phase 1 Day 0.

## Phase 1 Day 0: CEDA / AGMARKNET Validation

Stop after validation. Do not build full ingestion yet.

- [ ] Confirm CEDA bearer-token auth using `CEDA_API_TOKEN`.
- [ ] Run `python scripts\day0_validate_ceda.py --from-date 2025-03-01 --to-date 2025-03-31`.
- [ ] Fetch commodity IDs from `/agmarknet/commodities`.
- [ ] Fetch state/district IDs from `/agmarknet/geographies`.
- [ ] Fetch market IDs from `/agmarknet/markets` for one MVP commodity/state/district.
- [ ] Test a small Onion price request.
- [ ] Test a small Tomato price request.
- [ ] Test at least one MVP state and district filter.
- [ ] Verify response fields and casing.
- [ ] Verify price fields: min, max, modal.
- [ ] Verify market, commodity, state, district, and date ID mappings.
- [ ] Verify whether date ranges need chunking or rate-limit handling.
- [ ] Save one small sample response under `data/raw/samples/`.
- [ ] Update `docs/DATA_SOURCES.md` with findings.
- [ ] Stop before full ingestion.

## Week 1 Priorities

- [x] Create project folder structure.
- [x] Add dependency/config skeleton.
- [ ] Confirm raw and processed data storage conventions.
- [ ] Build only the first reproducible raw data sample flow after Day 0 is complete.
- [ ] Start EDA for crop/state/mandi coverage.
- [ ] Finalize MVP crops, states, and 50-100 mandis based on data quality.
- [ ] Update `docs/TRACKER.md` after completed tasks.

## Scope Guardrails

- [ ] Keep MVP to 2 crops, 3 states, and 50-100 mandis.
- [ ] Use temporal validation only.
- [ ] Use LightGBM as the first primary model.
- [ ] Keep CatBoost as P1 comparison only.
- [ ] Keep weather and SHAP as P1, not blockers.
- [ ] Do not add P2 endpoints or advanced modules during MVP.
- [ ] Do not add React, Kubernetes, mobile app, WhatsApp bot, deep learning, or TFT.
