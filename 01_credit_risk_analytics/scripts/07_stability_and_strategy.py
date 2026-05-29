from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "train_predictions.csv"
TEST_PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "test_predictions_with_risk_bands.csv"

TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"
CHARTS_PATH = PROJECT_ROOT / "outputs" / "charts"

TABLES_PATH.mkdir(parents=True, exist_ok=True)
CHARTS_PATH.mkdir(parents=True, exist_ok=True)


TARGET = "default_flag"
PD_COL = "pd_primary"
EAD_COL = "ead_proxy"

RISK_BAND_ORDER = ["Low Risk", "Medium Risk", "High Risk", "Very High Risk"]


# ------------------------------------------------------------
# PSI helpers
# ------------------------------------------------------------

def calculate_psi(expected, actual, bins=10):
    """
    Calculate Population Stability Index.

    expected = reference distribution, usually train sample
    actual = comparison distribution, usually test sample

    PSI interpretation rule of thumb:
    - PSI < 0.10: stable / no material shift
    - 0.10 <= PSI < 0.25: moderate shift
    - PSI >= 0.25: significant shift
    """
    expected = pd.Series(expected).dropna()
    actual = pd.Series(actual).dropna()

    quantiles = np.linspace(0, 1, bins + 1)
    breakpoints = expected.quantile(quantiles).values
    breakpoints = np.unique(breakpoints)

    if len(breakpoints) <= 2:
        raise ValueError("Not enough unique breakpoints to calculate PSI.")

    expected_bins = pd.cut(expected, bins=breakpoints, include_lowest=True, duplicates="drop")
    actual_bins = pd.cut(actual, bins=breakpoints, include_lowest=True, duplicates="drop")

    expected_dist = expected_bins.value_counts(normalize=True, sort=False)
    actual_dist = actual_bins.value_counts(normalize=True, sort=False)

    psi_df = pd.DataFrame(
        {
            "bin": expected_dist.index.astype(str),
            "expected_share_train": expected_dist.values,
            "actual_share_test": actual_dist.reindex(expected_dist.index).fillna(0).values,
        }
    )

    epsilon = 1e-6
    psi_df["expected_share_train_adj"] = psi_df["expected_share_train"].clip(lower=epsilon)
    psi_df["actual_share_test_adj"] = psi_df["actual_share_test"].clip(lower=epsilon)

    psi_df["psi_component"] = (
        (psi_df["actual_share_test_adj"] - psi_df["expected_share_train_adj"])
        * np.log(psi_df["actual_share_test_adj"] / psi_df["expected_share_train_adj"])
    )

    total_psi = psi_df["psi_component"].sum()

    if total_psi < 0.10:
        interpretation = "Stable / no material shift"
    elif total_psi < 0.25:
        interpretation = "Moderate distribution shift"
    else:
        interpretation = "Significant distribution shift"

    return total_psi, interpretation, psi_df


def save_train_test_pd_distribution(train_df, test_df):
    """Save train-test predicted PD distribution chart."""
    plt.figure(figsize=(9, 6))
    plt.hist(train_df[PD_COL], bins=50, alpha=0.6, density=True, label="Train")
    plt.hist(test_df[PD_COL], bins=50, alpha=0.6, density=True, label="Test")
    plt.xlabel("Predicted Probability of Default")
    plt.ylabel("Density")
    plt.title("Train vs Test Predicted PD Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "train_test_pd_distribution.png", dpi=300)
    plt.close()


# ------------------------------------------------------------
# Threshold strategy simulation
# ------------------------------------------------------------

def create_threshold_strategy_simulation(test_df):
    """
    Simulate approval/rejection strategy using PD cutoffs.

    Interpretation:
    - approve loans with PD <= threshold
    - reject / manual-review loans with PD > threshold

    This is illustrative and not a recommended credit policy.
    """
    thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]

    rows = []

    total_loans = len(test_df)
    total_defaults = test_df[TARGET].sum()
    total_exposure = test_df[EAD_COL].sum()

    for threshold in thresholds:
        approved = test_df[test_df[PD_COL] <= threshold].copy()
        rejected = test_df[test_df[PD_COL] > threshold].copy()

        approved_loans = len(approved)
        rejected_loans = len(rejected)

        approved_defaults = approved[TARGET].sum()
        rejected_defaults = rejected[TARGET].sum()

        approved_exposure = approved[EAD_COL].sum()
        rejected_exposure = rejected[EAD_COL].sum()

        rows.append(
            {
                "pd_threshold": threshold,
                "approval_rate": approved_loans / total_loans,
                "rejection_or_review_rate": rejected_loans / total_loans,
                "approved_loans": approved_loans,
                "rejected_or_review_loans": rejected_loans,
                "approved_default_rate": approved[TARGET].mean() if approved_loans > 0 else np.nan,
                "rejected_or_review_default_rate": rejected[TARGET].mean() if rejected_loans > 0 else np.nan,
                "exposure_retained": approved_exposure,
                "exposure_retained_share": approved_exposure / total_exposure,
                "exposure_rejected_or_review": rejected_exposure,
                "default_capture_rate_in_rejected_or_review": rejected_defaults / total_defaults if total_defaults > 0 else np.nan,
                "defaults_in_approved": approved_defaults,
                "defaults_in_rejected_or_review": rejected_defaults,
            }
        )

    return pd.DataFrame(rows)


