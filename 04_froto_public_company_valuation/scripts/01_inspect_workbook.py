"""
Inspect the local FROTO valuation workbook.

Usage:
    python scripts/01_inspect_workbook.py --workbook "/path/to/FROTO_DCF_Trading_Comps_Model_v1_9.xlsx"

Output:
    outputs/tables/workbook_sheet_inventory.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", required=True, help="Local FROTO valuation workbook path")
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
            df = pd.read_excel(workbook, sheet_name=sheet, header=None, nrows=20)
            non_empty = df.dropna(how="all").shape[0]
            rows.append(
                {
                    "sheet": sheet,
                    "n_preview_rows": len(df),
                    "n_preview_columns": len(df.columns),
                    "non_empty_preview_rows": non_empty,
                    "read_status": "ok",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "sheet": sheet,
                    "n_preview_rows": "",
                    "n_preview_columns": "",
                    "non_empty_preview_rows": "",
                    "read_status": f"failed: {str(exc)[:200]}",
                }
            )

    inventory = pd.DataFrame(rows)
    out = tables_dir / "workbook_sheet_inventory.csv"
    inventory.to_csv(out, index=False)

    print(f"Workbook inventory written to: {out}")
    print(inventory.to_string(index=False))


if __name__ == "__main__":
    main()
