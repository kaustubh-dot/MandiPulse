# Milestone J Plan — DuckDB read-layer + coverage gating

**Goal:** Close the last RULES-compliance gap. RULES §Architecture mandates DuckDB as the local data
store; the pipeline is CSV-only today. Adopt DuckDB as a **read/query layer over the existing processed
CSVs** (CSV stays the on-disk source of truth), route the dashboard + evaluation reads through it, and
add a `pytest --cov` floor so coverage cannot silently regress.

This milestone is **data-access + tests + docs**. Do **NOT** change modeling (Milestone I is closed), the
recommendation math, the forecaster (moving-average stays shipped), or any report's numbers. Keep MVP
scope: Onion/Maharashtra, 7-day horizon, 15 mandis.

---

## Why this, why now

The project's own docs already chose DuckDB — `configs/data.yaml` defines
`paths.duckdb: data/processed/mandipulse.duckdb`, `.gitignore` excludes `*.duckdb`, `duckdb>=1.0` is a
declared dependency, and `docs/TECH_STACK.md` names DuckDB the "Local analytics store." Yet every read is
`pd.read_csv`. RULES §Architecture is explicit: *"Use DuckDB as the default local data store. Do not
substitute with raw CSV-only or Parquet-only workflows without documented justification."* So the
compliance move is to **adopt DuckDB**, not to write a justification that contradicts the stack docs.

**Decision already made (do not relitigate):** DuckDB is a **read-layer over CSV**, not a storage rewrite.
CSV files remain what the `build_*` / `train_*` scripts write and what git tracks for reports. DuckDB
registers those CSVs as views and serves reads via SQL. This satisfies RULES, keeps every pipeline output
reproducible and diffable, and touches only the *read* path — no `build_*` script's write path changes.

---

## Critical constraints (read before coding)

1. **CSV stays the source of truth.** Do not make any `build_*` / `train_*` script write into the
   `.duckdb` file. They keep writing CSV exactly as today. The store reads those CSVs. The `.duckdb` file
   (if persisted at all) is an ephemeral query cache, already gitignored — never a required committed
   artifact.

2. **Behavior parity, byte-for-parity frames.** The DuckDB read of each artifact must return a DataFrame
   **equivalent** to the current `pd.read_csv` (same columns, same dtypes after the existing
   `date` parsing, same row count/order-insensitive content). The dashboard and backtest must produce
   identical results. This is a refactor, not a feature — no report number may move.

3. **Preserve the graceful-degrade contract.** `data_access.py` has two contracts that must survive:
   mandatory artifacts call `_missing_artifact_error()` → `st.stop()` when absent; the optional backtest
   loader returns `None` (added in Milestone H). Routing reads through DuckDB must NOT change which
   artifacts stop the page vs. degrade. A missing CSV must still trigger the same path it does today.

4. **Windows console:** keep unicode arrows (→ … ± × —) out of any string that reaches `print()`. Reports
   are UTF-8 (arrows fine there only). Same rule that bit H and I. Also: on this machine the pytest
   `tmp_path` fixture throws a Windows `PermissionError` — use `tempfile.TemporaryDirectory()` instead
   (see `TestMissingArtifactGuard` / `TestLoadRecommendationBacktest` in `tests/test_app_data_access.py`).

5. **DuckDB connections are not Streamlit-cacheable.** A live `duckdb.DuckDBPyConnection` must not be
   stored in `@st.cache_data` (it caches by value/pickling). The loaders already return DataFrames — keep
   it that way: the store opens a connection, reads to a DataFrame, returns it. Use a fresh in-memory
   connection per read (cheap for 15 mandis) or a module-level connection guarded with
   `@st.cache_resource` — pick the simpler one that keeps the loaders returning plain DataFrames.

---

## Tasks

### J-01 — Add a `DuckDBStore` read-layer in `src/mandipulse/data/store.py`

Create a small, tested module that wraps DuckDB reads over CSV. No I/O side effects beyond reading.

```python
def read_csv_via_duckdb(path: Path, *, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Read a CSV through DuckDB and return a pandas DataFrame.

    Uses an in-memory DuckDB connection to SELECT * FROM read_csv_auto(path).
    parse_dates columns are coerced to datetime to match the current pd.read_csv
    + pd.to_datetime behavior exactly. Raises FileNotFoundError if path is absent
    (caller decides stop-vs-degrade — do not swallow it here).
    """
```

- Keep the surface minimal: one read helper is enough for the MVP. Optionally add a thin
  `DuckDBStore` dataclass holding the connection if a module-level resource is cleaner, but do not
  over-build (no migrations, no schema DDL, no write path).
- The function must reproduce the current loader semantics: e.g. `load_clean_panel` does
  `pd.read_csv(path)` then `df["date"] = pd.to_datetime(df["date"])`. The DuckDB path must yield the same
  dtypes. Decide date coercion in Python (`pd.to_datetime`) after the DuckDB read for an exact match,
  rather than relying on DuckDB's own date inference — safer for parity.
- Do **not** hardcode paths; the caller passes the `paths.py` helper result.

### J-02 — Route `data_access.py` reads through the store

- Replace the `pd.read_csv(...)` calls in `load_clean_panel`, `load_feature_table`, `load_forecasts`,
  `load_recommendations`, `load_mandi_metadata`, `load_recommendation_backtest` with
  `read_csv_via_duckdb(...)` (passing `parse_dates=["date"]` where the current code parses dates).
- **Preserve every guard exactly:** the `if not path.exists(): _missing_artifact_error(path)` checks stay
  in `data_access.py` (mandatory artifacts), and `load_recommendation_backtest` keeps its
  `if not path.exists(): return None`. The store raising `FileNotFoundError` is a backstop, not the
  primary control flow — keep the existing `path.exists()` checks so stop-vs-degrade behavior is unchanged.
