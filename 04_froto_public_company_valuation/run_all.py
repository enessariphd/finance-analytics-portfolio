"""
Run the FROTO public company valuation case workflow.

Usage:
    python run_all.py --workbook "/path/to/FROTO_DCF_Trading_Comps_Model_v1_9.xlsx"

This workflow:
1. Inspects the local valuation workbook
2. Extracts memo-ready valuation outputs and sensitivity tables
3. Generates Python valuation charts
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
    parser.add_argument("--workbook", required=True, help="Local FROTO valuation workbook path")
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
            str(project_dir / "scripts" / "02_extract_valuation_outputs.py"),
            "--workbook",
            args.workbook,
        ],
        [
            sys.executable,
            str(project_dir / "scripts" / "03_generate_valuation_charts.py"),
        ],
    ]

    for step in steps:
        run_step(step)

    print("\nWorkflow completed successfully.")
    print(f"Outputs written under: {project_dir / 'outputs'}")


if __name__ == "__main__":
    main()
