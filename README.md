# MandiPulse India

**Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers.**

[![Tests](https://img.shields.io/badge/tests-139%20passed-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-70%25-green)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

> **[Live Demo → mandipulse.streamlit.app](https://mandipulse.streamlit.app/)**

---

## The problem

Maharashtra onion farmers choose which mandi (market) to sell at based on word-of-mouth and nearest
distance. They ignore transport cost, forecast uncertainty, and historical ranking quality. A farmer
who drives 40 km to a mandi with a higher forecast price can still lose money if transport costs
exceed the price premium.

MandiPulse forecasts 7-day prices across 15 mandis, subtracts transparent distance-based transport
cost, and ranks mandis by **net expected price** with uncertainty bounds and risk labels.

---

## Honest results

LightGBM was trained and evaluated — it **did not beat the 7-day moving-average baseline** on the
held-out test split. The baseline ships. This is reported transparently.

| Model | Test MAE (INR/qtl) | Ships? |
|---|---|---|
| `moving_average_7d` | **139.57** | Yes |
| `ridge` | 224.43 | No |
| `lightgbm` | 188.2 | No |
| `lightgbm_residual` | 195.63 | No |

Forecast uncertainty intervals (nominal 90%) achieved **86.71% empirical coverage** on the test
split — conservative, safe to show to users.

Recommendation backtest (regret@K vs nearest-mandi baseline, held-out test window):

| Metric | Value |
|---|---|
| Mean regret@1 | 296.3 INR/qtl |
| Nearest-mandi baseline regret | 370.1 INR/qtl |
| Beats nearest-mandi | 78.8% of dates |

---

## Architecture

```
CEDA/AGMARKNET cache
       |
 clean daily panel  (15 mandis × 2020–2025)
       |
 leakage-safe features  (lags/rolling/calendar — no future data)
       |
 temporal split  (train/val/test — no random splits)
       |
 baseline comparison  (moving-avg wins)
       |
 residual uncertainty intervals  (validation calibration)
       |
 transport-aware recommendation ranking  (haversine + cost/km)
       |
 regret@K backtest  (vs nearest-mandi baseline)
       |
 Streamlit dashboard  (Data Coverage · Forecast · Recommendation)
```

Data reads go through a DuckDB query layer (`src/mandipulse/data/store.py`). CSV files remain the
on-disk source of truth; DuckDB is the read interface per `docs/RULES.md §Architecture`.

---

## Quickstart (2 minutes, no pipeline run required)

The repo ships a bundled demo dataset (`data/sample/`) so the dashboard works from a fresh clone.

```powershell
git clone https://github.com/kaustubh-dot/MandiPulse.git
cd MandiPulse
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
streamlit run app\streamlit_app.py
```

Open `http://localhost:8501`. All three pages load on the bundled Oct 2025 snapshot — no CEDA key,
no full pipeline run. A banner in the app shows which data source is active.

> **Run the full pipeline** to replace the demo bundle with your own freshly-generated artifacts.
> See [RELEASE.md](RELEASE.md) for the 7-stage pipeline runbook.

---

## Deploy in 3 steps

1. Fork this repo (or push to your GitHub account).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **New app**.
3. Set: **Repository** = this repo, **Branch** = `main`, **Main file** = `app/streamlit_app.py`.

No secrets required. The app runs entirely on the committed demo bundle.

Paste the resulting URL in the badge at the top of this README.

---

## Run the full pipeline

If you want to generate fresh artifacts from the raw CEDA data:

```powershell
python scripts\build_clean_onion_panel.py
python scripts\build_feature_table.py
python scripts\train_baselines_7d.py
python scripts\run_baseline_sensitivity_7d.py
python scripts\train_lightgbm_7d.py
python scripts\build_forecast_intervals_7d.py
python scripts\build_recommendations_7d.py
python scripts\run_recommendation_backtest_7d.py
```

See [RELEASE.md](RELEASE.md) for the full runbook with expected outputs.

---

## Tests

```powershell
pytest
```

139 tests, 70% coverage, `--cov-fail-under=69`. Includes pipeline smoke tests, leakage guards,
temporal-split validation, recommendation scoring, and data-store parity tests.

---

## Project docs

| Doc | Contents |
|---|---|
| [RELEASE.md](RELEASE.md) | Full pipeline runbook, key metrics, deploy instructions |
| [docs/RULES.md](docs/RULES.md) | Development rules (authoritative scope guard) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, storage decision, data flow |
| [docs/TRACKER.md](docs/TRACKER.md) | Milestone history; v0.1-mvp is frozen |
| [docs/PRD.md](docs/PRD.md) | Product scope and requirements |
| [reports/modeling/](reports/modeling/) | Committed model and evaluation reports |

---

## Setup for data ingestion (optional)

The static historical dump is already used for all modeling. Re-fetch only if you need to refresh:

```powershell
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
```

Requires a CEDA API token — create `.env` from `.env.example` and set `CEDA_API_TOKEN`.
