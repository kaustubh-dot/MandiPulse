from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
DEFAULT_SCHEMA_DIR = PROJECT_ROOT / "schemas" / "web_export" / "v2"

ARTIFACT_SCHEMAS: dict[str, str] = {
    "backtest.json": "backtest.schema.json",
    "forecasts.json": "forecasts.schema.json",
    "honest_results.json": "honest_results.schema.json",
    "mandis.json": "mandis.schema.json",
    "manifest.json": "manifest.schema.json",
    "meta.json": "meta.schema.json",
    "price_history.json": "price_history.schema.json",
    "recommendations.json": "recommendations.schema.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_non_standard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def load_strict_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=_reject_non_standard_constant,
    )


def _non_finite_paths(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return [] if math.isfinite(value) else [path]
    if isinstance(value, list):
        failures: list[str] = []
        for index, item in enumerate(value):
            failures.extend(_non_finite_paths(item, f"{path}[{index}]"))
        return failures
    if isinstance(value, dict):
        failures = []
        for key, item in value.items():
            failures.extend(_non_finite_paths(item, f"{path}.{key}"))
        return failures
    return []


def _validate_manifest_integrity(manifest: dict[str, Any], data_dir: Path, root: Path) -> None:
    entries = manifest["artifacts"]
    expected_payloads = set(ARTIFACT_SCHEMAS) - {"manifest.json"}
    recorded_payloads = {Path(entry["path"]).name for entry in entries}
    if recorded_payloads != expected_payloads:
        raise ValueError(
            "manifest artifact inventory mismatch: "
            f"expected {sorted(expected_payloads)}, got {sorted(recorded_payloads)}"
        )

    for entry in entries:
        artifact_path = data_dir / Path(entry["path"]).name
        actual_hash = sha256_file(artifact_path)
        if entry["sha256"] != actual_hash:
            raise ValueError(f"manifest hash mismatch for {artifact_path.name}")
        if entry["bytes"] != artifact_path.stat().st_size:
            raise ValueError(f"manifest byte-size mismatch for {artifact_path.name}")

    for entry in manifest["inputs"]:
        input_path = root / entry["path"]
        if not input_path.is_file():
            raise ValueError(f"manifest input missing: {entry['path']}")
        if entry["sha256"] != sha256_file(input_path):
            raise ValueError(f"manifest input hash mismatch: {entry['path']}")
        if entry["bytes"] != input_path.stat().st_size:
            raise ValueError(f"manifest input byte-size mismatch: {entry['path']}")

    generator = manifest["code"]
    generator_path = root / generator["generator_path"]
    if generator["generator_sha256"] != sha256_file(generator_path):
        raise ValueError("manifest generator hash does not match scripts/build_web_export.py")

    configuration = manifest["configuration"]
    config_path = root / configuration["path"]
    if configuration["sha256"] != sha256_file(config_path):
        raise ValueError("manifest recommendation configuration hash mismatch")


def validate_exports(
    data_dir: Path = DEFAULT_DATA_DIR,
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
    root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    actual = {path.name for path in data_dir.glob("*.json")}
    expected = set(ARTIFACT_SCHEMAS)
    if actual != expected:
        raise ValueError(
            f"export inventory mismatch: expected {sorted(expected)}, got {sorted(actual)}"
        )

    results: list[dict[str, Any]] = []
    parsed: dict[str, Any] = {}
    for artifact_name, schema_name in ARTIFACT_SCHEMAS.items():
        artifact_path = data_dir / artifact_name
        schema_path = schema_dir / schema_name
        instance = load_strict_json(artifact_path)
        schema = load_strict_json(schema_path)
        Draft202012Validator.check_schema(schema)
        # JSON Schema format keywords are annotations unless a checker is
        # supplied explicitly.  The exports promise ISO dates/timestamps, so
        # enforce those formats rather than accepting malformed strings.
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
        failures = _non_finite_paths(instance)
        if failures:
            raise ValueError(
                f"{artifact_name} contains non-finite numeric values at {failures[:5]}"
            )
        parsed[artifact_name] = instance
        results.append(
            {
                "artifact": artifact_name,
                "strict_json": "PASS",
                "schema": "PASS",
                "finite_numbers": "PASS",
            }
        )

    _validate_manifest_integrity(parsed["manifest.json"], data_dir, root)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strictly parse, schema-validate, and verify the MandiPulse web export bundle."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = validate_exports(args.data_dir, args.schema_dir)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    for result in results:
        print(f"PASS {result['artifact']}: strict JSON, schema-valid, finite numeric values")
    print(f"PASS: {len(results)}/{len(ARTIFACT_SCHEMAS)} exported JSON files validated")
    print("PASS: manifest artifact/input/code/config hashes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
