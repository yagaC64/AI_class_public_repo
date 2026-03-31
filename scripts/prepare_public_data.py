#!/usr/bin/env python3
"""Generate a publish-safe CSV and manifest for the public ontology app."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "config" / "public-data-pipeline.json"


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def resolve_repo_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    required_keys = {
        "pipeline_name",
        "input",
        "output",
        "manifest",
        "source_to_public_field_map",
        "required_source_fields",
        "required_public_fields",
        "default_public_values",
        "unique_public_fields",
        "sort_by_public_fields",
    }
    missing = sorted(required_keys.difference(config))
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

    config["config_path"] = config_path
    config["input"] = resolve_repo_path(config["input"])
    config["output"] = resolve_repo_path(config["output"])
    config["manifest"] = resolve_repo_path(config["manifest"])
    return config


def build_public_rows(config: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    input_path: Path = config["input"]
    field_map: dict[str, str] = config["source_to_public_field_map"]
    required_source_fields = set(config["required_source_fields"])
    required_public_fields = config["required_public_fields"]
    default_public_values = config["default_public_values"]
    unique_public_fields = config["unique_public_fields"]
    sort_by_public_fields = config["sort_by_public_fields"]
    output_fields = list(field_map.values())

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        source_fields = reader.fieldnames or []
        missing = sorted(required_source_fields.difference(source_fields))
        if missing:
            raise ValueError(f"Missing required source columns: {', '.join(missing)}")

        source_row_count = 0
        skipped_missing_required_rows = 0
        duplicate_rows_removed = 0
        public_rows: list[dict[str, str]] = []
        seen: set[tuple[str, ...]] = set()

        for raw_row in reader:
            source_row_count += 1
            public_row = {
                public_field: normalize_text(raw_row.get(source_field, ""))
                for source_field, public_field in field_map.items()
            }

            for public_field, default_value in default_public_values.items():
                if not public_row.get(public_field):
                    public_row[public_field] = normalize_text(default_value)

            if any(not public_row.get(field) for field in required_public_fields):
                skipped_missing_required_rows += 1
                continue

            unique_key = tuple(public_row[field].casefold() for field in unique_public_fields)
            if unique_key in seen:
                duplicate_rows_removed += 1
                continue

            seen.add(unique_key)
            public_rows.append({field: public_row[field] for field in output_fields})

    public_rows.sort(
        key=lambda row: tuple(row[field].casefold() for field in sort_by_public_fields)
    )

    metadata = {
        "source_fields": source_fields,
        "dropped_source_fields": [
            field for field in source_fields if field not in field_map
        ],
        "public_fields": output_fields,
        "source_row_count": source_row_count,
        "public_row_count": len(public_rows),
        "skipped_missing_required_rows": skipped_missing_required_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "required_source_fields": sorted(required_source_fields),
        "required_public_fields": required_public_fields,
        "unique_public_fields": unique_public_fields,
    }
    return public_rows, metadata


def write_rows(output_path: Path, rows: list[dict[str, str]], output_fields: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate the pipeline inputs and print a summary without rewriting public artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(resolve_repo_path(args.config))

    if args.input:
        config["input"] = resolve_repo_path(args.input)
    if args.output:
        config["output"] = resolve_repo_path(args.output)
    if args.manifest:
        config["manifest"] = resolve_repo_path(args.manifest)

    public_rows, metadata = build_public_rows(config)
    output_fields = metadata["public_fields"]
    input_path: Path = config["input"]
    output_path: Path = config["output"]
    manifest_path: Path = config["manifest"]

    if not args.check_only:
        write_rows(output_path, public_rows, output_fields)

    manifest = {
        "pipeline_name": config["pipeline_name"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config["config_path"].relative_to(REPO_ROOT)),
        "input_path": str(input_path.relative_to(REPO_ROOT)),
        "output_path": str(output_path.relative_to(REPO_ROOT)),
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
        "input_filename": input_path.name,
        "source_sha256": sha256_for_file(input_path),
        **metadata,
    }

    if not args.check_only:
        manifest["output_sha256"] = sha256_for_file(output_path)
        write_manifest(manifest_path, manifest)

    print(f"pipeline={manifest['pipeline_name']}")
    print(f"input={input_path}")
    print(f"output={output_path}")
    print(f"manifest={manifest_path}")
    print(f"source_rows={manifest['source_row_count']}")
    print(f"public_rows={manifest['public_row_count']}")
    print(f"dropped_fields={','.join(manifest['dropped_source_fields'])}")
    print(f"public_fields={','.join(output_fields)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
