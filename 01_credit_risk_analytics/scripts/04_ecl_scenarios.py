from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "test_predictions_with_risk_bands.csv"

CHARTS_PATH = PROJECT_ROOT / "outputs" / "charts"
TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"

CHARTS_PATH.mkdir(parents=True, exist_ok=True)
TABLES_PATH.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# ECL assumptions
# ------------------------------------------------------------

BASE_LGD = 0.45

SCENARIOS = {
    "Base": {
        "pd_multiplier": 1.00,
        "lgd": 0.45,
        "ead_multiplier": 1.00,
    },
    "Mild Deterioration": {
        "pd_multiplier": 1.15,
        "lgd": 0.50,
        "ead_multiplier": 1.00,
    },
    "Adverse": {
        "pd_multiplier": 1.25,
        "lgd": 0.55,
        "ead_multiplier": 1.00,
    },
    "Severe Stress": {
        "pd_multiplier": 1.50,
        "lgd": 0.60,
        "ead_multiplier": 1.00,
    },
}


RISK_BAND_ORDER = ["Low Risk", "Medium Risk", "High Risk", "Very High Risk"]


def assign_ifrs9_stage(row):
    """
    Assign simplified IFRS 9-style stage.

    This is an illustrative proxy:
    - Stage 3: observed default in the test sample
    - Stage 2: non-defaulted loans in High or Very High risk bands
    - Stage 1: non-defaulted loans in Low or Medium risk bands
    """
    if row["default_flag"] == 1:
        return "Stage 3"
    if row["risk_band"] in ["High Risk", "Very High Risk"]:
        return "Stage 2"
    return "Stage 1"


def lifetime_pd_proxy(pd_12m, stage):
    """
    Convert model PD into simplified stage-specific PD proxy.

    This is not a regulatory IFRS 9 lifetime PD model.
    It is an illustrative portfolio analytics proxy.
    """
    if stage == "Stage 1":
        return pd_12m
    if stage == "Stage 2":
        return np.minimum(pd_12m * 2.0, 1.0)
    if stage == "Stage 3":
        return 1.0
    return pd_12m


def calculate_base_ecl(df):
    """Calculate simplified IFRS 9-style base ECL."""
    df = df.copy()

    df["ifrs9_stage_proxy"] = df.apply(assign_ifrs9_stage, axis=1)
    df["pd_12m"] = df["pd_primary"]
    df["pd_ecl_base"] = df.apply(
        lambda row: lifetime_pd_proxy(row["pd_12m"], row["ifrs9_stage_proxy"]),
        axis=1,
    )

    df["lgd_base"] = BASE_LGD
    df["ead_base"] = df["ead_proxy"]

    df["ecl_base"] = df["pd_ecl_base"] * df["lgd_base"] * df["ead_base"]

    return df


def create_stage_summary(df):
    """Summarize exposure and ECL by simplified IFRS 9-style stage."""
    summary = (
        df.groupby("ifrs9_stage_proxy")
        .agg(
            loans=("default_flag", "size"),
            exposure=("ead_base", "sum"),
            avg_pd_12m=("pd_12m", "mean"),
            avg_pd_ecl=("pd_ecl_base", "mean"),
            lgd=("lgd_base", "mean"),
            ecl=("ecl_base", "sum"),
            actual_default_rate=("default_flag", "mean"),
        )
        .reset_index()
    )

    summary["exposure_share"] = summary["exposure"] / summary["exposure"].sum()
    summary["ecl_share"] = summary["ecl"] / summary["ecl"].sum()
    summary["ecl_rate"] = summary["ecl"] / summary["exposure"]

    return summary


def create_risk_band_ecl_summary(df):
    """Summarize ECL by risk band."""
    summary = (
        df.groupby("risk_band", observed=True)
        .agg(
            loans=("default_flag", "size"),
            exposure=("ead_base", "sum"),
            avg_pd_12m=("pd_12m", "mean"),
            avg_pd_ecl=("pd_ecl_base", "mean"),
            actual_default_rate=("default_flag", "mean"),
            ecl=("ecl_base", "sum"),
            defaults=("default_flag", "sum"),
        )
        .reset_index()
    )

    summary["exposure_share"] = summary["exposure"] / summary["exposure"].sum()
    summary["ecl_share"] = summary["ecl"] / summary["ecl"].sum()
    summary["ecl_rate"] = summary["ecl"] / summary["exposure"]

    summary["risk_band"] = pd.Categorical(
        summary["risk_band"],
        categories=RISK_BAND_ORDER,
        ordered=True,
    )
    summary = summary.sort_values("risk_band")

    return summary


def create_scenario_summary(df):
    """Calculate portfolio ECL under stress scenarios."""
    scenario_rows = []

    for scenario_name, assumptions in SCENARIOS.items():
        pd_stressed = np.minimum(df["pd_ecl_base"] * assumptions["pd_multiplier"], 1.0)
        lgd = assumptions["lgd"]
        ead = df["ead_proxy"] * assumptions["ead_multiplier"]

        ecl = pd_stressed * lgd * ead

        scenario_rows.append(
            {
                "scenario": scenario_name,
                "pd_multiplier": assumptions["pd_multiplier"],
                "lgd_assumption": lgd,
                "ead_multiplier": assumptions["ead_multiplier"],
                "total_exposure": ead.sum(),
                "total_ecl": ecl.sum(),
                "ecl_rate": ecl.sum() / ead.sum(),
                "average_pd_ecl": pd_stressed.mean(),
                "ecl_increase_vs_base": np.nan,
                "ecl_increase_pct_vs_base": np.nan,
            }
        )

    scenario = pd.DataFrame(scenario_rows)

    base_ecl = scenario.loc[scenario["scenario"] == "Base", "total_ecl"].iloc[0]
    scenario["ecl_increase_vs_base"] = scenario["total_ecl"] - base_ecl
    scenario["ecl_increase_pct_vs_base"] = scenario["total_ecl"] / base_ecl - 1

    return scenario


