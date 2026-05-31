"""
Raw source audit for the Turkey Treasury / ALM & Liquidity Risk Dashboard.

This script inspects the local raw-data directory and creates a compact inventory
of available source files. Raw data files are not stored in the GitHub repository.

Usage:
    python scripts/01_inspect_raw_sources.py --raw-dir "/path/to/local/data_raw"

Outputs:
    outputs/tables/raw_source_inventory.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx", ".pdf"}


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def preview_tabular_file(path: Path) -> dict:
    """Return basic preview metadata for CSV/XLS/XLSX files."""
    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            for encoding in ["utf-8", "utf-8-sig", "latin1"]:
                try:
                    df = pd.read_csv(path, nrows=5, encoding=encoding)
                    return {
                        "read_status": "ok",
                        "sheet_or_encoding": encoding,
                        "n_preview_columns": len(df.columns),
                        "preview_columns": " | ".join(map(str, df.columns[:12])),
                    }
                except Exception:
                    continue
            return {
                "read_status": "failed",
                "sheet_or_encoding": "",
                "n_preview_columns": "",
                "preview_columns": "CSV read failed with tested encodings",
            }

        if suffix in {".xls", ".xlsx"}:
            xl = pd.ExcelFile(path)
            sheet_names = xl.sheet_names
            first_sheet = sheet_names[0] if sheet_names else ""
            if first_sheet:
                df = pd.read_excel(path, sheet_name=first_sheet, nrows=5)
                return {
                    "read_status": "ok",
                    "sheet_or_encoding": first_sheet,
                    "n_preview_columns": len(df.columns),
                    "preview_columns": " | ".join(map(str, df.columns[:12])),
                }
            return {
                "read_status": "ok_no_sheets",
                "sheet_or_encoding": "",
                "n_preview_columns": 0,
                "preview_columns": "",
            }

        if suffix == ".pdf":
            return {
                "read_status": "pdf_not_parsed",
                "sheet_or_encoding": "",
                "n_preview_columns": "",
                "preview_columns": "PDF source; not parsed in audit script",
            }

    except Exception as exc:
        return {
            "read_status": "failed",
            "sheet_or_encoding": "",
            "n_preview_columns": "",
            "preview_columns": str(exc)[:250],
        }

    return {
        "read_status": "unsupported",
        "sheet_or_encoding": "",
        "n_preview_columns": "",
        "preview_columns": "",
    }


def build_inventory(raw_dir: Path) -> pd.DataFrame:
    rows = []

    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".DS_Store":
            continue

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        preview = preview_tabular_file(path)

        rows.append(
            {
                "relative_path": str(path.relative_to(raw_dir)),
                "file_name": path.name,
                "extension": suffix,
                "size_mb": round(file_size_mb(path), 3),
                **preview,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, help="Local raw-data directory path")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).expanduser().resolve()
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    project_dir = Path(__file__).resolve().parents[1]
    output_dir = project_dir / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory(raw_dir)
    output_path = output_dir / "raw_source_inventory.csv"
    inventory.to_csv(output_path, index=False)

    print(f"Raw source inventory written to: {output_path}")
    print(f"Files inspected: {len(inventory)}")
    if len(inventory) > 0:
        print(inventory[["relative_path", "extension", "size_mb", "read_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
