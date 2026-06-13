from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*_: Any, **__: Any) -> bool:
        return False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mandipulse.config import load_yaml_config, resolve_project_path  # noqa: E402
from mandipulse.data.ceda_client import CedaAgmarknetClient, CedaApiError  # noqa: E402


def payload_records(payload: dict[str, Any], keys: list[str] | None = None) -> list[dict[str, Any]]:
    keys = keys or []
    for key in [*keys, "data"]:
        records = payload.get(key)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]

    output = payload.get("output")
    if isinstance(output, dict):
        for key in [*keys, "data"]:
            records = output.get(key)
            if isinstance(records, list):
                return [record for record in records if isinstance(record, dict)]

    return []


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_chunks(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def batched(values: list[int], batch_size: int) -> list[list[int]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def maharashtra_district_rows(
    geographies_payload: dict[str, Any],
    state_id: int,
) -> list[dict[str, Any]]:
    rows = payload_records(geographies_payload, ["geographies"])
    return [row for row in rows if row.get("census_state_id") == state_id]


def append_price_rows(
    writer: csv.DictWriter[str],
    rows: list[dict[str, Any]],
    district_lookup: dict[int, str],
    market_lookup: dict[int, str],
) -> int:
    written = 0
    for row in rows:
        district_id = row.get("census_district_id")
        market_id = row.get("market_id")
        if not isinstance(district_id, int) or not isinstance(market_id, int):
            continue

        writer.writerow(
            {
                "date": row.get("date"),
                "commodity_id": row.get("commodity_id"),
                "commodity_name": "Onion",
                "state_id": row.get("census_state_id"),
                "state_name": "Maharashtra",
                "district_id": district_id,
                "district_name": district_lookup.get(district_id, ""),
                "market_id": market_id,
                "market_name": market_lookup.get(market_id, ""),
                "min_price": row.get("min_price"),
                "max_price": row.get("max_price"),
                "modal_price": row.get("modal_price"),
            }
        )
        written += 1
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch raw CEDA AGMARKNET data for the narrowed Onion/Maharashtra MVP."
    )
    parser.add_argument("--config", default="configs/data.yaml")
    parser.add_argument("--from-date", default=None, help="Start date, YYYY-MM-DD.")
    parser.add_argument("--to-date", default=None, help="End date, YYYY-MM-DD.")
    parser.add_argument("--chunk-days", type=int, default=366)
    parser.add_argument("--market-batch-size", type=int, default=25)
    parser.add_argument("--max-districts", type=int, default=None)
    parser.add_argument("--request-sleep-seconds", type=float, default=2.0)
    parser.add_argument("--api-max-retries", type=int, default=6)
    parser.add_argument("--api-retry-backoff-seconds", type=float, default=10.0)
    parser.add_argument(
        "--district-level",
        action="store_true",
        help="Fetch each district separately. Default is faster state-level market batches.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refetch even when raw response JSON exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")

    config = load_yaml_config(args.config)
    source = config["data_source"]
    scope = config["mvp_scope"]
    raw_dir = resolve_project_path(config["paths"]["narrowed_mvp_raw_dir"])
    metadata_dir = raw_dir / "metadata"
    response_dir = raw_dir / "responses"
    flat_csv_path = raw_dir / "onion_maharashtra_prices_raw.csv"

    commodity_id = int(scope["commodity_id"])
    state_id = int(scope["state_id"])
    from_date = parse_iso_date(args.from_date or scope["start_date"])
    to_date = parse_iso_date(args.to_date or scope["end_date"])

    client = CedaAgmarknetClient(
        base_url=source["api_base"],
        max_retries=args.api_max_retries,
        retry_backoff_seconds=args.api_retry_backoff_seconds,
    )

    geographies_path = metadata_dir / "geographies.json"
    if geographies_path.exists() and not args.force:
        geographies_payload = load_json(geographies_path)
    else:
        try:
            geographies_payload = client.geographies()
        except CedaApiError as exc:
            print(f"Failed to fetch CEDA geographies: {exc}", file=sys.stderr)
            return 1
        save_json(geographies_path, geographies_payload)
    district_rows = maharashtra_district_rows(geographies_payload, state_id)
    if args.max_districts is not None:
        district_rows = district_rows[: args.max_districts]

    district_lookup = {
        int(row["census_district_id"]): str(row.get("census_district_name", ""))
        for row in district_rows
        if isinstance(row.get("census_district_id"), int)
    }

    print(f"Districts selected: {len(district_rows)}", flush=True)
    if args.dry_run:
        for row in district_rows:
            print(f"{row.get('census_district_id')}: {row.get('census_district_name')}", flush=True)
        return 0

    all_market_rows: list[dict[str, Any]] = []
    for row in district_rows:
        district_id = row.get("census_district_id")
        if not isinstance(district_id, int):
            continue
        try:
            markets_path = metadata_dir / f"markets_district_{district_id}.json"
            used_market_cache = markets_path.exists() and not args.force
            if used_market_cache:
                markets_payload = load_json(markets_path)
            else:
                markets_payload = client.markets(
                    commodity_id=commodity_id,
                    state_id=state_id,
                    district_id=district_id,
                    indicator="price",
                )
                save_json(markets_path, markets_payload)
        except CedaApiError as exc:
            print(f"Market lookup failed for district {district_id}: {exc}", file=sys.stderr)
            continue

        all_market_rows.extend(payload_records(markets_payload))
        if not used_market_cache:
            time.sleep(args.request_sleep_seconds)

    market_lookup = {
        int(row["market_id"]): str(row.get("market_name", ""))
        for row in all_market_rows
        if isinstance(row.get("market_id"), int)
    }
    save_json(metadata_dir / "markets_all.json", {"data": all_market_rows})
    print(f"Markets selected: {len(market_lookup)}", flush=True)

    flat_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "commodity_id",
        "commodity_name",
        "state_id",
        "state_name",
        "district_id",
        "district_name",
        "market_id",
        "market_name",
        "min_price",
        "max_price",
        "modal_price",
    ]

    total_rows = 0
    with flat_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        if not args.district_level:
            all_market_ids = sorted(market_lookup)
            for market_ids in batched(all_market_ids, args.market_batch_size):
                for start, end in date_chunks(from_date, to_date, args.chunk_days):
                    response_path = (
                        response_dir
                        / "state_level"
                        / f"{start.isoformat()}_{end.isoformat()}_markets_{market_ids[0]}.json"
                    )
                    used_cache = response_path.exists() and not args.force
                    if used_cache:
                        prices_payload = load_json(response_path)
                    else:
                        try:
                            prices_payload = client.prices(
                                commodity_id=commodity_id,
                                state_id=state_id,
                                market_ids=market_ids,
                                from_date=start.isoformat(),
                                to_date=end.isoformat(),
                            )
                        except CedaApiError as exc:
                            print(
                                "Price fetch failed for "
                                f"state={state_id}, {start}..{end}: {exc}",
                                file=sys.stderr,
                                flush=True,
                            )
                            continue
                        save_json(response_path, prices_payload)

                    total_rows += append_price_rows(
                        writer,
                        payload_records(prices_payload),
                        district_lookup,
                        market_lookup,
                    )
                    print(
                        f"Fetched state={state_id} markets={len(market_ids)} "
                        f"{start}..{end}; total_rows={total_rows}"
                        f"{' (cached)' if used_cache else ''}",
                        flush=True,
                    )
                    if not used_cache:
                        time.sleep(args.request_sleep_seconds)

        for row in district_rows if args.district_level else []:
            district_id = row.get("census_district_id")
            if not isinstance(district_id, int):
                continue

            district_market_ids = [
                int(market["market_id"])
                for market in all_market_rows
                if market.get("census_district_id") == district_id
                and isinstance(market.get("market_id"), int)
            ]
            if not district_market_ids:
                continue

            for market_ids in batched(district_market_ids, args.market_batch_size):
                for start, end in date_chunks(from_date, to_date, args.chunk_days):
                    response_path = (
                        response_dir
                        / f"district_{district_id}"
                        / f"{start.isoformat()}_{end.isoformat()}_markets_{market_ids[0]}.json"
                    )
                    used_cache = response_path.exists() and not args.force
                    if used_cache:
                        prices_payload = load_json(response_path)
                    else:
                        try:
                            prices_payload = client.prices(
                                commodity_id=commodity_id,
                                state_id=state_id,
                                district_ids=[district_id],
                                market_ids=market_ids,
                                from_date=start.isoformat(),
                                to_date=end.isoformat(),
                            )
                        except CedaApiError as exc:
                            print(
                                "Price fetch failed for "
                                f"district={district_id}, {start}..{end}: {exc}",
                                file=sys.stderr,
                                flush=True,
                            )
                            continue
                        save_json(response_path, prices_payload)

                    total_rows += append_price_rows(
                        writer,
                        payload_records(prices_payload),
                        district_lookup,
                        market_lookup,
                    )
                    print(
                        f"Fetched district={district_id} markets={len(market_ids)} "
                        f"{start}..{end}; total_rows={total_rows}"
                        f"{' (cached)' if used_cache else ''}",
                        flush=True,
                    )
                    if not used_cache:
                        time.sleep(args.request_sleep_seconds)

    summary = {
        "commodity_id": commodity_id,
        "commodity_name": scope["commodity_name"],
        "state_id": state_id,
        "state_name": scope["state_name"],
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "district_count": len(district_rows),
        "market_count": len(market_lookup),
        "row_count": total_rows,
        "flat_csv_path": str(flat_csv_path),
    }
    save_json(raw_dir / "fetch_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
