# MandiPulse India

**Transport-cost-aware mandi decision intelligence for Maharashtra onion farmers.**

[![Tests](https://img.shields.io/badge/tests-235%20passed-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-78.05%25-green)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

## What it does

Maharashtra onion farmers choose which mandi (market) to sell at based on word-of-mouth and nearest
distance. They ignore transport cost, forecast uncertainty, and historical ranking quality. A farmer
who drives 40 km to a mandi with a higher forecast price can still lose money if transport costs
exceed the price premium.

MandiPulse forecasts 7-day onion prices across **15 Maharashtra mandis**, subtracts transparent
distance-based transport cost, and ranks mandis by **transport-adjusted net expected price** with
uncertainty bounds shown as separate evidence. The demo snapshot is frozen at **2025-10-30**: it is
a reproducible portfolio artifact, not a live price feed.

## Architecture

A Python analytical core produces committed artifacts; three read-only surfaces consume them.

```
CEDA/AGMARKNET cached extract
       |
 clean daily panel  (15 mandis × 2020–2025)
       |
 leakage-safe features  (lags/rolling/calendar — no future data)
       |
 temporal split  (train/val/test — no random splits)
       |
 model comparison  (7-day moving average wins; LightGBM reported, unshipped)
       |
 residual uncertainty intervals  (validation-calibrated)
       |
 transport-adjusted recommendation ranking  (haversine × 1.3 road factor + cost/km)
       |
 regret@K backtest  (vs nearest-mandi baseline)
       |
 committed artifacts  (data/sample/*.csv, web/public/data/*.json, schemas validated)
       |
       +-- Next.js static export  (web/ — Decision · Forecast · Coverage, re-ranks in TS)
       +-- Streamlit dashboard    (app/ — same four destinations, shared Python ranking)
       +-- FastAPI service        (api/ — /health, /forecast, /recommend over the same bundle)
```

Data reads go through a DuckDB query layer (`src/mandipulse/data/store.py`). CSV files remain the
on-disk source of truth; DuckDB is the read interface per `docs/RULES.md §Architecture`. The
Next.js TypeScript ranking is parity-tested against Python at a 0.01 INR/qtl tolerance.

## Two-minute demo

Install once (PowerShell):

```powershell
git clone https://github.com/kaustubh-dot/MandiPulse.git
cd MandiPulse
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,post-mvp]"
```

No API key or pipeline run is needed — everything below runs on the committed demo bundle.

**Next.js web product**

```powershell
cd web
npm install
npm run dev
```

1. Open `http://localhost:3000` — the Overview states the thesis, shows a live decision preview at
   artifact defaults, and links the evaluation evidence (`/#method`).
2. Click **Decision** in the rail (or go to `http://localhost:3000/recommend`). Inputs are prefilled;
   click **Compare mandis** to get the ranked list with arithmetic, alternatives, table, and map.
3. Change quantity, transport rate, or radius — results re-rank instantly and the decision state is
   serialized into the URL; use the copy-link action to save a reproducible scenario.
4. Open **Forecast** (`/forecast`) and pick a mandi for history plus the 7-day interval, then
   **Coverage** (`/coverage`) for row definitions and per-mandi comparability.

**Streamlit technical dashboard**

```powershell
streamlit run app\streamlit_app.py
```

1. Open `http://localhost:8501` — Overview shows the same decision preview at artifact defaults.
2. Open **Decision** in the sidebar. Edit any input; the workbench compares mandis on every edit.
3. Open **Forecast** and **Coverage** from the sidebar for the matching evidence views.

**FastAPI service**

```powershell
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# Swagger UI at http://localhost:8000/docs
```

| Endpoint | Description |
|---|---|
| `GET /health` | Data and API readiness |
| `POST /forecast` | 7-day price + uncertainty interval for a mandi |
| `POST /recommend` | Transport-adjusted mandi ranking |

## Tests and build

Python quality gate:

```powershell
ruff check api app src scripts tests
black --check api app src scripts tests
pytest -q
```

235 Python tests pass at 78.05% coverage against a 70% floor. The suite covers pipeline smoke tests,
leakage guards, temporal-split validation, recommendation scoring, schema validation, Streamlit
smoke tests, and golden-fixture comparisons under `tests/golden/`.

Web quality gate (from `web/`, Node 20.9+):

```powershell
npm run lint
npm run typecheck
npm test                # logic + Python/TypeScript parity fixtures
npm run test:components # jsdom component suites
npm run build           # production static export (7 routes)
npx playwright test     # browser + accessibility suite against the built export
```

CI runs all of the above on GitHub Actions (see `.github/workflows/ci.yml`).

## Honest results

LightGBM was trained and evaluated — it **did not beat the 7-day moving-average baseline** on the
held-out test split. The baseline ships. This is reported transparently
([reports/modeling/lightgbm_metrics_7d.md](reports/modeling/lightgbm_metrics_7d.md)).

| Model | Test MAE (INR/qtl) | Ships? |
|---|---|---|
| `moving_average_7d` | **139.57** | Yes |
| `ridge` | 224.43 | No |
| `lightgbm` | 188.2 | No |
| `lightgbm_residual` | 195.63 | No |

The shipped residual interval reports **86.71% empirical coverage** on its test split against a 90%
nominal level ([reports/modeling/forecast_intervals_7d.md](reports/modeling/forecast_intervals_7d.md)).
It falls short of nominal, so the interval is an observed uncertainty estimate, not a guarantee. The
Phase 3 observed-target re-evaluation
([reports/modeling/phase3_evaluation.md](reports/modeling/phase3_evaluation.md)) keeps a separate
internal population: 792 eligible rows, MAE 133.61, 86.87% conditional-residual and 90.91%
split-conformal coverage.

Recommendation backtest vs nearest-mandi baseline (held-out test window,
[reports/modeling/recommendation_backtest_7d.md](reports/modeling/recommendation_backtest_7d.md)):

| Metric | Value |
|---|---|
| Mean regret@1 | 296.3 INR/qtl |
| Nearest-mandi baseline regret | 370.1 INR/qtl |
| Beats nearest-mandi | 74.4% of dates |

What makes this credible:

- Temporal train/validation/test splits only; no random split on time-series data.
- Baseline honesty: LightGBM variants are reported even though they lose.
- Forecasts include uncertainty intervals with measured empirical coverage.
- Recommendations are evaluated with regret@K against a nearest-mandi baseline.
- The whole demo is clone-runnable from committed `data/sample/` artifacts; no secrets required.

## Limitations

- **Frozen demo data.** The snapshot ends on **2025-10-30** and is not a live feed. Results are
  decision-support examples on historical data, not current market guidance.
- **Transport is a scenario estimate, not a carrier quote.** Road distance is haversine distance ×
  a configurable `1.3` factor, priced at a configurable rate (default `4.0 INR/km/quintal`). It is
  not routing-engine distance or freight pricing; Phase 3 sensitivity tests 0.8x/1.0x/1.2x rates.
- **Uncertainty does not change the ranking order.** The public interval has one global width, so
  its penalty is identical for every eligible mandi in a snapshot. Ranking is driven by forecast
  price minus transport cost; uncertainty is displayed as separate evidence.
- **Moving-average policy ships; the model comparison does not.** LightGBM and residual-LightGBM
  stay unshipped because they lost on held-out MAE. No stronger claim is made for them.
- **Single crop, single state.** Onion, Maharashtra, 15 mandis, 7-day horizon only. Other crops,
  states, horizons, live ingestion, and causal claims are out of scope by design.

## Where the evidence lives

| Location | Contents |
|---|---|
| [docs/portfolio/](docs/portfolio/) | Release gates, checkpoint history, rescue plan, current state |
| [tests/golden/](tests/golden/) | Golden fixtures pinning panel, features, forecasts, recommendations |
| [reports/modeling/](reports/modeling/) | Baseline, LightGBM, interval, backtest, and Phase 3 reports |
| [web/public/data/meta.json](web/public/data/meta.json) | Snapshot date, policy bounds, ranking config for the exported bundle |
| [web/public/data/manifest.json](web/public/data/manifest.json) | Artifact/input/code/config hashes for strict export verification |

Regenerate contracts when source artifacts change:

```powershell
python scripts\build_demo_sample.py
python scripts\build_web_export.py
python scripts\validate_web_export.py
```

## Run the full pipeline (optional)

To regenerate local artifacts from the cached raw extract instead of the committed
demo bundle (optionally fetch fresh CEDA data first):

```powershell
# Optional fresh fetch — requires a CEDA API token in .env (see below)
python scripts\fetch_ceda_onion_maharashtra.py --from-date 2020-01-01 --to-date 2026-06-13
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

Requires a CEDA API token for the fetch step — create `.env` from `.env.example` and set
`CEDA_API_TOKEN`. See [RELEASE.md](RELEASE.md) for the full runbook with expected outputs.

## Deploy (optional)

Deploy the release branch `finish/portfolio-release` — it carries the portfolio release
(the tagged commit); `main` may not contain it yet.

1. **Streamlit Cloud:** [share.streamlit.io](https://share.streamlit.io) → New app → repository,
   branch `finish/portfolio-release`, Main file `app/streamlit_app.py`. No secrets required.
2. **Vercel (Next.js):** import the repo with **Root Directory** set to `web` and the
   production branch set to `finish/portfolio-release` (or deploy that branch explicitly).
   Static export; no environment variables required. See
   [docs/DEPLOY_FRONTEND.md](docs/DEPLOY_FRONTEND.md).
3. **Render (FastAPI, optional):** deploy `api/` from `finish/portfolio-release` with
   `requirements-api.txt`; start command `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
   See [docs/DEPLOY_API.md](docs/DEPLOY_API.md).

Public URLs for this release are recorded in
[docs/portfolio/RELEASE_GATES.md](docs/portfolio/RELEASE_GATES.md) once deployment verification
completes.

## Project docs

| Doc | Contents |
|---|---|
| [PRODUCT.md](PRODUCT.md) | Product truth: users, purpose, constraints, evidence |
| [RELEASE.md](RELEASE.md) | Full pipeline runbook, key metrics, deploy instructions |
| [docs/RULES.md](docs/RULES.md) | Development rules (authoritative scope guard) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, storage policy, ranking boundary |
| [docs/APP_FLOW.md](docs/APP_FLOW.md) | Authoritative product-flow specification |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Approved finish-track execution sequence |
| [docs/portfolio/RELEASE_GATES.md](docs/portfolio/RELEASE_GATES.md) | Release acceptance checklist |
| [docs/TRACKER.md](docs/TRACKER.md) | Milestone history; v0.1-mvp is frozen |
