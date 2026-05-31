"""
Build project economics and sensitivity outputs for the Fortis Energy growth
capital screening memo.

This is a screening-level public-data analytical case. It is not a full
valuation, not due diligence, and not investment advice.

Outputs:
    outputs/tables/project_economics_summary.csv
    outputs/tables/sensitivity_analysis.csv
    outputs/tables/screening_scorecard.csv
    outputs/charts/project_economics_snapshot.png
    outputs/charts/irr_sensitivity.png
    outputs/charts/payback_sensitivity.png
    outputs/charts/screening_scorecard.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def npv(rate: float, cashflows: list[float]) -> float:
    return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))


def irr_bisection(cashflows: list[float], low: float = -0.9, high: float = 1.0, tol: float = 1e-7) -> float:
    """Simple IRR solver without external dependencies."""
    f_low = npv(low, cashflows)
    f_high = npv(high, cashflows)

    if f_low * f_high > 0:
        return np.nan

    for _ in range(200):
        mid = (low + high) / 2
        f_mid = npv(mid, cashflows)

        if abs(f_mid) < tol:
            return mid

        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    return (low + high) / 2


def build_base_economics() -> pd.DataFrame:
    capacity_mwp = 6.9
    annual_generation_mwh = 12_000
    capex_try_mn = 167.1
    ptf_try_per_mwh = 2619.81
    o_and_m_cost_try_mn = capex_try_mn * 0.02
    degradation = 0.005
    discount_rate = 0.15

    revenue_try_mn = annual_generation_mwh * ptf_try_per_mwh / 1_000_000
    ebitda_try_mn = revenue_try_mn - o_and_m_cost_try_mn
    capex_per_mwp = capex_try_mn / capacity_mwp
    specific_production = annual_generation_mwh / capacity_mwp
    capacity_factor = annual_generation_mwh / (capacity_mwp * 8760)
    simple_payback = capex_try_mn / ebitda_try_mn

    annual_ebitda = [
        ((annual_generation_mwh * ((1 - degradation) ** year)) * ptf_try_per_mwh / 1_000_000)
        - o_and_m_cost_try_mn
        for year in range(20)
    ]
    cashflows = [-capex_try_mn] + annual_ebitda
    project_irr = irr_bisection(cashflows)
    project_npv_15 = npv(discount_rate, cashflows)

    rows = [
        ("Capacity", capacity_mwp, "MWp"),
        ("Expected annual generation", annual_generation_mwh, "MWh"),
        ("Investment cost", capex_try_mn, "TRY mn"),
        ("CAPEX / MWp", capex_per_mwp, "TRY mn / MWp"),
        ("Specific production", specific_production, "MWh / MWp / year"),
        ("Capacity factor", capacity_factor, "%"),
        ("Base PTF", ptf_try_per_mwh, "TRY / MWh"),
        ("First-year revenue", revenue_try_mn, "TRY mn"),
        ("First-year EBITDA", ebitda_try_mn, "TRY mn"),
        ("Simple payback", simple_payback, "years"),
        ("Screening project IRR", project_irr, "%"),
        ("NPV @ 15%", project_npv_15, "TRY mn"),
    ]

    return pd.DataFrame(rows, columns=["Metric", "Value", "Unit"])


def build_sensitivity() -> pd.DataFrame:
    capacity_mwp = 6.9
    annual_generation_mwh = 12_000
    base_capex_try_mn = 167.1
    base_ptf = 2619.81

    rows = []

    for price_factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
        for capex_factor in [0.9, 1.0, 1.1]:
            ptf = base_ptf * price_factor
            capex = base_capex_try_mn * capex_factor
            o_and_m_cost = capex * 0.02
            revenue = annual_generation_mwh * ptf / 1_000_000
            ebitda = revenue - o_and_m_cost
            payback = capex / ebitda
            annual_ebitda = [
                ((annual_generation_mwh * ((1 - 0.005) ** year)) * ptf / 1_000_000)
                - o_and_m_cost
                for year in range(20)
            ]
            cashflows = [-capex] + annual_ebitda
            project_irr = irr_bisection(cashflows)
            project_npv_15 = npv(0.15, cashflows)

            rows.append(
                {
                    "PTF factor": price_factor,
                    "CAPEX factor": capex_factor,
                    "PTF TRY/MWh": ptf,
                    "CAPEX TRY mn": capex,
                    "Revenue TRY mn": revenue,
                    "EBITDA TRY mn": ebitda,
                    "Simple payback": payback,
                    "Project IRR": project_irr,
                    "NPV @ 15% TRY mn": project_npv_15,
                }
            )

    return pd.DataFrame(rows)


def build_scorecard() -> pd.DataFrame:
    rows = [
        ("Project benchmark clarity", 4, "Tokça SPP benchmark gives useful capacity, generation and capex anchors."),
        ("Revenue visibility", 3, "Merchant PTF exposure supports screening but needs offtake detail."),
        ("Self-consumption upside", 5, "C&I or municipal self-consumption could materially improve economics."),
        ("Platform scalability", 4, "Distributed solar pipeline can scale if demand and permits are visible."),
        ("Storage / resilience option", 3, "Storage-supported revenue resilience is attractive but requires separate diligence."),
        ("Due diligence completeness", 2, "Screening-level case; not full technical, legal or financial diligence."),
    ]

    return pd.DataFrame(rows, columns=["Criterion", "Score / 5", "Comment"])


def save_project_snapshot(summary: pd.DataFrame, output_path: Path) -> None:
    keep = summary[summary["Metric"].isin(["Investment cost", "First-year revenue", "First-year EBITDA"])]
    plt.figure(figsize=(8.5, 5))
    plt.bar(keep["Metric"], keep["Value"])
    plt.title("Fortis Energy Screening Economics Snapshot")
    plt.ylabel("TRY mn")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_irr_sensitivity(sensitivity: pd.DataFrame, output_path: Path) -> None:
    pivot = sensitivity[sensitivity["CAPEX factor"] == 1.0].copy()
    plt.figure(figsize=(8.5, 5))
    plt.plot(pivot["PTF factor"], pivot["Project IRR"], marker="o")
    plt.title("Project IRR Sensitivity to Power Price")
    plt.xlabel("PTF factor")
    plt.ylabel("Project IRR")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_payback_sensitivity(sensitivity: pd.DataFrame, output_path: Path) -> None:
    pivot = sensitivity[sensitivity["CAPEX factor"] == 1.0].copy()
    plt.figure(figsize=(8.5, 5))
    plt.plot(pivot["PTF factor"], pivot["Simple payback"], marker="o")
    plt.title("Simple Payback Sensitivity to Power Price")
    plt.xlabel("PTF factor")
    plt.ylabel("Years")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_scorecard(scorecard: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(9, 5.5))
    plt.barh(scorecard["Criterion"], scorecard["Score / 5"])
    plt.title("Growth Capital Screening Scorecard")
    plt.xlabel("Score / 5")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    summary = build_base_economics()
    sensitivity = build_sensitivity()
    scorecard = build_scorecard()

    summary.to_csv(tables_dir / "project_economics_summary.csv", index=False)
    sensitivity.to_csv(tables_dir / "sensitivity_analysis.csv", index=False)
    scorecard.to_csv(tables_dir / "screening_scorecard.csv", index=False)

    save_project_snapshot(summary, charts_dir / "project_economics_snapshot.png")
    save_irr_sensitivity(sensitivity, charts_dir / "irr_sensitivity.png")
    save_payback_sensitivity(sensitivity, charts_dir / "payback_sensitivity.png")
    save_scorecard(scorecard, charts_dir / "screening_scorecard.png")

    print("Fortis screening economics completed.")
    print("\nProject economics summary:")
    print(summary.to_string(index=False))

    print("\nScreening scorecard:")
    print(scorecard.to_string(index=False))


if __name__ == "__main__":
    main()
