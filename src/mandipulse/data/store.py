from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def read_csv_via_duckdb(path: Path, *, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Read a CSV through DuckDB and return a pandas DataFrame.

    Uses an in-memory DuckDB connection to SELECT * FROM read_csv_auto(path).
    parse_dates columns are coerced to datetime after the read (not via DuckDB
    inference) to match pd.read_csv + pd.to_datetime semantics exactly.
    Raises FileNotFoundError if path is absent — caller decides stop-vs-degrade.
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    # in-memory connection: cheap for MVP scale (15 mandis, ~20k rows), not cacheable
    con = duckdb.connect(database=":memory:")
    df: pd.DataFrame = con.execute(f"SELECT * FROM read_csv_auto('{Path(path).as_posix()}')").df()
    con.close()
    if parse_dates:
        for col in parse_dates:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    return df
