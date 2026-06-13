from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(column) for column in df.columns]
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in df.columns) + " |")
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the clean Onion/Maharashtra MVP panel.")
    parser.add_argument(
        "--raw-input",
        default="data/raw/ceda/onion_maharashtra/onion_maharashtra_prices_raw.csv",
    )
    parser.add_argument("--mandis", default="data/external/mvp_mandis.csv")
    parser.add_argument(
        "--output",
        default="data/processed/onion_maharashtra/clean_mandi_prices.csv",
    )
    parser.add_argument(
        "--report",
        default="reports/data_quality/onion_maharashtra_clean_panel.md",
    )
    parser.add_argument("--max-impute-gap-days", type=int, default=3)
    return parser.parse_args()


def aggregate_duplicates(raw: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    duplicate_count = int(raw.duplicated(["date", "market_id"], keep=False).sum())
    aggregated = (
        raw.groupby(
            [
                "date",
                "commodity_id",
                "commodity_name",
                "state_id",
                "state_name",
                "district_id",
                "district_name",
                "market_id",
                "market_name",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            min_price=("min_price", "min"),
            max_price=("max_price", "max"),
            modal_price=("modal_price", "median"),
            source_rows=("modal_price", "size"),
        )
        .sort_values(["market_id", "date"])
    )
    return aggregated, duplicate_count


def add_short_gap_imputations(
    panel: pd.DataFrame,
    max_gap_days: int,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    price_columns = ["min_price", "max_price", "modal_price"]

    for _, group in panel.groupby("market_id", sort=False):
        group = group.sort_values("date").copy()
        missing = group["modal_price"].isna()
        run_id = missing.ne(missing.shift()).cumsum()
        run_lengths = missing.groupby(run_id).transform("sum")
        previous_seen = group["modal_price"].notna().cummax()
        next_seen = group["modal_price"].notna()[::-1].cummax()[::-1]
        short_internal_gap = missing & previous_seen & next_seen & (run_lengths <= max_gap_days)

        group["is_imputed"] = False
        group["imputation_method"] = ""
        if short_internal_gap.any():
            filled_prices = group[price_columns].ffill()
            group.loc[short_internal_gap, price_columns] = filled_prices.loc[
                short_internal_gap,
                price_columns,
            ]
            group.loc[short_internal_gap, "is_imputed"] = True
            group.loc[short_internal_gap, "imputation_method"] = (
                f"ffill_gap_le_{max_gap_days}_days"
            )

        group["is_observed"] = group["source_rows"].fillna(0).astype(int) > 0
        group["quality_flag"] = "ok"
        group.loc[group["is_imputed"], "quality_flag"] = "imputed_short_gap"
        group.loc[
            group["modal_price"].isna() & ~group["is_imputed"],
            "quality_flag",
        ] = "missing_long_gap"
        frames.append(group)

    return pd.concat(frames, ignore_index=True)


def build_panel(
    raw: pd.DataFrame,
    mandis: pd.DataFrame,
    max_gap_days: int,
) -> tuple[pd.DataFrame, dict]:
    raw = raw.copy()
    raw["date"] = pd.to_datetime(raw["date"]).dt.date
    raw = raw[raw["market_id"].isin(mandis["market_id"])]

    invalid_mask = (
        raw["modal_price"].isna()
        | (raw["modal_price"] <= 0)
        | raw["min_price"].isna()
        | raw["max_price"].isna()
        | (raw["min_price"] > raw["modal_price"])
        | (raw["modal_price"] > raw["max_price"])
    )
    invalid_rows = int(invalid_mask.sum())
    raw = raw.loc[~invalid_mask].copy()

    aggregated, duplicate_count = aggregate_duplicates(raw)
    market_meta = (
        aggregated[
            [
                "commodity_id",
                "commodity_name",
                "state_id",
                "state_name",
                "district_id",
                "district_name",
                "market_id",
                "market_name",
            ]
        ]
        .drop_duplicates("market_id")
        .set_index("market_id")
    )

    global_dates = pd.date_range(aggregated["date"].min(), aggregated["date"].max(), freq="D").date
    full_index = pd.MultiIndex.from_product(
        [sorted(mandis["market_id"].unique()), global_dates],
        names=["market_id", "date"],
    )
    panel = (
        aggregated.set_index(["market_id", "date"])
        .reindex(full_index)
        .reset_index()
        .sort_values(["market_id", "date"])
    )

    for column in market_meta.columns:
        panel[column] = panel["market_id"].map(market_meta[column])

    panel["crop"] = "onion"
    panel["crop_id"] = "onion"
    panel["state"] = "maharashtra"
    panel["district"] = panel["district_name"].fillna("").map(slugify)
    panel["mandi"] = panel["market_name"].fillna("").map(slugify)
    panel["mandi_id"] = "maharashtra__" + panel["mandi"]
    panel["source_name"] = "ceda_agmarknet"
    panel["unit"] = "INR/quintal"
    panel["source_rows"] = panel["source_rows"].fillna(0).astype(int)

    panel = add_short_gap_imputations(panel, max_gap_days)

    panel = panel.rename(
        columns={
            "min_price": "min_price_inr_qtl",
            "max_price": "max_price_inr_qtl",
            "modal_price": "modal_price_inr_qtl",
        }
    )

    output_columns = [
        "date",
        "state",
        "district",
        "district_id",
        "mandi",
        "mandi_id",
        "market_id",
        "market_name",
        "crop",
        "crop_id",
        "min_price_inr_qtl",
        "max_price_inr_qtl",
        "modal_price_inr_qtl",
        "is_observed",
        "is_imputed",
        "imputation_method",
        "quality_flag",
        "source_rows",
        "source_name",
        "unit",
    ]
    panel = panel[output_columns]

    summary = {
        "raw_selected_rows": len(raw),
        "invalid_rows_dropped": invalid_rows,
        "duplicate_market_date_rows": duplicate_count,
        "panel_rows": len(panel),
        "observed_rows": int(panel["is_observed"].sum()),
        "imputed_rows": int(panel["is_imputed"].sum()),
        "missing_long_gap_rows": int((panel["quality_flag"] == "missing_long_gap").sum()),
        "market_count": int(panel["market_id"].nunique()),
        "date_min": str(panel["date"].min()),
        "date_max": str(panel["date"].max()),
    }
    return panel, summary


def write_report(panel: pd.DataFrame, summary: dict, report_path: Path) -> None:
    by_market = (
        panel.groupby(["market_id", "market_name", "district"], dropna=False)
        .agg(
            panel_days=("date", "size"),
            observed_days=("is_observed", "sum"),
            imputed_days=("is_imputed", "sum"),
            missing_long_gap_days=(
                "quality_flag",
                lambda values: (values == "missing_long_gap").sum(),
            ),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .reset_index()
    )
    by_market["observed_pct"] = (
        by_market["observed_days"] / by_market["panel_days"] * 100
    ).round(2)
    by_market = by_market.sort_values(["observed_days", "observed_pct"], ascending=False)

    lines = [
        "# Clean Onion/Maharashtra Panel",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in summary.items())
    lines.extend(
        [
            "",
            "## Market Coverage",
            "",
            dataframe_to_markdown(by_market),
            "",
            "## Cleaning Rules",
            "",
            "- Dropped rows with non-positive modal price or invalid min/modal/max order.",
            "- Aggregated duplicate market-date rows using min(min), max(max), median(modal).",
            "- Built a daily panel for the selected MVP mandis.",
            "- Forward-filled only internal gaps of 3 days or less.",
            "- Kept longer missing gaps as `missing_long_gap` rows.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    raw = pd.read_csv(args.raw_input)
    mandis = pd.read_csv(args.mandis)
    panel, summary = build_panel(raw, mandis, args.max_impute_gap_days)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output_path, index=False)

    report_path = Path(args.report)
    write_report(panel, summary, report_path)

    print(f"Wrote clean panel: {output_path}")
    print(f"Wrote report: {report_path}")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