def save_threshold_strategy_chart(strategy_df):
    """Save approval rate vs approved default rate chart."""
    plt.figure(figsize=(9, 6))
    plt.plot(
        strategy_df["pd_threshold"],
        strategy_df["approval_rate"],
        marker="o",
        label="Approval rate",
    )
    plt.plot(
        strategy_df["pd_threshold"],
        strategy_df["approved_default_rate"],
        marker="o",
        label="Default rate among approved",
    )
    plt.xlabel("PD Approval Threshold")
    plt.ylabel("Rate")
    plt.title("Approval Threshold Simulation")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "approval_threshold_simulation.png", dpi=300)
    plt.close()

    plt.figure(figsize=(9, 6))
    plt.plot(
        strategy_df["pd_threshold"],
        strategy_df["default_capture_rate_in_rejected_or_review"],
        marker="o",
        label="Default capture rate in rejected/review segment",
    )
    plt.plot(
        strategy_df["pd_threshold"],
        strategy_df["exposure_retained_share"],
        marker="o",
        label="Exposure retained share",
    )
    plt.xlabel("PD Approval Threshold")
    plt.ylabel("Rate")
    plt.title("Risk Capture vs Exposure Retention by PD Threshold")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "risk_capture_vs_exposure_retention.png", dpi=300)
    plt.close()


# ------------------------------------------------------------
# Stress migration
# ------------------------------------------------------------

def create_band_cutoffs(test_df):
    """Create risk band cutoffs based on existing qcut bands."""
    cutoffs = (
        test_df.groupby("risk_band", observed=True)[PD_COL]
        .agg(min_pd="min", max_pd="max")
        .reset_index()
    )

    cutoffs["risk_band"] = pd.Categorical(
        cutoffs["risk_band"],
        categories=RISK_BAND_ORDER,
        ordered=True,
    )
    cutoffs = cutoffs.sort_values("risk_band")

    return cutoffs


def assign_band_from_base_cutoffs(pd_value, cutoffs):
    """Assign risk band using base PD cutoffs."""
    for _, row in cutoffs.iterrows():
        if row["min_pd"] <= pd_value <= row["max_pd"]:
            return str(row["risk_band"])

    if pd_value < cutoffs["min_pd"].min():
        return "Low Risk"

    return "Very High Risk"


def create_risk_band_migration(test_df, scenario_name, pd_multiplier):
    """
    Create migration matrix under stressed PDs.

    Stressed PD = min(base PD × multiplier, 1)
    New risk band is assigned using base risk-band PD cutoffs.
    """
    df = test_df.copy()
    cutoffs = create_band_cutoffs(df)

    df["base_risk_band"] = df["risk_band"].astype(str)
    df["pd_stressed"] = np.minimum(df[PD_COL] * pd_multiplier, 1.0)
    df["stressed_risk_band"] = df["pd_stressed"].apply(
        lambda x: assign_band_from_base_cutoffs(x, cutoffs)
    )

    migration = pd.crosstab(
        df["base_risk_band"],
        df["stressed_risk_band"],
        values=df[EAD_COL],
        aggfunc="sum",
        normalize="index",
    ).fillna(0)

    migration = migration.reindex(index=RISK_BAND_ORDER, columns=RISK_BAND_ORDER).fillna(0)

    migration_long = (
        migration.reset_index()
        .melt(
            id_vars="base_risk_band",
            var_name="stressed_risk_band",
            value_name="exposure_share_of_base_band",
        )
    )

    migration_long["scenario"] = scenario_name
    migration_long["pd_multiplier"] = pd_multiplier

    return migration_long


