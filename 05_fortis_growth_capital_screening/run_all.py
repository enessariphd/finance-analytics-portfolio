"""
Run the Fortis Energy Growth Capital Screening workflow.

Usage:
    python run_all.py

This workflow:
1. Builds screening-level project economics
2. Generates sensitivity tables
3. Generates screening scorecard outputs
4. Produces charts for the growth capital memo
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_step(command: list[str]) -> None:
    print("\n" + "=" * 90)
    print("Running:", " ".join(command))
    print("=" * 90)
    subprocess.run(command, check=True)


def main() -> None:
    project_dir = Path(__file__).resolve().parent

    steps = [
        [
            sys.executable,
            str(project_dir / "scripts" / "01_project_economics.py"),
        ],
    ]

    for step in steps:
        run_step(step)

    print("\nWorkflow completed successfully.")
    print(f"Outputs written under: {project_dir / 'outputs'}")


if __name__ == "__main__":
    main()
