"""
Prepare Garanti BBVA public-data-calibrated ALM proxy extension.

This module reads a locally stored bank financial statement extract derived from
Garanti BBVA unconsolidated public financial statements. The extract is not
included in the GitHub repository.

Usage:
    python scripts/05_prepare_bank_alm_proxy.py --bank-pack "/path/to/treasury_alm_data_pack_4_bank_alm_extension.xlsx"

Outputs:
    outputs/tables/bank_alm_key_metrics.csv
    outputs/tables/bank_maturity_ladder_proxy.csv
    outputs/tables/bank_liquidity_proxy.csv
    outputs/tables/bank_nii_sensitivity_proxy.csv
    outputs/charts/bank_alm_proxy_snapshot.png
    outputs/charts/bank_maturity_ladder_proxy.png
    outputs/charts/bank_nii_sensitivity_proxy.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_bank_extract(bank_pack: Path) -> pd.DataFrame:
    raw = pd.read_excel(bank_pack, sheet_name="Bank_FS_Raw_Extract", header=None)

    # Row 2 contains column names; rows 3 onward contain quarterly values.
    columns = raw.iloc[2].tolist()
    df = raw.iloc[3:].copy()
    df.columns = columns

    df = df.dropna(subset=["period_end"]).copy()
    df["period_end"] = pd.to_datetime(df["period_end"])

    numeric_cols = [c for c in df.columns if c not in {"period_end", "source_file"}]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("period_end")


def build_key_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["period_end", "source_file"]].copy()

    out["total_assets_tl_bn"] = df["total_assets"]
    out["loans_to_assets_pct"] = df["loans"] / df["total_assets"] * 100
    out["securities_to_assets_pct"] = df["securities_total"] / df["total_assets"] * 100
    out["cash_equiv_to_assets_pct"] = df["cash_equiv"] / df["total_assets"] * 100
    out["liquid_assets_proxy_to_assets_pct"] = (
        (df["cash_equiv"] + df["securities_total"]) / df["total_assets"] * 100
    )
    out["deposits_to_non_equity_liabilities_pct"] = (
        df["deposits"] / df["total_liabilities_ex_equity"] * 100
    )
    out["wholesale_funding_to_non_equity_liabilities_pct"] = (
        df["wholesale_funding"] / df["total_liabilities_ex_equity"] * 100
    )
    out["loan_deposit_ratio_pct"] = df["loans"] / df["deposits"] * 100
    out["liquid_assets_proxy_to_deposits_pct"] = (
        (df["cash_equiv"] + df["securities_total"]) / df["deposits"] * 100
    )
    out["fc_deposits_to_deposits_pct"] = df["deposits_FC"] / df["deposits"] * 100
    out["bs_fc_gap_to_equity_pct"] = df["balance_sheet_FC_gap"] / df["shareholders_equity"] * 100
    out["derivative_notional_to_assets_pct"] = df["derivative_notional"] / df["total_assets"] * 100
    out["risk_mgmt_derivatives_to_assets_pct"] = df["risk_mgmt_derivatives"] / df["total_assets"] * 100

    return out


def build_maturity_ladder(latest: pd.Series) -> pd.DataFrame:
    buckets = ["0-1M", "1-3M", "3-6M", "6-12M", "1Y+"]

    assumptions = pd.DataFrame(
        {
            "bucket": buckets,
            "cash_inflow_pct": [0.60, 0.20, 0.10, 0.05, 0.05],
            "securities_inflow_pct": [0.25, 0.20, 0.20, 0.15, 0.20],
            "loans_inflow_pct": [0.18, 0.20, 0.22, 0.20, 0.20],
            "deposit_outflow_pct": [0.25, 0.25, 0.20, 0.15, 0.15],
            "wholesale_outflow_pct": [0.25, 0.25, 0.20, 0.15, 0.15],
        }
    )

    assumptions["cash_equiv_inflow_tl_bn"] = latest["cash_equiv"] * assumptions["cash_inflow_pct"]
    assumptions["securities_inflow_tl_bn"] = latest["securities_total"] * assumptions["securities_inflow_pct"]
    assumptions["loans_inflow_tl_bn"] = latest["loans"] * assumptions["loans_inflow_pct"]
    assumptions["deposit_outflow_tl_bn"] = latest["deposits"] * assumptions["deposit_outflow_pct"]
    assumptions["wholesale_outflow_tl_bn"] = latest["wholesale_funding"] * assumptions["wholesale_outflow_pct"]

    assumptions["total_asset_inflow_tl_bn"] = (
        assumptions["cash_equiv_inflow_tl_bn"]
        + assumptions["securities_inflow_tl_bn"]
        + assumptions["loans_inflow_tl_bn"]
    )
    assumptions["total_liability_outflow_tl_bn"] = (
        assumptions["deposit_outflow_tl_bn"]
        + assumptions["wholesale_outflow_tl_bn"]
    )
    assumptions["net_gap_tl_bn"] = (
        assumptions["total_asset_inflow_tl_bn"] - assumptions["total_liability_outflow_tl_bn"]
    )
    assumptions["cumulative_gap_tl_bn"] = assumptions["net_gap_tl_bn"].cumsum()

    return assumptions


def build_liquidity_proxy(latest: pd.Series) -> pd.DataFrame:
    scenarios = pd.DataFrame(
        {
            "scenario": [
                "Base proxy",
                "Liquidity tightening",
                "FX / confidence stress",
                "Gold / FX volatility stress",
            ],
            "liquid_asset_haircut": [0.15, 0.20, 0.25, 0.25],
            "deposit_runoff_stress": [0.08, 0.12, 0.15, 0.12],
            "wholesale_rolloff_stress": [0.20, 0.30, 0.35, 0.30],
        }
    )

    liquid_assets = latest["cash_equiv"] + latest["securities_total"]

    scenarios["liquid_assets_proxy_tl_bn"] = liquid_assets
    scenarios["post_haircut_buffer_tl_bn"] = liquid_assets * (1 - scenarios["liquid_asset_haircut"])
    scenarios["deposits_stressed_outflow_tl_bn"] = latest["deposits"] * scenarios["deposit_runoff_stress"]
    scenarios["wholesale_stressed_outflow_tl_bn"] = latest["wholesale_funding"] * scenarios["wholesale_rolloff_stress"]
    scenarios["total_stressed_outflow_tl_bn"] = (
        scenarios["deposits_stressed_outflow_tl_bn"]
        + scenarios["wholesale_stressed_outflow_tl_bn"]
    )
    scenarios["coverage_proxy_pct"] = (
        scenarios["post_haircut_buffer_tl_bn"] / scenarios["total_stressed_outflow_tl_bn"] * 100
    )

    return scenarios


def build_nii_sensitivity(latest: pd.Series) -> pd.DataFrame:
    # Simplified repricing assumptions calibrated to the published memo's
    # public-data ALM proxy sensitivity table. This is not an internal bank NII
    # model; it is a transparent management-dashboard proxy.
    loans_rsa = latest["loans"] * 0.30
    securities_rsa = latest["securities_total"] * 0.20
    deposits_rsl = latest["deposits"] * 0.50
    wholesale_rsl = latest["wholesale_funding"] * 0.65

    rsa = loans_rsa + securities_rsa
    rsl = deposits_rsl + wholesale_rsl
    repricing_gap = rsa - rsl

    scenarios = pd.DataFrame(
        {
            "scenario": ["Rate cut -200 bps", "Rate shock +100 bps", "Liquidity tightening +300 bps"],
            "rate_shock_pp": [-2.0, 1.0, 3.0],
        }
    )
    scenarios["repricing_gap_tl_bn"] = repricing_gap
    scenarios["estimated_annual_nii_impact_tl_bn"] = repricing_gap * (scenarios["rate_shock_pp"] / 100)

    return scenarios


def save_key_metric_chart(metrics: pd.DataFrame, output_path: Path) -> None:
    latest = metrics.iloc[-1]

    chart_data = pd.Series(
        {
            "Loans / assets": latest["loans_to_assets_pct"],
            "Liquid assets / assets": latest["liquid_assets_proxy_to_assets_pct"],
            "Loan / deposit": latest["loan_deposit_ratio_pct"],
            "FC deposits / deposits": latest["fc_deposits_to_deposits_pct"],
            "BS FC gap / equity": latest["bs_fc_gap_to_equity_pct"],
        }
    )

    plt.figure(figsize=(10, 5.5))
    chart_data.plot(kind="bar")
    plt.title("Garanti BBVA Public-Data ALM Proxy Snapshot")
    plt.ylabel("%")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_maturity_ladder_chart(ladder: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))
    plt.plot(ladder["bucket"], ladder["net_gap_tl_bn"], marker="o", label="Net gap")
    plt.plot(ladder["bucket"], ladder["cumulative_gap_tl_bn"], marker="o", label="Cumulative gap")
    plt.title("Garanti BBVA Maturity Ladder Proxy")
    plt.ylabel("TL bn")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_nii_chart(nii: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(9, 5))
    plt.bar(nii["scenario"], nii["estimated_annual_nii_impact_tl_bn"])
    plt.title("Simplified Repricing-Gap Sensitivity Proxy")
    plt.ylabel("Estimated annual impact, TL bn")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank-pack", required=True, help="Local bank ALM extension workbook path")
    args = parser.parse_args()

    bank_pack = Path(args.bank_pack).expanduser().resolve()
    if not bank_pack.exists():
        raise FileNotFoundError(f"Bank pack not found: {bank_pack}")

    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    bank_extract = read_bank_extract(bank_pack)
    latest = bank_extract.iloc[-1]

    key_metrics = build_key_metrics(bank_extract)
    maturity_ladder = build_maturity_ladder(latest)
    liquidity_proxy = build_liquidity_proxy(latest)
    nii_sensitivity = build_nii_sensitivity(latest)

    bank_extract.to_csv(tables_dir / "bank_fs_raw_extract.csv", index=False)
    key_metrics.to_csv(tables_dir / "bank_alm_key_metrics.csv", index=False)
    maturity_ladder.to_csv(tables_dir / "bank_maturity_ladder_proxy.csv", index=False)
    liquidity_proxy.to_csv(tables_dir / "bank_liquidity_proxy.csv", index=False)
    nii_sensitivity.to_csv(tables_dir / "bank_nii_sensitivity_proxy.csv", index=False)

    save_key_metric_chart(key_metrics, charts_dir / "bank_alm_proxy_snapshot.png")
    save_maturity_ladder_chart(maturity_ladder, charts_dir / "bank_maturity_ladder_proxy.png")
    save_nii_chart(nii_sensitivity, charts_dir / "bank_nii_sensitivity_proxy.png")

    print("Bank ALM proxy extension completed.")
    print("\nLatest bank ALM key metrics:")
    print(key_metrics.tail(1).T.to_string())

    print("\nSimplified repricing-gap sensitivity:")
    print(nii_sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
