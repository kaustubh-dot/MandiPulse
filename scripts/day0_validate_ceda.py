from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mandipulse.config import load_yaml_config, resolve_project_path  # noqa: E402
from mandipulse.data.ceda_client import CedaAgmarknetClient, CedaApiError  # noqa: E402


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip().casefold()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def find_by_normalized_name(
    rows: list[dict[str, Any]],
    name_keys: list[str],
    target: str,
) -> dict[str, Any] | None:
    wanted = normalize_name(target)
    for row in rows:
        for key in name_keys:
            value = row.get(key)
            if isinstance(value, str) and normalize_name(value) == wanted:
                return row
    return None


def first_int(row: dict[str, Any], keys: list[str]) -> int | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def validate_price_samples(
    client: CedaAgmarknetClient,
    output_dir: Path,
    commodities: list[dict[str, Any]],
    geographies: list[dict[str, Any]],
    mvp_crops: list[str],
    mvp_states: list[str],
    from_date: str,
    to_date: str,
    max_districts_per_state: int,
    max_markets_per_sample: int,
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for crop_name in mvp_crops:
        crop_result: dict[str, Any] = {"status": "not_found"}
        commodity = find_by_normalized_name(commodities, ["name", "commodity_name"], crop_name)
        commodity_id = first_int(commodity or {}, ["id", "commodity_id"])
        if commodity is None or commodity_id is None:
            results[crop_name] = crop_result
            continue

        crop_result = {
            "status": "commodity_found",
            "commodity_id": commodity_id,
            "samples": [],
        }

        for state_name in mvp_states:
            state = find_by_normalized_name(geographies, ["state_name", "name"], state_name)
            state_id = first_int(state or {}, ["state_id", "census_state_id", "id"])
            districts = (state or {}).get("districts") or []
            if state is None or state_id is None or not isinstance(districts, list):
                crop_result["samples"].append(
                    {"state": state_name, "status": "state_or_district_not_found"}
                )
                continue

            for district in districts[:max_districts_per_state]:
                district_id = first_int(district, ["district_id", "census_district_id", "id"])
                district_name = district.get("district_name") or district.get("name")
                if district_id is None:
                    continue

                try:
                    markets_payload = client.markets(
                        commodity_id=commodity_id,
                        state_id=state_id,
                        district_id=district_id,
                        indicator="price",
                    )
                except CedaApiError as exc:
                    crop_result["samples"].append(
                        {
                            "state": state_name,
                            "district": district_name,
                            "status": "markets_failed",
                            "error": str(exc),
                        }
                    )
                    continue

                markets = markets_payload.get("data") or []
                if not markets:
                    continue

                market_ids = [
                    market_id
                    for market in markets[:max_markets_per_sample]
                    if (market_id := first_int(market, ["market_id", "id"])) is not None
                ]
                markets_file = output_dir / f"day0_ceda_{crop_name}_{state_name}_markets.json"
                save_json(markets_file, markets_payload)

                price_result: dict[str, Any] = {
                    "state": state_name,
                    "state_id": state_id,
                    "district": district_name,
                    "district_id": district_id,
                    "market_ids": market_ids,
                    "markets_sample_path": str(markets_file),
                    "status": "markets_found",
                }

                if market_ids:
                    try:
                        prices_payload = client.prices(
                            commodity_id=commodity_id,
                            state_id=state_id,
                            district_ids=[district_id],
                            market_ids=market_ids,
                            from_date=from_date,
                            to_date=to_date,
                        )
                        prices_file = output_dir / f"day0_ceda_{crop_name}_{state_name}_prices.json"
                        save_json(prices_file, prices_payload)
                        price_result.update(
                            {
                                "status": "prices_fetched",
                                "prices_sample_path": str(prices_file),
                                "record_count": len(prices_payload.get("data") or []),
                            }
                        )
                    except CedaApiError as exc:
                        price_result.update({"status": "prices_failed", "error": str(exc)})

                crop_result["samples"].append(price_result)
                break

            if any(sample.get("status") == "prices_fetched" for sample in crop_result["samples"]):
                break

        results[crop_name] = crop_result

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CEDA AGMARKNET access for Day 0.")
    parser.add_argument("--config", default="configs/data.yaml", help="Path to data config.")
    parser.add_argument("--from-date", default="2025-03-01", help="Sample start date, YYYY-MM-DD.")
    parser.add_argument("--to-date", default="2025-03-31", help="Sample end date, YYYY-MM-DD.")
    parser.add_argument("--max-districts-per-state", type=int, default=8)
    parser.add_argument("--max-markets-per-sample", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    output_dir = resolve_project_path(config["paths"]["raw_data"]) / "samples"
    source = config["data_source"]
    client = CedaAgmarknetClient(base_url=source["api_base"])

    try:
        commodities_payload = client.commodities()
        geographies_payload = client.geographies()
    except CedaApiError as exc:
        print(f"CEDA validation failed before samples could be saved: {exc}", file=sys.stderr)
        return 1

    commodities_file = output_dir / "day0_ceda_commodities.json"
    geographies_file = output_dir / "day0_ceda_geographies.json"
    save_json(commodities_file, commodities_payload)
    save_json(geographies_file, geographies_payload)

    sample_results = validate_price_samples(
        client=client,
        output_dir=output_dir,
        commodities=commodities_payload.get("commodities") or [],
        geographies=geographies_payload.get("geographies") or [],
        mvp_crops=config["mvp_crops"],
        mvp_states=config["mvp_states"],
        from_date=args.from_date,
        to_date=args.to_date,
        max_districts_per_state=args.max_districts_per_state,
        max_markets_per_sample=args.max_markets_per_sample,
    )

    summary = {
        "api_base": source["api_base"],
        "from_date": args.from_date,
        "to_date": args.to_date,
        "commodities_sample_path": str(commodities_file),
        "geographies_sample_path": str(geographies_file),
        "crop_results": sample_results,
    }
    summary_file = output_dir / "day0_ceda_summary.json"
    save_json(summary_file, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