def save_migration_heatmap(migration_long, scenario_name):
    """Save simple heatmap-style chart for risk band migration."""
    matrix = migration_long.pivot(
        index="base_risk_band",
        columns="stressed_risk_band",
        values="exposure_share_of_base_band",
    ).reindex(index=RISK_BAND_ORDER, columns=RISK_BAND_ORDER).fillna(0)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix.values)

    ax.set_xticks(np.arange(len(RISK_BAND_ORDER)))
    ax.set_yticks(np.arange(len(RISK_BAND_ORDER)))
    ax.set_xticklabels(RISK_BAND_ORDER, rotation=30, ha="right")
    ax.set_yticklabels(RISK_BAND_ORDER)

    for i in range(len(RISK_BAND_ORDER)):
        for j in range(len(RISK_BAND_ORDER)):
            value = matrix.values[i, j]
            ax.text(j, i, f"{value:.1%}", ha="center", va="center")

    ax.set_xlabel("Stressed Risk Band")
    ax.set_ylabel("Base Risk Band")
    ax.set_title(f"Risk Band Migration under {scenario_name}")

    plt.tight_layout()

    filename = scenario_name.lower().replace(" ", "_") + "_risk_band_migration.png"
    plt.savefig(CHARTS_PATH / filename, dpi=300)
    plt.close()


def main():
    print("Reading train and test predictions...")

    if not TRAIN_PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Train predictions not found at {TRAIN_PREDICTIONS_PATH}. "
            "Please rerun scripts/02_train_models.py after adding train prediction export."
        )

    if not TEST_PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Test predictions with risk bands not found at {TEST_PREDICTIONS_PATH}. "
            "Please run scripts/03_model_validation.py first."
        )

    train_df = pd.read_csv(TRAIN_PREDICTIONS_PATH)
    test_df = pd.read_csv(TEST_PREDICTIONS_PATH)

    print(f"Train predictions shape: {train_df.shape}")
    print(f"Test predictions shape: {test_df.shape}")

    # ------------------------------------------------------------
    # PSI
    # ------------------------------------------------------------

    psi_value, psi_interpretation, psi_bins = calculate_psi(
        expected=train_df[PD_COL],
        actual=test_df[PD_COL],
        bins=10,
    )

    psi_summary = pd.DataFrame(
        [
            {
                "metric": "PD score PSI: train vs test",
                "psi": psi_value,
                "interpretation": psi_interpretation,
            }
        ]
    )

    psi_summary.to_csv(TABLES_PATH / "psi_summary.csv", index=False)
    psi_bins.to_csv(TABLES_PATH / "psi_bins_pd_score.csv", index=False)

    save_train_test_pd_distribution(train_df, test_df)

    # ------------------------------------------------------------
    # Threshold strategy simulation
    # ------------------------------------------------------------

    strategy_df = create_threshold_strategy_simulation(test_df)
    strategy_df.to_csv(TABLES_PATH / "threshold_strategy_simulation.csv", index=False)
    save_threshold_strategy_chart(strategy_df)

    # ------------------------------------------------------------
    # Risk band migration under stress
    # ------------------------------------------------------------

    adverse_migration = create_risk_band_migration(
        test_df,
        scenario_name="Adverse",
        pd_multiplier=1.25,
    )

    severe_migration = create_risk_band_migration(
        test_df,
        scenario_name="Severe Stress",
        pd_multiplier=1.50,
    )

    migration_all = pd.concat([adverse_migration, severe_migration], ignore_index=True)
    migration_all.to_csv(TABLES_PATH / "risk_band_migration_under_stress.csv", index=False)

    save_migration_heatmap(adverse_migration, "Adverse")
    save_migration_heatmap(severe_migration, "Severe Stress")

    print("Saved stability and strategy outputs:")
    print(TABLES_PATH / "psi_summary.csv")
    print(TABLES_PATH / "psi_bins_pd_score.csv")
    print(TABLES_PATH / "threshold_strategy_simulation.csv")
    print(TABLES_PATH / "risk_band_migration_under_stress.csv")
    print(CHARTS_PATH / "train_test_pd_distribution.png")
    print(CHARTS_PATH / "approval_threshold_simulation.png")
    print(CHARTS_PATH / "risk_capture_vs_exposure_retention.png")
    print(CHARTS_PATH / "adverse_risk_band_migration.png")
    print(CHARTS_PATH / "severe_stress_risk_band_migration.png")

    print("Stability and strategy analysis completed successfully.")
    print(f"PD score PSI: {psi_value:.4f} — {psi_interpretation}")


if __name__ == "__main__":
    main()