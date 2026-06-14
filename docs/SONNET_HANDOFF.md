# Sonnet Handoff — MandiPulse India MVP Completion

Paste this entire file as your first message when starting a new Claude session to complete the MandiPulse project.

---

## Your mission

You are completing the **MandiPulse India MVP** — a transport-cost-aware mandi decision-intelligence system (Onion/Maharashtra, 7-day price forecast, offline static showcase).

Work directory: the repo root (wherever this file lives).

The pipeline is already implemented and producing artifacts. Your job is to finish it: package refactor, correctness fixes, MLflow tracking, Streamlit dashboard, tests, and docs refresh — following the approved roadmap exactly.

---

## Read first (in this order)

1. `docs/COMPLETION_ROADMAP.md` — the approved 7-milestone roadmap; this is your primary task list
2. `CLAUDE.md` — project conventions (code style, hard rules, build commands)
3. `docs/RULES.md` — hard constraints (temporal split, INR/quintal, MVP scope, no commit of secrets/artifacts)
4. `docs/APP_FLOW.md` + `docs/DESIGN.md` — read these before building Milestone E (dashboard)
5. `configs/recommendation.yaml` — source of truth for recommendation params (road factor, cost per km, penalty weight, risk thresholds)

---

## Locked decisions — do not re-litigate

- **Full remaining MVP**: complete all milestones A–G as described in the roadmap.
- **Full package refactor**: all shared logic moves into `src/mandipulse/`. Scripts become thin CLIs.
- **Stay offline**: the raw CEDA dump is cached locally (data ends 2025-10-30); no live API key needed. Do not add any live-fetch calls.
- **`configs/recommendation.yaml` wins**: recommendation params come from this file, not hardcoded defaults. CLI flags may still override for demo purposes.
- **Temporal split only**: train < validation < test by date. Never random-split. Never use future data as features.

---

## Skills to invoke

Before starting, invoke these skills to load their behavioral guidelines:

- `/python-patterns` — Pythonic idioms, type hints, PEP 8 (available in `.claude/skills/python-patterns/`)
- `/error-handling` — typed errors, retry patterns (available in `.claude/skills/error-handling/`)

---

## How to work

### Track everything with TodoWrite

Before starting each milestone, write out its tasks as todos. Mark each task `in_progress` when you start it, `completed` immediately when done. Never have more than one task `in_progress` at a time.

### Move, then thin (the golden-file strategy)

For every refactor milestone (A, B):
1. First, run the existing pipeline to produce fresh artifacts (if not already present).
2. Copy current artifacts to `tests/golden/` **before** any code changes (task A1).
3. Move code bodies verbatim — no logic changes during the move.
4. Re-run the pipeline; diff output CSVs against goldens (≤1e-6 tolerance). If they match, the move is clean.
5. Only then apply fixes (Milestone C).

### Single source of truth for mandi_id

`make_mandi_id(market_name, state="maharashtra")` must exist in exactly one place: `src/mandipulse/utils/text.py`. Every script and the recommendation engine must import from there. Delete all inline copies.

### Config wiring pattern

All scripts that have config-equivalent parameters must load the YAML first, use config values as defaults, and let CLI flags override. Example:
```python
cfg = load_yaml_config(resolve_project_path("configs/recommendation.yaml"))
road_factor = args.road_factor or cfg["transport_cost"]["road_distance_factor"]
```

### Quality gate after every milestone

After completing each milestone, run:
```bash
ruff check . && black --check . && pytest -q
```
Do not proceed to the next milestone until these pass (or until tests exist — for A and B, just ruff+black).

---

## Milestone execution order

Execute milestones strictly in order A → B → C → D → E → F → G. Each builds on the last.

| Milestone | Goal | Key acceptance check |
|-----------|------|----------------------|
| A | Foundation: utils package + golden files | CSVs reproduce ≤1e-6; ruff+black clean |
| B | Modeling package: move shared code out of scripts/ | Golden metrics unchanged; no `from train_baselines_7d import` |
| C | Correctness fixes: config wiring, market_id join, purge gap, coverage labels | Recommendation report shows road=1.3, penalty=0.3, thresholds 10/25 |
| D | Persistence + MLflow | `artifacts/models/lightgbm_7d.joblib` exists; MLflow run visible |
| E | Streamlit dashboard | `streamlit run app/streamlit_app.py` opens all 3 pages offline |
| F | pytest suite | `pytest -q` green |
| G | Docs refresh | README → install → pipeline → streamlit → pytest works for a new contributor |

---

## Package import pattern for scripts

Every script that imports from `mandipulse` must add this shim at the top (before the `mandipulse` import), so it resolves whether run as `python scripts/foo.py` or `python -m scripts.foo`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
```

This pattern already exists in `scripts/fetch_ceda_onion_maharashtra.py` — copy it exactly.

---

## Key files to know before you start

| File | Purpose |
|------|---------|
| `src/mandipulse/config.py` | `PROJECT_ROOT`, `resolve_project_path(rel)`, `load_yaml_config(path)` — use these everywhere |
| `scripts/train_baselines_7d.py` | De-facto shared library (SplitConfig, predict_baselines, metrics, etc.) — this is what Milestone B moves into the package |
| `scripts/build_forecast_intervals_7d.py` | Imports 14 symbols from train_baselines_7d — fragile; fixed in Milestone B |
| `scripts/build_recommendations_7d.py` | Uses hardcoded params instead of configs/recommendation.yaml — fixed in Milestone C |
| `configs/recommendation.yaml` | Correct params: road_distance_factor=1.3, cost_per_km_per_quintal=4.0, uncertainty_penalty_weight=0.3, risk thresholds 10%/25% |
| `data/external/mvp_mandis.csv` | 15 MVP mandis with coordinates; used for transport cost |
| `artifacts/forecasts/forecast_outputs_7d.csv` | 15 rows × 15 cols; input to recommendation engine |

---

## Before declaring the project done

Run the full pipeline end-to-end from a clean state:

```bash
python -m pip install -e ".[dev]"
python scripts/build_clean_onion_panel.py
python scripts/build_feature_table.py
python scripts/train_baselines_7d.py
python scripts/run_baseline_sensitivity_7d.py
python scripts/train_lightgbm_7d.py
python scripts/build_forecast_intervals_7d.py
python scripts/build_recommendations_7d.py
ruff check . && black --check . && pytest -q
streamlit run app/streamlit_app.py   # verify all 3 pages work
```

Then:
1. Run `/code-review` (high effort) on the final diff.
2. Run `/security-review` on the app layer (no secrets in code, no path traversal in file loaders).
3. Update `docs/COMPLETION_ROADMAP.md` — check off all 17 TODO items.
4. Flip milestone rows in `docs/TRACKER.md` to Done with today's date.

---

## Hard constraints (from docs/RULES.md)

- Temporal split only — train < validation < test by date. No `random_state` splits on time-series data.
- All prices in INR/quintal.
- MVP scope only: 1 crop (Onion), 1 state (Maharashtra), ~10–15 mandis, 7-day horizon.
- Do not add: FastAPI, SHAP, CatBoost, 14/30-day horizons, additional crops/states, live data refresh.
- Never commit: `.env`, raw CEDA CSVs, model `.joblib` files, `mlruns/`, `artifacts/` (except reports).
- No hardcoded paths — always use `resolve_project_path()` from `mandipulse.config`.
