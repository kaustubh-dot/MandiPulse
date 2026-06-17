# Milestone M Plan — FastAPI Backend (post-MVP, additive)

## Decision

Promote the **FastAPI service** from deferred to active. This is the first milestone of a
three-part full-stack track (M = API, N = Next.js frontend, O = deploy both). The backend serves
the same precomputed artifacts the Streamlit app reads, behind the contract already written in
`docs/API_SPEC.md`.

**This is a deliberate scope promotion.** RULES.md line 13 lists FastAPI as optional/future "unless
explicitly scoped and documented." M-01 does exactly that: updates RULES.md and TRACKER to record
the promotion. The narrowed MVP scope itself (1 crop, 1 state, 7-day) does **not** widen — only the
delivery surface does.

**The Streamlit app stays.** It is the data-science showcase; the API + future frontend is the
full-stack showcase. Both consume the same `src/mandipulse/` logic. No feature is removed.

### Deployment reality (why not Vercel for the API)

Vercel Python serverless caps unzipped bundles at ~250 MB and has short timeouts/cold starts. But
the serve path needs **only** pandas/numpy/duckdb/pydantic — forecasts and intervals are
precomputed CSVs, and `score_recommendations` is haversine + arithmetic. No lightgbm, shap, mlflow,
or sklearn at runtime. So:

- **FastAPI backend → Render** (free tier, slim `requirements-api.txt`, ~native install).
- **Next.js frontend → Vercel** (Milestone N).

A slim API requirements file is the lever that keeps the container small and the cold start short.

## Scope guard

- No modeling, forecaster, or number changes. The API reads existing artifacts and reuses
  `score_recommendations` **verbatim**.
- M ships **three endpoints only**: `/health`, `/forecast`, `/recommend`. `/regime` (Future) and
  `/metrics` (Post-MVP) are **not** in M.
- 7-day horizon only; Maharashtra only; onion only. Out-of-scope requests return typed errors, not
  silent fallback (RULES line 133, API_SPEC line 326).

## Reconciling API_SPEC.md to MVP reality

`docs/API_SPEC.md` was written speculatively. M-01 updates it to match what is actually built, with
each deviation documented:

| Spec says | MVP actual | Why |
|---|---|---|
| horizons 7/14/30 | **7 only** | RULES line 42 — only the 7-day horizon is evaluated |
| states MH/KA/UP | **maharashtra only** | RULES line 8 — single-state MVP |
| `market_regime` value | **`null`** | Regime detection deferred (RULES line 66); never fabricate a label |
| `top_drivers` via SHAP | **`[]`** | Shipped model is moving-average; no SHAP. Empty over invented (RULES causality) |
| `/health` `model_status: "loaded"` | **`"available"`** from artifact presence | No model is loaded at runtime; forecasts are precomputed |

## Architecture

```
api/                         # top-level, mirrors app/ (Streamlit) — delivery layer
  __init__.py
  main.py                    # FastAPI app, CORS, exception handlers, router wiring
  config.py                  # api_version, SUPPORTED_CROPS=[onion], _STATES=[maharashtra], _HORIZONS=[7]
  errors.py                  # ApiError + standard {"error":{code,message,details}} + handlers
  schemas.py                 # Pydantic models named per API_SPEC §"Pydantic Model Names"
  service.py                 # forecast lookup, mandi resolution, recommend — uses src/ only

src/mandipulse/data/loaders.py   # NEW — streamlit-free shared artifact loaders + sample fallback
```

**Reused verbatim (no changes):** `recommend.engine.score_recommendations`, `engine.risk_level`,
`data.store.read_csv_via_duckdb`, `paths.*`, `utils.text.slugify` / `make_mandi_id`,
`config.load_yaml_config`.

## Tasks

| ID | Task | Depends On |
|---|---|---|
| M-01 | Scope promotion: RULES + TRACKER + reconcile API_SPEC.md; `requirements-api.txt` | - |
| M-02 | Extract streamlit-free `data/loaders.py`; refactor `data_access.py` to delegate | - |
| M-03 | API skeleton: `main.py`, `config.py`, `errors.py`, `schemas.py` | M-01, M-02 |
| M-04 | `/health` + `/forecast` with mandi resolution + typed errors | M-03 |
| M-05 | `/recommend` reusing `score_recommendations` | M-03 |
| M-06 | `tests/test_api.py` (TestClient over `data/sample/`) | M-04, M-05 |
| M-07 | `docs/DEPLOY_API.md` (Render) + README/RELEASE notes + local run | M-04..M-06 |
| M-08 | ruff/black, full pytest, commit, push when asked, STOP for review | all |

