# MandiPulse Tech Stack

## Current Stack

| Layer | Tooling | Role |
|---|---|---|
| Core language | Python 3.11+ | Data pipeline, modeling, and Streamlit dashboard |
| Data processing | pandas, NumPy, DuckDB | Cleaning, feature creation, read-layer SQL |
| Modeling | scikit-learn, LightGBM | Baselines and comparison models |
| Tracking | MLflow | Local experiment metadata |
| Dashboard | Streamlit, Plotly | Offline data-science showcase |
| Frontend | Next.js 16, React 19, Tailwind v4, Recharts, Leaflet | Static Vercel frontend |
| Testing | pytest, pytest-cov, Node test runner | Python logic, export validation, TS/Python parity |
| Quality | Ruff, Black, GitHub Actions | Lint, format, CI gates |

## Deployment Targets

| Surface | Target | Notes |
|---|---|---|
| Streamlit | Streamlit Cloud | Uses committed `data/sample/`; no secrets required |
| Next.js | Vercel | Static export from `web/`; reads committed JSON |

## Data And Artifact Tools

- CSV remains the source-of-truth artifact format.
- DuckDB is the read/query interface over CSV.
- `data/sample/` is the committed demo bundle.
- `web/public/data/*.json` is committed static frontend data.
- Full generated `artifacts/`, raw data, processed data, and MLflow runs are ignored.

## Optional Future Tools

These are intentionally not blockers for the portfolio demo:

- Calendar/exogenous feature module for offline known-date signals.
- Conformal interval implementation in-repo.
- Weather, arrivals, additional crops/states, monitoring, and causal modules after explicit scope
  promotion.
- Docker Compose if a local multi-service demo becomes useful.

## Stack Decision Rules

- Prefer one simple tool per layer.
- Keep public demos secret-free and clone-runnable.
- Keep TypeScript recommendation logic parity-tested against Python.
- Do not add deep learning, orchestration, Kubernetes, or extra services until the documented demo is
  stable.
