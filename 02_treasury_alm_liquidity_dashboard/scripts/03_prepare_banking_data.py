"""
Prepare BDDK / BRSA banking-sector liquidity data for the
Turkey Treasury / ALM & Liquidity Risk Dashboard.

The BDDK source files used here have .xls extensions but are HTML tables exported
in an Excel-compatible format. Therefore, this script reads them with pandas.read_html.

Usage:
    python scripts/03_prepare_banking_data.py --raw-dir "/path/to/local/data_raw"

Outputs:
    outputs/tables/banking_weekly_core.csv
    outputs/tables/latest_banking_dashboard_snapshot.csv
    outputs/charts/banking_liquidity_conditions.png
    outputs/charts/deposit_structure.png
    outputs/charts/securities_liquidity_proxy.png
    outputs/charts/fx_position_capital_proxy.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def clean_numeric(series: pd.Series) -> pd.Series:
    """
    Convert BDDK Turkish-formatted numeric strings into floats.

    Examples:
    - 383.721,47 -> 383721.47
    - 22106 -> 22106
    - 000 -> 0
    """
    s = (
        series.astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("−", "-", regex=False)
        .str.strip()
        .replace({"nan": np.nan, "": np.nan, "-": np.nan})
    )

    def convert_one(x):
        if pd.isna(x):
            return np.nan

        x = str(x).strip()

        if x in {"000", "0.00", "0,00"}:
            return 0.0

        # Turkish format: 383.721,47
        if "." in x and "," in x:
            return float(x.replace(".", "").replace(",", "."))

        # Decimal comma: 49,27
        if "," in x and "." not in x:
            return float(x.replace(",", "."))

        return float(x)

    return s.apply(convert_one)


def parse_bddk_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def read_bddk_html_xls(path: Path, value_columns: list[str]) -> pd.DataFrame:
    """
    Read a BDDK HTML-exported .xls file.

    The first three rows contain metadata, header group labels and sector label.
    Data starts from row index 3. Column 0 is the date column.
    """
    tables = pd.read_html(path)
    if not tables:
        raise ValueError(f"No HTML table found in {path}")

    raw = tables[0].copy()

    data = raw.iloc[3:].copy()
    expected_cols = ["date"] + value_columns

    if data.shape[1] != len(expected_cols):
        raise ValueError(
            f"Unexpected number of columns in {path.name}: "
            f"found {data.shape[1]}, expected {len(expected_cols)}"
        )

    data.columns = expected_cols
    data["date"] = parse_bddk_date(data["date"])
    data = data.dropna(subset=["date"]).sort_values("date")

    for col in value_columns:
        data[col] = clean_numeric(data[col])

    data["week_ending"] = data["date"]
    return data


def build_banking_weekly_core(raw_dir: Path) -> pd.DataFrame:
    bddk_dir = raw_dir / "bddk"

    loans_cols = [
        "total_loans_try", "total_loans_fx", "total_loans_total",
        "consumer_loans_cc_try", "consumer_loans_cc_fx", "consumer_loans_cc_total",
        "commercial_other_loans_try", "commercial_other_loans_fx", "commercial_other_loans_total",
        "sme_loans_try", "sme_loans_fx", "sme_loans_total",
        "fx_indexed_loans_try", "fx_indexed_loans_fx", "fx_indexed_loans_total",
    ]

    deposits_cols = [
        "total_deposits_try", "total_deposits_fx", "total_deposits_total",
        "natural_person_deposits_try", "natural_person_deposits_fx", "natural_person_deposits_total",
        "natural_person_demand_try", "natural_person_demand_fx", "natural_person_demand_total",
        "natural_person_term_try", "natural_person_term_fx", "natural_person_term_total",
        "commercial_deposits_try", "commercial_deposits_fx", "commercial_deposits_total",
        "commercial_demand_try", "commercial_demand_fx", "commercial_demand_total",
        "commercial_term_try", "commercial_term_fx", "commercial_term_total",
        "official_other_deposits_try", "official_other_deposits_fx", "official_other_deposits_total",
        "official_other_demand_try", "official_other_demand_fx", "official_other_demand_total",
        "official_other_term_try", "official_other_term_fx", "official_other_term_total",
        "kkm_deposits_try", "kkm_deposits_fx", "kkm_deposits_total",
    ]

    securities_cols = [
        "total_securities_try", "total_securities_fx", "total_securities_total",
        "fvpl_securities_try", "fvpl_securities_fx", "fvpl_securities_total",
        "fvoci_securities_try", "fvoci_securities_fx", "fvoci_securities_total",
        "amortised_cost_securities_try", "amortised_cost_securities_fx", "amortised_cost_securities_total",
        "repo_securities_try", "repo_securities_fx", "repo_securities_total",
        "collateral_securities_try", "collateral_securities_fx", "collateral_securities_total",
        "eurobonds_try", "eurobonds_fx", "eurobonds_total",
    ]

    fx_position_cols = [
        "balance_sheet_fx_position_try", "balance_sheet_fx_position_fx", "balance_sheet_fx_position_total",
        "balance_sheet_fx_assets_try", "balance_sheet_fx_assets_fx", "balance_sheet_fx_assets_total",
        "balance_sheet_fx_liabilities_try", "balance_sheet_fx_liabilities_fx", "balance_sheet_fx_liabilities_total",
        "off_bs_fx_position_try", "off_bs_fx_position_fx", "off_bs_fx_position_total",
        "off_bs_fx_assets_try", "off_bs_fx_assets_fx", "off_bs_fx_assets_total",
        "off_bs_fx_liabilities_try", "off_bs_fx_liabilities_fx", "off_bs_fx_liabilities_total",
        "fx_net_general_position_try", "fx_net_general_position_fx", "fx_net_general_position_total",
        "regulatory_capital_try", "regulatory_capital_fx", "regulatory_capital_total",
        "fx_indexed_assets_try", "fx_indexed_assets_fx", "fx_indexed_assets_total",
        "fx_indexed_liabilities_try", "fx_indexed_liabilities_fx", "fx_indexed_liabilities_total",
    ]

    loans = read_bddk_html_xls(bddk_dir / "loans.xls", loans_cols)
    deposits = read_bddk_html_xls(bddk_dir / "deposits.xls", deposits_cols)
    securities = read_bddk_html_xls(bddk_dir / "securities.xls", securities_cols)
    fx_position = read_bddk_html_xls(bddk_dir / "fx_general_position.xls", fx_position_cols)

    weekly = loans.merge(deposits, on=["date", "week_ending"], how="outer")
    weekly = weekly.merge(securities, on=["date", "week_ending"], how="outer")
    weekly = weekly.merge(fx_position, on=["date", "week_ending"], how="outer")
    weekly = weekly.sort_values("week_ending")

    # Core sector indicators.
    weekly["total_loans"] = weekly["total_loans_total"]
    weekly["total_deposits"] = weekly["total_deposits_total"]
    weekly["tl_deposits"] = weekly["total_deposits_try"]
    weekly["fx_deposits"] = weekly["total_deposits_fx"]
    weekly["kkm_deposits"] = weekly["kkm_deposits_total"]
    weekly["total_securities"] = weekly["total_securities_total"]

    weekly["loan_deposit_ratio_pct"] = weekly["total_loans"] / weekly["total_deposits"] * 100
    weekly["loan_growth_wow_pct"] = weekly["total_loans"].pct_change() * 100
    weekly["deposit_growth_wow_pct"] = weekly["total_deposits"].pct_change() * 100
    weekly["loan_deposit_growth_gap_pp"] = weekly["loan_growth_wow_pct"] - weekly["deposit_growth_wow_pct"]

    weekly["fx_deposit_share_pct"] = weekly["fx_deposits"] / weekly["total_deposits"] * 100
    weekly["tl_deposit_share_pct"] = weekly["tl_deposits"] / weekly["total_deposits"] * 100
    weekly["kkm_share_pct"] = weekly["kkm_deposits"] / weekly["total_deposits"] * 100

    weekly["demand_deposits"] = (
        weekly["natural_person_demand_total"]
        + weekly["commercial_demand_total"]
        + weekly["official_other_demand_total"]
    )
    weekly["term_deposits"] = (
        weekly["natural_person_term_total"]
        + weekly["commercial_term_total"]
        + weekly["official_other_term_total"]
    )
    weekly["demand_deposit_share_pct"] = weekly["demand_deposits"] / weekly["total_deposits"] * 100
    weekly["term_deposit_share_pct"] = weekly["term_deposits"] / weekly["total_deposits"] * 100

    weekly["natural_person_deposit_share_pct"] = (
        weekly["natural_person_deposits_total"] / weekly["total_deposits"] * 100
    )
    weekly["commercial_deposit_share_pct"] = (
        weekly["commercial_deposits_total"] / weekly["total_deposits"] * 100
    )

    weekly["securities_to_deposits_pct"] = weekly["total_securities"] / weekly["total_deposits"] * 100
    weekly["repo_securities_share_pct"] = weekly["repo_securities_total"] / weekly["total_securities"] * 100
    weekly["collateral_securities_share_pct"] = (
        weekly["collateral_securities_total"] / weekly["total_securities"] * 100
    )

    weekly["fx_position_to_capital_pct"] = (
        weekly["fx_net_general_position_total"] / weekly["regulatory_capital_total"] * 100
    )

    return weekly


def latest_banking_snapshot(weekly: pd.DataFrame) -> pd.DataFrame:
    latest = weekly.iloc[-1]

    rows = [
        ("Total loans", latest.get("total_loans"), "TRY mn", "Banking-sector credit stock"),
        ("Total deposits", latest.get("total_deposits"), "TRY mn", "Banking-sector deposit funding base"),
        ("Loan/deposit ratio", latest.get("loan_deposit_ratio_pct"), "%", "Sector funding balance proxy"),
        ("FX deposit share", latest.get("fx_deposit_share_pct"), "%", "Dollarization / funding mix proxy"),
        ("KKM share", latest.get("kkm_share_pct"), "%", "FX-protected TL deposit stock proxy"),
        ("Demand deposit share", latest.get("demand_deposit_share_pct"), "%", "Deposit stability / repricing proxy"),
        ("Securities/deposits", latest.get("securities_to_deposits_pct"), "%", "Liquidity and collateral proxy"),
        ("Repo securities share", latest.get("repo_securities_share_pct"), "%", "Repo-linked securities proxy"),
        ("Collateral securities share", latest.get("collateral_securities_share_pct"), "%", "Collateral availability proxy"),
        ("FX position/capital", latest.get("fx_position_to_capital_pct"), "%", "Capital-relative FX position proxy"),
    ]

    return pd.DataFrame(rows, columns=["metric", "latest_reading", "unit", "interpretation"])


def save_line_chart(df: pd.DataFrame, x: str, y_cols: list[str], title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))
    for col in y_cols:
        if col in df.columns:
            plt.plot(df[x], df[col], label=col)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, help="Local raw-data directory path")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).expanduser().resolve()
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    weekly = build_banking_weekly_core(raw_dir)
    weekly_path = tables_dir / "banking_weekly_core.csv"
    weekly.to_csv(weekly_path, index=False)

    snapshot = latest_banking_snapshot(weekly)
    snapshot_path = tables_dir / "latest_banking_dashboard_snapshot.csv"
    snapshot.to_csv(snapshot_path, index=False)

    save_line_chart(
        weekly,
        "week_ending",
        ["total_loans", "total_deposits"],
        "Banking-Sector Liquidity: Loans and Deposits",
        "TRY mn",
        charts_dir / "banking_loans_deposits.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["loan_deposit_ratio_pct"],
        "Banking-Sector Loan/Deposit Ratio",
        "%",
        charts_dir / "banking_loan_deposit_ratio.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["fx_deposit_share_pct", "tl_deposit_share_pct", "kkm_share_pct"],
        "Deposit Structure: TL, FX and KKM Shares",
        "%",
        charts_dir / "deposit_structure.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["securities_to_deposits_pct", "repo_securities_share_pct", "collateral_securities_share_pct"],
        "Securities Liquidity and Collateral Proxies",
        "%",
        charts_dir / "securities_liquidity_proxy.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["fx_position_to_capital_pct"],
        "FX Net General Position / Regulatory Capital",
        "%",
        charts_dir / "fx_position_capital_proxy.png",
    )

    print(f"Banking-sector dashboard dataset written to: {weekly_path}")
    print(f"Latest banking dashboard snapshot written to: {snapshot_path}")
    print(f"Charts written to: {charts_dir}")
    print("\nLatest banking snapshot:")
    print(snapshot.to_string(index=False))


if __name__ == "__main__":
    main()
