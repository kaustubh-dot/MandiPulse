from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(column) for column in df.columns]
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join("---" for _ in columns) + " |")
    for _, row in df.iterrows():
        values = [str(row[column]) for column in df.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile the narrowed Onion/Maharashtra raw dump.")
    parser.add_argument(
        "--input",
        default="data/raw/ceda/onion_maharashtra/onion_maharashtra_prices_raw.csv",
    )
    parser.add_argument(
        "--output",
        default="reports/data_quality/onion_maharashtra_profile.md",
    )
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, parse_dates=["date"])
    if df.empty:
        raise SystemExit(f"No rows found in {input_path}")

    df["date_day"] = df["date"].dt.date
    df["valid_price"] = (
        df["modal_price"].notna()
        & (df["modal_price"] > 0)
        & df["min_price"].notna()
        & df["max_price"].notna()
        & (df["min_price"] <= df["modal_price"])
        & (df["modal_price"] <= df["max_price"])
    )

    market_summary = (
        df.groupby(["market_id", "market_name", "district_id", "district_name"], dropna=False)
        .agg(
            rows=("modal_price", "size"),
            valid_rows=("valid_price", "sum"),
            active_days=("date_day", "nunique"),
            first_date=("date_day", "min"),
            last_date=("date_day", "max"),
            median_modal_price=("modal_price", "median"),
            min_modal_price=("modal_price", "min"),
            max_modal_price=("modal_price", "max"),
        )
        .reset_index()
    )
    market_summary["valid_row_pct"] = (
        market_summary["valid_rows"] / market_summary["rows"] * 100
    ).round(2)
    market_summary = market_summary.sort_values(
        ["active_days", "valid_rows", "rows"],
        ascending=False,
    )

    top_markets = market_summary.head(args.top_n)
    invalid_rows = df.loc[~df["valid_price"]]
    duplicate_count = int(
        df.duplicated(["date_day", "commodity_id", "market_id"], keep=False).sum()
    )

    markdown = [
        "# Onion/Maharashtra Data Profile",
        "",
        "## Dataset",
        "",
        f"- Input: `{input_path}`",
        f"- Rows: {len(df):,}",
        f"- Markets: {df['market_id'].nunique():,}",
        f"- Districts: {df['district_id'].nunique():,}",
        f"- Date range: {df['date_day'].min()} to {df['date_day'].max()}",
        f"- Invalid price rows: {len(invalid_rows):,}",
        f"- Duplicate market-date rows: {duplicate_count:,}",
        "",
        "## Top Markets By Coverage",
        "",
        dataframe_to_markdown(top_markets),
        "",
        "## Notes",
        "",
        "- Select the first 10-15 markets only after checking missingness and geographic spread.",
        "- Do not forward-fill gaps longer than 3 consecutive reporting days.",
        "- Add an `is_imputed` flag if short gaps are filled later.",
    ]
    output_path.write_text("\n".join(markdown), encoding="utf-8")

    print(f"Wrote {output_path}")
    print(top_markets[["market_id", "market_name", "district_name", "active_days", "rows"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