def create_scenario_by_risk_band(df):
    """Calculate scenario ECL by risk band."""
    rows = []

    for scenario_name, assumptions in SCENARIOS.items():
        temp = df.copy()
        temp["pd_stressed"] = np.minimum(temp["pd_ecl_base"] * assumptions["pd_multiplier"], 1.0)
        temp["lgd_scenario"] = assumptions["lgd"]
        temp["ead_scenario"] = temp["ead_proxy"] * assumptions["ead_multiplier"]
        temp["ecl_scenario"] = temp["pd_stressed"] * temp["lgd_scenario"] * temp["ead_scenario"]

        grouped = (
            temp.groupby("risk_band", observed=True)
            .agg(
                exposure=("ead_scenario", "sum"),
                ecl=("ecl_scenario", "sum"),
                avg_pd=("pd_stressed", "mean"),
            )
            .reset_index()
        )

        grouped["scenario"] = scenario_name
        grouped["ecl_rate"] = grouped["ecl"] / grouped["exposure"]
        rows.append(grouped)

    output = pd.concat(rows, ignore_index=True)

    output["risk_band"] = pd.Categorical(
        output["risk_band"],
        categories=RISK_BAND_ORDER,
        ordered=True,
    )

    return output.sort_values(["scenario", "risk_band"])


def save_ecl_charts(risk_band_summary, scenario_summary, scenario_band):
    """Save ECL-related charts."""
    # ECL by risk band
    plt.figure(figsize=(8, 6))
    plt.bar(risk_band_summary["risk_band"].astype(str), risk_band_summary["ecl"] / 1_000_000)
    plt.xlabel("Risk Band")
    plt.ylabel("ECL, USD million")
    plt.title("Illustrative ECL by Risk Band")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "ecl_by_risk_band.png", dpi=300)
    plt.close()

    # ECL rate by risk band
    plt.figure(figsize=(8, 6))
    plt.bar(risk_band_summary["risk_band"].astype(str), risk_band_summary["ecl_rate"])
    plt.xlabel("Risk Band")
    plt.ylabel("ECL / Exposure")
    plt.title("Illustrative ECL Rate by Risk Band")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "ecl_rate_by_risk_band.png", dpi=300)
    plt.close()

    # Scenario ECL comparison
    plt.figure(figsize=(9, 6))
    plt.bar(scenario_summary["scenario"], scenario_summary["total_ecl"] / 1_000_000)
    plt.xlabel("Scenario")
    plt.ylabel("Total ECL, USD million")
    plt.title("Scenario ECL Comparison")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "scenario_ecl_comparison.png", dpi=300)
    plt.close()

    # Scenario ECL rate comparison
    plt.figure(figsize=(9, 6))
    plt.bar(scenario_summary["scenario"], scenario_summary["ecl_rate"])
    plt.xlabel("Scenario")
    plt.ylabel("ECL / Exposure")
    plt.title("Portfolio ECL Rate under Stress Scenarios")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "scenario_ecl_rate_comparison.png", dpi=300)
    plt.close()


def main():
    print("Reading predictions with risk bands...")
    print(f"Predictions path: {PREDICTIONS_PATH}")

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Predictions with risk bands not found at {PREDICTIONS_PATH}. "
            "Please run scripts/03_model_validation.py first."
        )

    df = pd.read_csv(PREDICTIONS_PATH)

    print(f"Input shape: {df.shape}")
    print(f"Observed default rate: {df['default_flag'].mean():.4f}")
    print(f"Total exposure / EAD proxy: {df['ead_proxy'].sum():,.0f}")

    df_ecl = calculate_base_ecl(df)

    stage_summary = create_stage_summary(df_ecl)
    risk_band_ecl = create_risk_band_ecl_summary(df_ecl)
    scenario_summary = create_scenario_summary(df_ecl)
    scenario_band = create_scenario_by_risk_band(df_ecl)

    df_ecl.to_csv(PROJECT_ROOT / "data" / "interim" / "test_predictions_with_ecl.csv", index=False)
    stage_summary.to_csv(TABLES_PATH / "ifrs9_stage_ecl_summary.csv", index=False)
    risk_band_ecl.to_csv(TABLES_PATH / "ecl_by_risk_band.csv", index=False)
    scenario_summary.to_csv(TABLES_PATH / "scenario_ecl_summary.csv", index=False)
    scenario_band.to_csv(TABLES_PATH / "scenario_ecl_by_risk_band.csv", index=False)

    save_ecl_charts(risk_band_ecl, scenario_summary, scenario_band)

    print("Saved ECL tables:")
    print(TABLES_PATH / "ifrs9_stage_ecl_summary.csv")
    print(TABLES_PATH / "ecl_by_risk_band.csv")
    print(TABLES_PATH / "scenario_ecl_summary.csv")
    print(TABLES_PATH / "scenario_ecl_by_risk_band.csv")

    print("Saved ECL charts to:")
    print(CHARTS_PATH)

    print("Illustrative IFRS 9-style ECL scenario analysis completed successfully.")


if __name__ == "__main__":
    main()