- `@st.cache_data` decorators stay (they cache the returned DataFrame, which is fine). Do not cache the
  connection inside a `@st.cache_data` function.

### J-03 — Route the evaluation/script reads through the store (where it's a drop-in)

- `scripts/run_recommendation_backtest_7d.py` and the other `read_csv` consumers: migrate the **input
  reads** (panel, predictions, mandis) to `read_csv_via_duckdb` where it's a clean drop-in and does not
  change outputs. If any read is entangled with special parsing, leave it on `pd.read_csv` and note why in
  a one-line comment — parity beats coverage here. The `build_*` write paths are untouched (constraint 1).
- Do **not** migrate `utils/io.py::save_dataframe` (it writes CSV — that's the source-of-truth write path,
  which stays).

### J-04 — Coverage gating (`pytest --cov`)

- Current baseline is **58%** total (measured: `pytest --cov=mandipulse`). Add a `--cov-fail-under` floor
  to `pyproject.toml` `[tool.pytest.ini_options]` set to **just under the post-J actual** (re-measure after
  J-01..03 land — the new `store.py` plus its tests will move the number). Set the floor to
  `floor(actual) - 1` so honest refactors don't trip it, but a real regression does. State the chosen
  number in the report/PR description.
- Add `addopts = "--cov=mandipulse --cov-report=term-missing --cov-fail-under=<N>"` (or equivalent) so a
  bare `pytest` enforces it. Confirm `pytest-cov>=5.0` is already a dep (it is).
- Add a couple of **cheap, honest** unit tests to lift the easy zero-coverage utils that the MVP actually
  uses (`utils/formatting.py::dataframe_to_markdown`, `utils/text.py::slugify`/`make_mandi_id`) so the
  floor sits on tested ground rather than coincidence. Do NOT chase coverage on `ceda_client.py`,
  `tracking.py` (MLflow), or `persistence.py` — those are live-IO/script-infra and out of MVP test scope
  per RULES §Testing ("small synthetic fixtures... do not require large raw datasets").

### J-05 — Tests for the store

- `tests/test_data_store.py` (new): using a golden CSV fixture (or a `tempfile` CSV),
  `read_csv_via_duckdb` returns a DataFrame **equal** to `pd.read_csv` on the same file
  (`pd.testing.assert_frame_equal` after applying the same date parse to both), proving parity.
- A date-parsing test: `parse_dates=["date"]` yields a datetime64 column matching the
  `pd.read_csv + pd.to_datetime` result.
- A missing-file test: `read_csv_via_duckdb(nonexistent)` raises `FileNotFoundError` (use
  `tempfile.TemporaryDirectory`, not `tmp_path`).
- Keep the existing `data_access` guard tests green — they already assert stop-vs-degrade; after J-02 they
  must still pass unchanged, proving the contract survived the swap.
- All existing tests stay green (currently 106).

### J-06 — Docs

- `docs/ARCHITECTURE.md`: in the Data Flow / Local Artifacts section, note that the dashboard and backtest
  read processed CSVs **through a DuckDB query layer** (`src/mandipulse/data/store.py`); CSV remains the
  on-disk source of truth, DuckDB is the query interface. Add a one-line "Storage decision" note recording
  the read-layer-over-CSV choice and why (MVP scale; reproducible diffable CSV outputs; RULES-compliant).
- `docs/TRACKER.md`: mark J-01 (and sub-tasks) Done; move J out of Next. There is no Milestone K queued —
  after J the MVP loop is RULES-complete; note that explicitly.
- `README.md`: one line under setup/architecture that processed data is queried via DuckDB over CSV.
- `docs/RULES.md` is authoritative and already satisfied by adopting DuckDB — do **not** edit it.

### J-07 — Finish

- `python -m pytest tests/ -q` (all green; the cov floor enforced via addopts).
- `python -m pytest tests/ --cov=mandipulse --cov-report=term-missing` (confirm the number; set the floor).
- Re-run the dashboard read path is NOT required, but if quick: `streamlit run app/streamlit_app.py` and
  click Recommendation/Forecast/Coverage to confirm pages still render and degrade gracefully.
- Optionally regenerate the backtest (`python scripts/run_recommendation_backtest_7d.py`) to confirm the
  store-routed reads produce the **same** regret numbers (296.3 / 370.1) — parity proof.
- `python -m ruff check app/ tests/ src/ scripts/` and `python -m black app/ tests/ src/ scripts/ --line-length 100`.
- Commit (imperative subject, no generated-code attribution trailer) and push.

---

## Acceptance criteria

- A DuckDB read-layer (`src/mandipulse/data/store.py`) serves the dashboard and backtest reads; CSV remains
  the on-disk source of truth and no `build_*`/`train_*` write path changed.
- Behavior parity proven: existing guard tests still green, backtest numbers unchanged, dashboard pages
  render and degrade exactly as before.
- `pytest --cov` enforces a `--cov-fail-under` floor set just under the measured post-J coverage, with a
  few honest util tests so the floor sits on tested code — not on `ceda_client`/`tracking`/`persistence`.
- Store tests cover read-parity, date parsing, and the missing-file error; full suite green; ruff/black clean.
- Docs record the read-layer-over-CSV storage decision and that the MVP loop is now RULES-complete.

## Out of scope (do not do here)

- Materializing tables into a persisted `.duckdb` as the primary store (the rejected fork — CSV stays
  source of truth).
- Any change to modeling, the shipped forecaster, recommendation math, or report numbers.
- New features, new pages, new artifacts, exogenous data, extra horizons/crops/states — all post-MVP.
- Chasing coverage on live-IO/script-infra modules (CEDA client, MLflow tracking, model persistence).
