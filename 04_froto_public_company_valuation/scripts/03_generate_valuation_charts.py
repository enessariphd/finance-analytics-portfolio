"""
Generate valuation charts for the FROTO public company valuation case.

Inputs:
    outputs/tables/valuation_methods_summary.csv
    outputs/tables/real_dcf_case_calculation.csv
    outputs/tables/wacc_terminal_growth_sensitivity.csv
    outputs/tables/peer_multiple_summary.csv
    outputs/tables/beta_sensitivity.csv

Outputs:
    outputs/charts/valuation_overview_python.png
    outputs/charts/real_dcf_case_range.png
    outputs/charts/wacc_terminal_growth_sensitivity_heatmap.png
    outputs/charts/peer_multiple_summary.png
    outputs/charts/beta_sensitivity.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def save_valuation_overview(valuation: pd.DataFrame, output_path: Path) -> None:
    plot_df = valuation[
        valuation["Method"].isin(
            [
                "Current price",
                "IAS29-consistent real DCF",
                "Bear real DCF case",
                "Bull real DCF case",
                "Şeker Invest target price",
                "Core manufacturing EV/EBITDA comps",
                "Broader BIST auto P/E comps",
            ]
        )
    ].copy()

    # The table uses "Current price" as a column, not a row. Add it explicitly.
    current_price = valuation["Current price"].dropna().iloc[0]
    extra = pd.DataFrame(
        [{"Method": "Current price", "Implied price (TRY/share)": current_price}]
    )

    plot_df = valuation[
        valuation["Method"].isin(
            [
                "IAS29-consistent real DCF",
                "Bear real DCF case",
                "Bull real DCF case",
                "Şeker Invest target price",
                "Core manufacturing EV/EBITDA comps",
                "Broader BIST auto P/E comps",
            ]
        )
    ][["Method", "Implied price (TRY/share)"]]

    plot_df = pd.concat([extra, plot_df], ignore_index=True)
    plot_df["Implied price (TRY/share)"] = pd.to_numeric(plot_df["Implied price (TRY/share)"], errors="coerce")

    plt.figure(figsize=(10, 5.8))
    plt.barh(plot_df["Method"], plot_df["Implied price (TRY/share)"])
    plt.title("FROTO Valuation Overview")
    plt.xlabel("TRY/share")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_real_dcf_range(real_dcf: pd.DataFrame, current_price: float, output_path: Path) -> None:
    df = real_dcf.copy()
    df["Implied price"] = pd.to_numeric(df["Implied price"], errors="coerce")

    plt.figure(figsize=(9, 5.5))
    plt.bar(df["Case"], df["Implied price"])
    plt.axhline(current_price, linestyle="--", linewidth=1, label="Current price")
    plt.title("Real DCF Case Range")
    plt.ylabel("TRY/share")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_sensitivity_heatmap(sensitivity: pd.DataFrame, output_path: Path) -> None:
    df = sensitivity.copy()
    df = df.drop(columns=["Notes"], errors="ignore")
    df["WACC"] = pd.to_numeric(df["WACC"], errors="coerce")
    df = df.set_index("WACC")
    df.columns = [float(c) for c in df.columns]
    values = df.astype(float).values

    plt.figure(figsize=(8, 5.8))
    plt.imshow(values, aspect="auto")
    plt.colorbar(label="DCF implied price, TRY/share")
    plt.xticks(np.arange(len(df.columns)), [f"{c:.0%}" for c in df.columns])
    plt.yticks(np.arange(len(df.index)), [f"{i:.1%}" for i in df.index])
    plt.title("DCF Sensitivity: WACC × Terminal Growth")
    plt.xlabel("Terminal growth")
    plt.ylabel("WACC")

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            plt.text(j, i, f"{values[i, j]:.1f}", ha="center", va="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_peer_summary(peer_summary: pd.DataFrame, output_path: Path) -> None:
    df = peer_summary.copy()
    df["EV/EBITDA"] = pd.to_numeric(df["EV/EBITDA"], errors="coerce")

    plt.figure(figsize=(9, 5.5))
    plt.bar(df["Peer set"], df["EV/EBITDA"])
    plt.title("Peer Set EV/EBITDA Summary")
    plt.ylabel("EV/EBITDA")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_beta_sensitivity(beta: pd.DataFrame, output_path: Path) -> None:
    df = beta.copy()
    df["DCF implied price"] = pd.to_numeric(df["DCF implied price"], errors="coerce")
    df["Real WACC"] = pd.to_numeric(df["Real WACC"], errors="coerce")

    plt.figure(figsize=(9, 5.5))
    plt.plot(df["Beta case"], df["DCF implied price"], marker="o")
    plt.title("Beta Sensitivity: DCF Implied Price")
    plt.ylabel("TRY/share")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    valuation = pd.read_csv(tables_dir / "valuation_methods_summary.csv")
    real_dcf = pd.read_csv(tables_dir / "real_dcf_case_calculation.csv")
    sensitivity = pd.read_csv(tables_dir / "wacc_terminal_growth_sensitivity.csv")
    peer_summary = pd.read_csv(tables_dir / "peer_multiple_summary.csv")
    beta = pd.read_csv(tables_dir / "beta_sensitivity.csv")

    current_price = pd.to_numeric(valuation["Current price"], errors="coerce").dropna().iloc[0]

    save_valuation_overview(valuation, charts_dir / "valuation_overview_python.png")
    save_real_dcf_range(real_dcf, current_price, charts_dir / "real_dcf_case_range.png")
    save_sensitivity_heatmap(sensitivity, charts_dir / "wacc_terminal_growth_sensitivity_heatmap.png")
    save_peer_summary(peer_summary, charts_dir / "peer_multiple_summary.png")
    save_beta_sensitivity(beta, charts_dir / "beta_sensitivity.png")

    print("Valuation charts generated.")
    print(f"Charts written to: {charts_dir}")


if __name__ == "__main__":
    main()
