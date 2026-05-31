"""
Run the Türkiye Multi-Asset Portfolio Analytics workflow.

Usage:
    python run_all.py --workbook "/path/to/turkiye_multi_asset_analysis_risk_return_fixed.xlsx"

This workflow:
1. Inspects the local analysis workbook
2. Prepares clean prices, returns, portfolio weights and summary tables
3. Computes risk-return metrics, drawdowns, VaR and Expected Shortfall
4. Runs stylized scenario analysis and illustrative Monte Carlo simulation
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(command: list[str]) -> None:
    print("\n" + "=" * 90)
    print("Running:", " ".join(command))
    print("=" * 90)
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", required=True, help="Local multi-asset analysis workbook path")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent

    steps = [
        [
            sys.executable,
            str(project_dir / "scripts" / "01_inspect_workbook.py"),
            "--workbook",
            args.workbook,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "02_prepare_asset_returns.py"),
            "--workbook",
            args.workbook,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "03_portfolio_risk_metrics.py"),
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "04_scenario_monte_carlo.py"),
        ],
    ]

    for step in steps:
        run_step(step)

    print("\nWorkflow completed successfully.")
    print(f"Outputs written under: {project_dir / 'outputs'}")


if __name__ == "__main__":
    main()
