"""
Run the Turkey Treasury / ALM & Liquidity Risk Dashboard workflow.

Usage:
    python run_all.py --raw-dir "/path/to/local/data_raw"

This workflow:
1. Audits raw public-data source files
2. Prepares market, FX/gold, yield, funding and reserves data
3. Prepares BDDK / BRSA banking-sector liquidity data
4. Builds the combined dashboard dataset and liquidity stress score
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
    parser.add_argument("--raw-dir", required=True, help="Local raw-data directory path")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent

    steps = [
        [
            sys.executable,
            str(project_dir / "scripts" / "01_inspect_raw_sources.py"),
            "--raw-dir",
            args.raw_dir,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "02_prepare_market_data.py"),
            "--raw-dir",
            args.raw_dir,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "03_prepare_banking_data.py"),
            "--raw-dir",
            args.raw_dir,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "04_build_dashboard_dataset.py"),
        ],
    ]

    for step in steps:
        run_step(step)

    print("\nWorkflow completed successfully.")
    print(f"Outputs written under: {project_dir / 'outputs'}")


if __name__ == "__main__":
    main()
