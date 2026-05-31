"""
Extract memo-ready valuation outputs from the local FROTO valuation workbook.

Usage:
    python scripts/02_extract_valuation_outputs.py --workbook "/path/to/FROTO_DCF_Trading_Comps_Model_v1_9.xlsx"

Outputs:
    outputs/tables/valuation_methods_summary.csv
    outputs/tables/real_dcf_case_calculation.csv
    outputs/tables/wacc_terminal_growth_sensitivity.csv
    outputs/tables/peer_multiple_summary.csv
    outputs/tables/beta_sensitivity.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def read_sheet(workbook: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(workbook, sheet_name=sheet_name, header=None)


def clean_extracted_table(table: pd.DataFrame) -> pd.DataFrame:
    """Remove empty rows/columns and unnamed/blank columns from extracted Excel regions."""
    table = table.dropna(axis=1, how="all").dropna(how="all")
    table = table.loc[:, [not pd.isna(c) for c in table.columns]]
    table = table.loc[:, [str(c).strip() not in {"", "nan", "None"} for c in table.columns]]
    return clean_extracted_table(table)


def extract_valuation_methods_summary(workbook: Path) -> pd.DataFrame:
    df = read_sheet(workbook, "21_Final_Valuation_Summary")

    # Table starts at row where first column is "Method".
    start_idx = df.index[df.iloc[:, 0].astype(str).str.strip().eq("Method")][0]
    header = df.iloc[start_idx].tolist()
    table = df.iloc[start_idx + 1 : start_idx + 9].copy()
    table.columns = header
    table = table.dropna(how="all")

    return clean_extracted_table(table)


def extract_real_dcf_case_calculation(workbook: Path) -> pd.DataFrame:
    df = read_sheet(workbook, "21_Final_Valuation_Summary")

    start_idx = df.index[df.iloc[:, 0].astype(str).str.strip().eq("Case")][0]
    header = df.iloc[start_idx].tolist()
    table = df.iloc[start_idx + 1 : start_idx + 4].copy()
    table.columns = header
    table = table.dropna(how="all")

    return clean_extracted_table(table)


def extract_wacc_terminal_growth_sensitivity(workbook: Path) -> pd.DataFrame:
    df = read_sheet(workbook, "08_Sensitivity")

    start_idx = df.index[df.iloc[:, 0].astype(str).str.strip().eq("WACC \\ g")][0]
    header = df.iloc[start_idx].tolist()
    table = df.iloc[start_idx + 1 : start_idx + 6].copy()
    table.columns = header
    table = table.dropna(how="all")

    # Rename first column for CSV clarity.
    first_col = table.columns[0]
    table = table.rename(columns={first_col: "WACC"})
    return clean_extracted_table(table)


def extract_peer_multiple_summary(workbook: Path) -> pd.DataFrame:
    df = read_sheet(workbook, "16_Peer_Audit")

    start_idx = df.index[df.iloc[:, 0].astype(str).str.strip().eq("Peer set")][0]
    header = df.iloc[start_idx].tolist()
    table = df.iloc[start_idx + 1 : start_idx + 4].copy()
    table.columns = header
    table = table.dropna(how="all")

    return clean_extracted_table(table)


def extract_beta_sensitivity(workbook: Path) -> pd.DataFrame:
    df = read_sheet(workbook, "23_Beta_Sensitivity_Check")

    start_idx = df.index[df.iloc[:, 0].astype(str).str.strip().eq("Beta case")][0]
    header = df.iloc[start_idx].tolist()
    table = df.iloc[start_idx + 1 : start_idx + 4].copy()
    table.columns = header
    table = table.dropna(how="all")

    return table


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

    valuation_methods = extract_valuation_methods_summary(workbook)
    real_dcf_cases = extract_real_dcf_case_calculation(workbook)
    sensitivity = extract_wacc_terminal_growth_sensitivity(workbook)
    peer_summary = extract_peer_multiple_summary(workbook)
    beta_sensitivity = extract_beta_sensitivity(workbook)

    valuation_methods.to_csv(tables_dir / "valuation_methods_summary.csv", index=False)
    real_dcf_cases.to_csv(tables_dir / "real_dcf_case_calculation.csv", index=False)
    sensitivity.to_csv(tables_dir / "wacc_terminal_growth_sensitivity.csv", index=False)
    peer_summary.to_csv(tables_dir / "peer_multiple_summary.csv", index=False)
    beta_sensitivity.to_csv(tables_dir / "beta_sensitivity.csv", index=False)

    print("Extracted valuation output tables.")
    print("\nValuation methods summary:")
    print(valuation_methods.to_string(index=False))

    print("\nReal DCF case calculation:")
    print(real_dcf_cases.to_string(index=False))

    print("\nWACC x terminal growth sensitivity:")
    print(sensitivity.to_string(index=False))

    print("\nPeer multiple summary:")
    print(peer_summary.to_string(index=False))

    print("\nBeta sensitivity:")
    print(beta_sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