---

### M-01 — Scope promotion + deployment deps

- `docs/RULES.md`: add a dated note under Architecture Rules that FastAPI is **promoted (post-MVP,
  additive)**; the Streamlit app remains the canonical offline showcase; MVP data scope unchanged.
- `docs/TRACKER.md`: Milestone M entry; mark X-01 (FastAPI) promoted.
- `docs/API_SPEC.md`: apply the reconciliation table above; mark `/regime` and `/metrics` as not yet
  implemented; add an "MVP implementation notes" section.
- `requirements-api.txt` (new, repo root) — slim runtime for Render:
  `fastapi`, `uvicorn[standard]`, `pandas`, `numpy`, `duckdb`, `pydantic`, `pyyaml`,
  `python-dateutil`. **No** lightgbm/shap/mlflow/sklearn/streamlit/plotly. Pin to match `.venv`.
- The `post-mvp` extra in `pyproject.toml` already has fastapi/uvicorn/httpx — install it for local
  dev (`pip install -e ".[dev,post-mvp]"`).

### M-02 — Shared streamlit-free loaders (de-couple from Streamlit)

**Problem:** the sample-fallback (`_resolve_or_sample`, `_SAMPLE_DIR`, `RUNNING_ON_SAMPLE`) lives in
`data_access.py`, which imports `streamlit`. The API must not import streamlit. Duplicating the
fallback would risk drift (RULES line 95).

**Fix:** new `src/mandipulse/data/loaders.py` (streamlit-free):
- `SAMPLE_DIR`, `resolve_or_sample(full_path, sample_name) -> (Path, used_sample: bool)`
- thin readers: `read_forecasts()`, `read_mandi_metadata()`, `read_recommendation_backtest()`,
  `read_clean_panel()`, `read_feature_table()` — each returns a plain DataFrame (no `st.cache`).

**Refactor `data_access.py`** to delegate path-resolution + reading to `loaders.py`, keeping its
public surface: `@st.cache_data` wrappers, `_missing_artifact_error` (st.stop), `RUNNING_ON_SAMPLE`.
`RUNNING_ON_SAMPLE` becomes a re-export/getter off `loaders` state so Home still reads it.

**Test churn (explicit):** the two L tests that patch `data_access._SAMPLE_DIR`
(`TestMissingArtifactGuard`, `TestLoadRecommendationBacktest`) move to patching
`mandipulse.data.loaders.SAMPLE_DIR`. `test_demo_fallback.py` likewise. Keep behavior identical;
only the patch target changes.

### M-03 — API skeleton, schemas, errors

- `schemas.py`: Pydantic v2 models exactly per API_SPEC names — `HealthResponse`, `ForecastRequest`,
  `ForecastResponse`, `RecommendationRequest`, `FarmerLocation`, `MandiRecommendation`,
  `RecommendationResponse`, `ErrorResponse`. `market_regime: str | None = None`,
  `top_drivers: list[str] = []`.
- `errors.py`: `ApiError(code, message, http_status, details)` exception; an exception handler that
  renders the standard `{"error": {...}}` body; override FastAPI's `RequestValidationError` to emit
  `VALIDATION_ERROR` (422) in the same shape.
- `config.py`: `API_VERSION="0.1.0"`, `SUPPORTED_CROPS={"onion"}`, `SUPPORTED_STATES={"maharashtra"}`,
  `SUPPORTED_HORIZONS={7}`. CORS origins from env `MANDIPULSE_ALLOWED_ORIGINS` (comma-sep), default
  `*` — acceptable for a public, read-only, no-auth, no-secrets demo (document the choice).
- `main.py`: create app, add CORSMiddleware, register handlers, include routes. `title`,
  `version`, OpenAPI docs at `/docs` (free interactive demo — a resume bonus).

### M-04 — `/health` + `/forecast`

- **Mandi resolution** (`service.py`): map request `mandi` (display name or slug) → `market_id` via
  metadata. Compare `slugify(request.mandi)` against the forecast frame's `mandi` column and the
  metadata's slugified `market_name`. No match → `ApiError("MANDI_NOT_FOUND", 404)`. Never guess
  (API_SPEC line 62).
