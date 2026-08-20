# MandiPulse India

**Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers.**

[![Tests](https://img.shields.io/badge/tests-206%20passed-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-75%25-green)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

## Demo surfaces

| Surface | URL | Stack |
|---|---|---|
| Streamlit dashboard | [mandipulse.streamlit.app](https://mandipulse.streamlit.app/) | Python + Streamlit |
| FastAPI service | _local snapshot API; optional Render deploy — see [docs/DEPLOY_API.md](docs/DEPLOY_API.md)_ | FastAPI |
| Next.js frontend | _updated frontend packaging is intentionally deferred to a separate commit_ | Next.js |

---

## Product surfaces

The Streamlit dashboard and FastAPI snapshot service are part of this release. The updated
recommendation-first Next.js experience is being packaged separately and should not be described as
publicly deployed until its dedicated frontend commit, CI pass, and browser smoke test are complete.

The snapshot is intentionally frozen at **2025-10-30**. It is a reproducible portfolio artifact,
not a live price feed.

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

The committed public v1 forecast bundle uses the residual interval from the shipped all-row
calibration and reports **86.71% empirical coverage** on its test split. This is below the nominal
level, so the interval is an observed uncertainty estimate, not a guarantee, and the shortfall is
reported rather than described as conservative. The Phase 3 observed-target re-evaluation is kept
separate in [the evidence report](reports/modeling/phase3_evaluation.md): conditional residual
coverage is 86.87%, split-conformal coverage is 90.91%, and the pre-declared rule adopts
split-conformal for that evaluation population. No public v1 field or schema is changed by the
internal evidence export.

Recommendation backtest (regret@K vs nearest-mandi baseline, held-out test window):

| Metric | Value |
|---|---|
| Mean regret@1 | 296.3 INR/qtl |
| Nearest-mandi baseline regret | 370.1 INR/qtl |
| Beats nearest-mandi | 74.4% of dates |

---

## What makes this credible

- Temporal train/validation/test splits only; no random split on time-series data.
- Baseline honesty: LightGBM and residual-LightGBM are reported even though they lose.
- Forecasts include uncertainty intervals with measured empirical coverage.
- Recommendations are evaluated with regret@K against a nearest-mandi baseline.
- The demo is clone-runnable from committed `data/sample/` artifacts; no secrets required.
- The separately packaged Next.js ranking has a recorded local Python/TypeScript parity tolerance
  of 0.01 INR/qtl; publish that claim with the frontend commit and its CI evidence.

## ML Engineer case study

**Problem.** A higher mandi price is not necessarily a better farmer outcome once distance,
transport cost, and forecast uncertainty are included.

**Approach.** Build a point-in-time daily panel for 15 Maharashtra onion mandis, compare temporal
models, calibrate uncertainty on observed targets, and rank only candidates whose forecast as-of
date matches the canonical bundle date. The shipped baseline is the 7-day moving average because
it beats the trained LightGBM variants on the untouched held-out split.

**Evidence.** The public v1 bundle reports 86.71% all-row test coverage; the Phase 3 observed-target
holdout has 792 eligible rows, with 86.87% conditional-residual coverage and 90.91% split-conformal
coverage. The multi-origin recommendation evidence reports matched observed-target denominators
and explicit 0.8x/1.0x/1.2x transport-cost scenarios. These are measured decision-support results,
not profit guarantees. The strict export process generates a manifest with snapshot, model,
configuration, input, code, and artifact hashes; that bundle will be published with the separate
frontend commit.

**Engineering lesson.** The valuable part is the contract between data, model, policy, API, and
UI: the same as-of date, denominator, transport assumptions, and uncertainty semantics must survive
export, browser ranking, and documentation.

### Decision-model limitations

- Road distance is approximated as haversine distance multiplied by a configurable `1.3` factor;
  it is not routing-engine distance.
- The baseline `4.0 INR/km/quintal` rate is a configurable evaluation scenario, not a live carrier
  quote. Phase 3 tests 0.8x, 1.0x, and 1.2x versions of that rate.
- The public v1 residual interval has one global width. Its penalty is therefore the same for every
  eligible mandi in a snapshot and does not change their relative ordering. The interval remains
  useful for coverage reporting and relative risk labels; transport cost and forecast price drive
  the current public ranking.

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
       |
 build_web_export.py  (→ web/public/data/*.json)
       |
Next.js frontend  (static export — decision inputs re-rank in TS)
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
> See [RELEASE.md](RELEASE.md) for the full pipeline runbook.

---

## API (FastAPI)

A REST API exposes the same forecasts and recommendations as a separate demo surface.

```powershell
# Local run
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# Swagger UI at http://localhost:8000/docs
```

| Endpoint | Description |
|---|---|
| `GET /health` | Data and API readiness |
| `POST /forecast` | 7-day price + uncertainty interval for a mandi |
| `POST /recommend` | Transport-adjusted mandi ranking |

All three endpoints run over the same committed `data/sample/` bundle — no pipeline run required.
FastAPI is a local snapshot surface by default; see [docs/DEPLOY_API.md](docs/DEPLOY_API.md) for the
optional Render deployment procedure.

---

## Frontend (Next.js)

The separately packaged static frontend reads generated JSON from `web/public/data/` and re-ranks
recommendations in the browser as the farmer location, transport rate, and maximum radius change.
Quantity is used to show the corresponding lot-level net estimate.

```powershell
python scripts\build_web_export.py
cd web
npm install
npm test
npm run build
npm run dev
```

To deploy it on Vercel, set **Root Directory** to `web`. No environment variables are required.

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
python scripts\run_phase3_evaluation.py
python scripts\build_demo_sample.py
python scripts\build_web_export.py
python scripts\validate_web_export.py
```

See [RELEASE.md](RELEASE.md) for the full runbook with expected outputs.

---

## Tests

```powershell
pytest
```

206 Python tests, 74.90% coverage, `--cov-fail-under=70`. Includes pipeline smoke tests, leakage guards,
temporal-split validation, recommendation scoring, and data-store parity tests.

Web gates:

```powershell
cd web
npm test
npm run build
```

GitHub Actions currently runs the Python lint/format/test gate. The Next.js source, generated public
data, strict export/schema gate, and updated frontend parity/build evidence are intentionally
reserved for a separate frontend commit.

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
