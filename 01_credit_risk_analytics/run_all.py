from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent

SCRIPTS = [
    "scripts/01_prepare_data.py",
    "scripts/02_train_models.py",
    "scripts/03_model_validation.py",
    "scripts/04_ecl_scenarios.py",
    "scripts/05_model_interpretability.py",
    "scripts/06_generate_project_summary.py",
    "scripts/07_stability_and_strategy.py",
    "scripts/08_turkey_macro_overlay.py",
]


def run_script(script_path: str) -> None:
    full_path = PROJECT_ROOT / script_path

    if not full_path.exists():
        raise FileNotFoundError(f"Script not found: {full_path}")

    print("=" * 80)
    print(f"Running: {script_path}")
    print("=" * 80)

    start = time.time()

    result = subprocess.run(
        [sys.executable, str(full_path)],
        cwd=PROJECT_ROOT,
        text=True,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")

    print(f"Completed: {script_path} in {elapsed:.1f} seconds")


def main():
    print("Starting full Credit Risk Analytics Mini-Model pipeline...")
    print(f"Project root: {PROJECT_ROOT}")

    for script in SCRIPTS:
        run_script(script)

    print("=" * 80)
    print("Full pipeline completed successfully.")
    print("=" * 80)
    print("Key outputs:")
    print(PROJECT_ROOT / "outputs" / "tables" / "project_key_metrics.csv")
    print(PROJECT_ROOT / "outputs" / "charts")
    print(PROJECT_ROOT / "outputs" / "models")
    print(PROJECT_ROOT / "data" / "interim" / "test_predictions_with_ecl.csv")


if __name__ == "__main__":
    main()