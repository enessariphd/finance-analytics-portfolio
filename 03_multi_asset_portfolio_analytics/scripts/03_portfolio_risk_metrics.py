"""
Compute asset and portfolio risk-return metrics for the Türkiye Multi-Asset
Portfolio Analytics case.

This script uses the cleaned Portfolio_Returns sheet exported by
02_prepare_asset_returns.py. That sheet contains both individual asset returns
and model portfolio returns on the same aligned date frame.

Inputs:
    outputs/tables/portfolio_returns.csv

Outputs:
    outputs/tables/asset_summary_recomputed.csv
    outputs/tables/portfolio_summary_recomputed.csv
    outputs/tables/correlation_matrix.csv
    outputs/tables/drawdowns.csv
    outputs/tables/historical_var_es.csv
    outputs/charts/asset_risk_return_map.png
    outputs/charts/portfolio_risk_return_map.png
    outputs/charts/portfolio_drawdowns.png
    outputs/charts/historical_var_expected_shortfall_portfolios.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


TRADING_DAYS = 252
VAR_LEVEL = 0.95

ASSET_COLS = ["GAU/TRY", "USD/TRY", "BIST 30 Futures", "HST Bond Fund"]
PORTFOLIO_COLS = ["Balanced Multi-Asset", "Conservative / Pension-like", "FX & Gold Hedge Tilt"]


def fix_date_column(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    df = df.copy()

    # First try standard date parsing.
    parsed = pd.to_datetime(df[date_col], errors="coerce")

    # If parsing collapses to 1970 because Excel serials were interpreted as
    # nanoseconds, retry as Excel serial dates.
    if parsed.notna().mean() > 0.8 and parsed.dt.year.median() < 1990:
        numeric_dates = pd.to_numeric(df[date_col], errors="coerce")
        parsed = pd.to_datetime(numeric_dates, unit="D", origin="1899-12-30", errors="coerce")

    df[date_col] = parsed
    return df


def annualized_return(returns: pd.Series) -> float:
    returns = returns.dropna()
    if returns.empty:
        return np.nan
    cumulative = (1 + returns).prod()
    years = len(returns) / TRADING_DAYS
    return cumulative ** (1 / years) - 1


def annualized_volatility(returns: pd.Series) -> float:
    return returns.dropna().std() * np.sqrt(TRADING_DAYS)


def max_drawdown_from_returns(returns: pd.Series) -> float:
    r = returns.dropna()
    index = (1 + r).cumprod()
    running_max = index.cummax()
    drawdown = index / running_max - 1
    return drawdown.min()


def compute_summary(returns: pd.DataFrame, series_cols: list[str], label_col: str) -> pd.DataFrame:
    rows = []

    for col in series_cols:
        r = returns[col].dropna()
        if r.empty:
            continue

        index = (1 + r).cumprod()
        ann_ret = annualized_return(r)
        ann_vol = annualized_volatility(r)

        rows.append(
            {
                label_col: col,
                "Total Return": index.iloc[-1] - 1,
                "Annualized Return": ann_ret,
                "Annualized Volatility": ann_vol,
                "Max Drawdown": max_drawdown_from_returns(r),
                "Best Daily Return": r.max(),
                "Worst Daily Return": r.min(),
                "Return / Volatility": ann_ret / ann_vol if ann_vol and not pd.isna(ann_vol) else np.nan,
                "Start Date": returns.loc[r.index.min(), "Date"].date(),
                "End Date": returns.loc[r.index.max(), "Date"].date(),
                "Observations": len(r),
            }
        )

    return pd.DataFrame(rows)


def compute_drawdowns(returns: pd.DataFrame, series_cols: list[str]) -> pd.DataFrame:
    out = pd.DataFrame({"Date": returns["Date"]})

    for col in series_cols:
        r = returns[col].fillna(0)
        index = (1 + r).cumprod()
        out[col] = index / index.cummax() - 1

    return out


def compute_var_es(returns: pd.DataFrame, series_cols: list[str]) -> pd.DataFrame:
    rows = []

    for col in series_cols:
        r = returns[col].dropna()
        if r.empty:
            continue

        var_95 = r.quantile(1 - VAR_LEVEL)
        es_95 = r[r <= var_95].mean()
        var_99 = r.quantile(0.01)
        es_99 = r[r <= var_99].mean()

        rows.append(
            {
                "Series": col,
                "Historical 95% VaR": var_95,
                "Historical 95% Expected Shortfall": es_95,
                "Historical 99% VaR": var_99,
                "Historical 99% Expected Shortfall": es_99,
                "Worst Daily Return": r.min(),
                "Best Daily Return": r.max(),
                "Observations": len(r),
            }
        )

    return pd.DataFrame(rows)


def save_risk_return_map(summary: pd.DataFrame, label_col: str, output_path: Path, title: str) -> None:
    plt.figure(figsize=(9, 6))
    plt.scatter(summary["Annualized Volatility"], summary["Annualized Return"])

    for _, row in summary.iterrows():
        plt.annotate(
            row[label_col],
            (row["Annualized Volatility"], row["Annualized Return"]),
            textcoords="offset points",
            xytext=(5, 5),
            ha="left",
        )

    plt.title(title)
    plt.xlabel("Annualized volatility")
    plt.ylabel("Annualized return")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_drawdown_chart(drawdowns: pd.DataFrame, series_cols: list[str], output_path: Path, title: str) -> None:
    plt.figure(figsize=(10, 5.5))

    for col in series_cols:
        plt.plot(drawdowns["Date"], drawdowns[col], label=col)

    plt.title(title)
    plt.xlabel("")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_var_es_chart(var_es: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))

    x = np.arange(len(var_es))
    width = 0.35

    plt.bar(x - width / 2, var_es["Historical 95% VaR"], width, label="VaR 95%")
    plt.bar(x + width / 2, var_es["Historical 95% Expected Shortfall"], width, label="Expected Shortfall 95%")

    plt.xticks(x, var_es["Series"], rotation=30, ha="right")
    plt.title("Historical 95% VaR and Expected Shortfall for Model Portfolios")
    plt.ylabel("Daily return")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    returns = pd.read_csv(tables_dir / "portfolio_returns.csv")
    returns = fix_date_column(returns)

    # Keep only the aligned clean return frame.
    required_cols = ["Date"] + ASSET_COLS + PORTFOLIO_COLS
    returns = returns[required_cols].copy()

    asset_summary = compute_summary(returns, ASSET_COLS, "Asset")
    portfolio_summary = compute_summary(returns, PORTFOLIO_COLS, "Portfolio")
    drawdowns = compute_drawdowns(returns, ASSET_COLS + PORTFOLIO_COLS)
    var_es = compute_var_es(returns, ASSET_COLS + PORTFOLIO_COLS)
    corr = returns[ASSET_COLS].corr()

    asset_summary.to_csv(tables_dir / "asset_summary_recomputed.csv", index=False)
    portfolio_summary.to_csv(tables_dir / "portfolio_summary_recomputed.csv", index=False)
    drawdowns.to_csv(tables_dir / "drawdowns.csv", index=False)
    var_es.to_csv(tables_dir / "historical_var_es.csv", index=False)
    corr.to_csv(tables_dir / "correlation_matrix.csv")

    save_risk_return_map(asset_summary, "Asset", charts_dir / "asset_risk_return_map.png", "Asset Risk-Return Map")
    save_risk_return_map(portfolio_summary, "Portfolio", charts_dir / "portfolio_risk_return_map.png", "Portfolio Risk-Return Map")
    save_drawdown_chart(drawdowns, PORTFOLIO_COLS, charts_dir / "portfolio_drawdowns.png", "Portfolio Drawdowns")
    save_var_es_chart(var_es[var_es["Series"].isin(PORTFOLIO_COLS)], charts_dir / "historical_var_expected_shortfall_portfolios.png")

    print("Risk-return metrics computed successfully.")
    print("\nAsset summary:")
    print(asset_summary.to_string(index=False))

    print("\nPortfolio summary:")
    print(portfolio_summary.to_string(index=False))

    print("\nHistorical VaR / ES:")
    print(var_es.to_string(index=False))


if __name__ == "__main__":
    main()