- **/health**: return `status`, `api_version`, `data_status` (from artifact presence via loaders),
  `latest_data_date` (max `as_of_date`), `model_version` (from forecast frame), `supported_crops`,
  `supported_horizons`. Missing data → `data_status: "unavailable"` (200, honest) — do not crash.
- **/forecast**: validate crop/state/horizon (→ `UNSUPPORTED_*`), resolve mandi, look up the row,
  compute `risk_level` from `(upper-lower)/forecast` via `engine.risk_level` + config thresholds,
  return `ForecastResponse` with `market_regime=None`, `top_drivers=[]`. Missing forecast row for a
  valid mandi → `INSUFFICIENT_HISTORY` (409).

### M-05 — `/recommend`

- Validate crop + `candidate_states` (MH only) + horizon. Load forecasts + mandi metadata via
  loaders; drop coordless mandis (mirror the Streamlit page). Call `score_recommendations` with the
  request `farmer_location` and config defaults (allow optional per-request overrides for
  cost/km, road factor, penalty — defaults from `configs/recommendation.yaml`).
- Build `RecommendationResponse`: `recommended_mandi` = rank 1; `alternatives` = full ranked list
  with transport cost, net price, bounds, risk-adjusted score, risk level, `market_regime=None`.
  Carry `reason` from the engine output. Assert rank-1 == recommended in a test.

### M-06 — Tests (CI-safe, over the committed bundle)

`tests/test_api.py` using `fastapi.testclient.TestClient` (httpx already in `post-mvp`):
- `/health` → 200, `data_status == "available"` (bundle is committed).
- `/forecast` happy path → 200, has lower/upper bounds + confidence; `UNSUPPORTED_CROP`,
  `UNSUPPORTED_STATE`, `UNSUPPORTED_HORIZON` (14), `MANDI_NOT_FOUND`, `VALIDATION_ERROR` (bad body).
- `/recommend` happy path → 200, `len(alternatives) > 1`, rank-1 == `recommended_mandi`, transport
  cost present, every `risk_level in {low,medium,high}`; validation errors as above.
- All run against `data/sample/`, so CI on a clean checkout passes.
- Coverage: `api/` is top-level (excluded from `--cov=mandipulse`, like `app/`); the new
  `data/loaders.py` is covered. Re-measure, bump `--cov-fail-under` to `(measured-1)` if it rises;
  never lower.

### M-07 — Deploy docs + local run

- `docs/DEPLOY_API.md`: Render setup — Build `pip install -r requirements-api.txt`, Start
  `uvicorn api.main:app --host 0.0.0.0 --port $PORT`; free-tier cold-start (~30-60 s spin-up) note;
  `MANDIPULSE_ALLOWED_ORIGINS` env for the Vercel origin (set in N).
- README: add an "API" section — local run (`uvicorn api.main:app --reload`), `/docs` link, and a
  "backend deployment" pointer. RELEASE.md: note the optional API surface.
- Local smoke: `uvicorn api.main:app --reload`, hit `/health`, `/docs`.

### M-08 — Finalize

- `ruff check api/ src/ scripts/ tests/` + `black --check` (skip `.claude/skills/`).
- Full `pytest` green at the (possibly raised) floor.
- TRACKER → M Done. Commit. **Push only when asked.** STOP for Opus review.

## Constraints (carried)

- No `→ … ± × —`/emoji in any `print()` path; UTF-8 file writes fine.
- `tempfile.TemporaryDirectory()`, never the `tmp_path` fixture (Windows PermissionError).
- No `Co-Authored-By: Claude` / "Generated with Claude Code" in commits or PRs.
- CORS `*` is a deliberate read-only-demo decision; revisit if auth/secrets are ever added.

## Out of scope for M (still deferred)

`/regime`, `/metrics`, SHAP `top_drivers`, real `market_regime`, horizons 14/30, non-MH states,
auth/rate-limiting, the Next.js frontend (Milestone N), deployment execution on Render (the agent
preps everything; connecting the Render account is a user step in N/O).

## Next

- **N — Next.js + Tailwind + shadcn/ui frontend** on Vercel, consuming this API.
- **O — deploy both** (Render API + Vercel frontend, wire CORS + env).
