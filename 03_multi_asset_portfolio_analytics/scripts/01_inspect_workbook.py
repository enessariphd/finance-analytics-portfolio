"""
Inspect the local Türkiye multi-asset analysis workbook.

Usage:
    python scripts/01_inspect_workbook.py --workbook "/path/to/turkiye_multi_asset_analysis_risk_return_fixed.xlsx"

Output:
    outputs/tables/workbook_sheet_inventory.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", required=True, help="Local multi-asset workbook path")
    args = parser.parse_args()

    workbook = Path(args.workbook).expanduser().resolve()
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    xl = pd.ExcelFile(workbook)
    rows = []

    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(workbook, sheet_name=sheet, nrows=5)
            rows.append(
                {
                    "sheet": sheet,
                    "n_preview_rows": len(df),
                    "n_preview_columns": len(df.columns),
                    "preview_columns": " | ".join(map(str, df.columns[:12])),
                    "read_status": "ok",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "sheet": sheet,
                    "n_preview_rows": "",
                    "n_preview_columns": "",
                    "preview_columns": str(exc)[:250],
                    "read_status": "failed",
                }
            )

    inventory = pd.DataFrame(rows)
    out = tables_dir / "workbook_sheet_inventory.csv"
    inventory.to_csv(out, index=False)

    print(f"Workbook inventory written to: {out}")
    print(inventory.to_string(index=False))


if __name__ == "__main__":
    main()
