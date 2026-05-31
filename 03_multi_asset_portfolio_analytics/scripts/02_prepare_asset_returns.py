"""
Prepare clean asset prices, daily returns, index series and portfolio weights
for the Türkiye Multi-Asset Portfolio Analytics case.

Usage:
    python scripts/02_prepare_asset_returns.py --workbook "/path/to/turkiye_multi_asset_analysis_risk_return_fixed.xlsx"

Outputs:
    outputs/tables/clean_prices.csv
    outputs/tables/daily_returns.csv
    outputs/tables/index_100.csv
    outputs/tables/portfolio_weights.csv
    outputs/tables/asset_summary.csv
    outputs/tables/portfolio_summary.csv
    outputs/charts/asset_performance_indexed_100.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def read_sheet(workbook: Path, sheet_name: str, date_cols: list[str] | None = None) -> pd.DataFrame:
    df = pd.read_excel(workbook, sheet_name=sheet_name)

    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def save_line_chart(df: pd.DataFrame, x_col: str, y_cols: list[str], title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))
    for col in y_cols:
        if col in df.columns:
            plt.plot(df[x_col], df[col], label=col)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", required=True, help="Local multi-asset analysis workbook path")
    args = parser.parse_args()

    workbook = Path(args.workbook).expanduser().resolve()
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    clean_prices = read_sheet(workbook, "Clean_Prices", ["Date"])
    daily_returns = read_sheet(workbook, "Daily_Returns", ["Date"])
    index_100 = read_sheet(workbook, "Index_100", ["Date"])
    portfolio_weights = read_sheet(workbook, "Portfolio_Weights")
    portfolio_returns = read_sheet(workbook, "Portfolio_Returns", ["Date"])
    portfolio_index_100 = read_sheet(workbook, "Portfolio_Index_100", ["Date"])
    workbook_drawdowns = read_sheet(workbook, "Drawdowns", ["Date"])
    asset_summary = read_sheet(workbook, "Asset_Summary", ["Start Date", "End Date"])
    portfolio_summary = read_sheet(workbook, "Portfolio_Summary", ["Start Date", "End Date"])

    clean_prices.to_csv(tables_dir / "clean_prices.csv", index=False)
    daily_returns.to_csv(tables_dir / "daily_returns.csv", index=False)
    index_100.to_csv(tables_dir / "index_100.csv", index=False)
    portfolio_weights.to_csv(tables_dir / "portfolio_weights.csv", index=False)
    portfolio_returns.to_csv(tables_dir / "portfolio_returns.csv", index=False)
    portfolio_index_100.to_csv(tables_dir / "portfolio_index_100.csv", index=False)
    workbook_drawdowns.to_csv(tables_dir / "workbook_drawdowns.csv", index=False)
    asset_summary.to_csv(tables_dir / "asset_summary.csv", index=False)
    portfolio_summary.to_csv(tables_dir / "portfolio_summary.csv", index=False)

    asset_index_cols = [c for c in index_100.columns if c != "Date"]
    save_line_chart(
        index_100,
        "Date",
        asset_index_cols,
        "Asset Performance Indexed to 100",
        "Index = 100 at start",
        charts_dir / "asset_performance_indexed_100.png",
    )

    print("Prepared asset price, return and summary tables.")
    print(f"Tables written to: {tables_dir}")
    print(f"Chart written to: {charts_dir / 'asset_performance_indexed_100.png'}")

    print("\nAsset summary:")
    print(asset_summary.to_string(index=False))

    print("\nPortfolio summary:")
    print(portfolio_summary.to_string(index=False))


if __name__ == "__main__":
    main()
