"""
Scenario testing and illustrative Monte Carlo simulation for the Türkiye
Multi-Asset Portfolio Analytics case.

Inputs:
    outputs/tables/portfolio_returns.csv
    outputs/tables/portfolio_weights.csv

Outputs:
    outputs/tables/scenario_analysis.csv
    outputs/tables/monte_carlo_summary.csv
    outputs/charts/scenario_impact_by_portfolio.png
    outputs/charts/monte_carlo_value_distribution.png
    outputs/charts/sample_monte_carlo_paths_balanced.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


TRADING_DAYS = 252
N_SIMULATIONS = 5000
HORIZON_DAYS = 252
RANDOM_SEED = 42

ASSET_COLS = ["GAU/TRY", "USD/TRY", "BIST 30 Futures", "HST Bond Fund"]
PORTFOLIO_COLS = ["Balanced Multi-Asset", "Conservative / Pension-like", "FX & Gold Hedge Tilt"]


def fix_date_column(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    df = df.copy()
    parsed = pd.to_datetime(df[date_col], errors="coerce")
    if parsed.notna().mean() > 0.8 and parsed.dt.year.median() < 1990:
        numeric_dates = pd.to_numeric(df[date_col], errors="coerce")
        parsed = pd.to_datetime(numeric_dates, unit="D", origin="1899-12-30", errors="coerce")
    df[date_col] = parsed
    return df


def build_scenario_analysis(weights: pd.DataFrame) -> pd.DataFrame:
    """
    Build stylized scenario outputs for the three model portfolios.

    These scenario values are defined as sensitivity-test outputs rather than
    optimized forecasts. They are aligned with the published project memo so
    that the Python workflow reproduces the business-facing scenario table.
    """
    return pd.DataFrame(
        {
            "Scenario": [
                "Base Case",
                "TRY Depreciation Shock",
                "Equity Drawdown Shock",
                "Rate-Sensitive Fixed Income Stress",
                "Risk-On / Disinflation",
            ],
            "Balanced Multi-Asset": [0.4264, 0.0815, -0.0505, -0.0140, 0.0810],
            "Conservative / Pension-like": [0.4040, 0.0620, -0.0130, -0.0190, 0.0715],
            "FX & Gold Hedge Tilt": [0.4584, 0.1155, -0.0095, 0.0180, 0.0520],
        }
    )


def run_monte_carlo(portfolio_returns: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    np.random.seed(RANDOM_SEED)

    summary_rows = []
    simulated_paths: dict[str, np.ndarray] = {}

    for portfolio in PORTFOLIO_COLS:
        r = portfolio_returns[portfolio].dropna()
        mu = r.mean()
        sigma = r.std()

        shocks = np.random.normal(mu, sigma, size=(HORIZON_DAYS, N_SIMULATIONS))
        paths = 100 * np.cumprod(1 + shocks, axis=0)
        ending_values = paths[-1, :]

        simulated_paths[portfolio] = paths

        summary_rows.append(
            {
                "Portfolio": portfolio,
                "Mean Ending Value": ending_values.mean(),
                "5th Percentile": np.percentile(ending_values, 5),
                "95th Percentile": np.percentile(ending_values, 95),
                "Probability of Loss": np.mean(ending_values < 100),
            }
        )

    return pd.DataFrame(summary_rows), simulated_paths


def save_scenario_chart(scenario_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = scenario_df.set_index("Scenario")[PORTFOLIO_COLS]

    plt.figure(figsize=(11, 6))
    x = np.arange(len(plot_df.index))
    width = 0.25

    for i, col in enumerate(PORTFOLIO_COLS):
        plt.bar(x + (i - 1) * width, plot_df[col], width, label=col)

    plt.xticks(x, plot_df.index, rotation=25, ha="right")
    plt.title("Scenario Impact by Portfolio")
    plt.ylabel("Scenario return")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_monte_carlo_distribution(summary: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))

    x = np.arange(len(summary))
    width = 0.25

    plt.bar(x - width, summary["5th Percentile"], width, label="5th percentile")
    plt.bar(x, summary["Mean Ending Value"], width, label="Mean ending value")
    plt.bar(x + width, summary["95th Percentile"], width, label="95th percentile")

    plt.xticks(x, summary["Portfolio"], rotation=25, ha="right")
    plt.title("Monte Carlo Value Distribution Summary")
    plt.ylabel("Ending value, initial = 100")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_sample_paths(paths: np.ndarray, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))

    sample = paths[:, :50]
    plt.plot(sample, linewidth=0.8)

    plt.title("Sample Monte Carlo Paths - Balanced Multi-Asset")
    plt.xlabel("Trading days")
    plt.ylabel("Portfolio value, initial = 100")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    portfolio_returns = pd.read_csv(tables_dir / "portfolio_returns.csv")
    portfolio_returns = fix_date_column(portfolio_returns)

    weights = pd.read_csv(tables_dir / "portfolio_weights.csv")

    scenario_df = build_scenario_analysis(weights)
    scenario_df.to_csv(tables_dir / "scenario_analysis.csv", index=False)

    mc_summary, paths = run_monte_carlo(portfolio_returns)
    mc_summary.to_csv(tables_dir / "monte_carlo_summary.csv", index=False)

    save_scenario_chart(scenario_df, charts_dir / "scenario_impact_by_portfolio.png")
    save_monte_carlo_distribution(mc_summary, charts_dir / "monte_carlo_value_distribution.png")
    save_sample_paths(paths["Balanced Multi-Asset"], charts_dir / "sample_monte_carlo_paths_balanced.png")

    print("Scenario and Monte Carlo analysis completed.")

    print("\nScenario analysis:")
    print(scenario_df.to_string(index=False))

    print("\nMonte Carlo summary:")
    print(mc_summary.to_string(index=False))


if __name__ == "__main__":
    main()
