from pathlib import Path
import pandas as pd
import numpy as np


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"
SUMMARY_PATH = TABLES_PATH / "project_key_metrics.csv"

DATA_PREP_PATH = TABLES_PATH / "data_preparation_summary.csv"
MODEL_PERFORMANCE_PATH = TABLES_PATH / "model_performance.csv"
RISK_BAND_PATH = TABLES_PATH / "risk_band_summary.csv"
ECL_STAGE_PATH = TABLES_PATH / "ifrs9_stage_ecl_summary.csv"
ECL_RISK_BAND_PATH = TABLES_PATH / "ecl_by_risk_band.csv"
SCENARIO_PATH = TABLES_PATH / "scenario_ecl_summary.csv"


def get_metric(df, metric_name):
    """Extract value from data_preparation_summary.csv."""
    return df.loc[df["metric"] == metric_name, "value"].iloc[0]


def fmt_pct(x):
    return f"{x:.2%}"


def fmt_num(x):
    return f"{x:,.0f}"


def fmt_usd_mn(x):
    return f"USD {x / 1_000_000:,.1f}mn"


def fmt_usd_bn(x):
    return f"USD {x / 1_000_000_000:,.2f}bn"


def main():
    print("Generating project key metrics summary...")

    required_files = [
        DATA_PREP_PATH,
        MODEL_PERFORMANCE_PATH,
        RISK_BAND_PATH,
        ECL_STAGE_PATH,
        ECL_RISK_BAND_PATH,
        SCENARIO_PATH,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}. "
                "Please run scripts 01-05 before generating the summary."
            )

    data_prep = pd.read_csv(DATA_PREP_PATH)
    performance = pd.read_csv(MODEL_PERFORMANCE_PATH)
    risk_band = pd.read_csv(RISK_BAND_PATH)
    ecl_stage = pd.read_csv(ECL_STAGE_PATH)
    ecl_risk_band = pd.read_csv(ECL_RISK_BAND_PATH)
    scenario = pd.read_csv(SCENARIO_PATH)

    clean_rows = get_metric(data_prep, "clean_model_rows")
    default_rate = get_metric(data_prep, "default_rate")
    total_ead_clean = get_metric(data_prep, "total_ead_proxy")

    logit_test = performance[
        (performance["model"] == "Logistic Regression") & (performance["sample"] == "Test")
    ].iloc[0]

    xgb_test = performance[
        (performance["model"] == "XGBoost") & (performance["sample"] == "Test")
    ].iloc[0]

    very_high = risk_band[risk_band["risk_band"] == "Very High Risk"].iloc[0]
    low_risk = risk_band[risk_band["risk_band"] == "Low Risk"].iloc[0]

    stage_1 = ecl_stage[ecl_stage["ifrs9_stage_proxy"] == "Stage 1"].iloc[0]
    stage_2 = ecl_stage[ecl_stage["ifrs9_stage_proxy"] == "Stage 2"].iloc[0]
    stage_3 = ecl_stage[ecl_stage["ifrs9_stage_proxy"] == "Stage 3"].iloc[0]

    ecl_very_high = ecl_risk_band[ecl_risk_band["risk_band"] == "Very High Risk"].iloc[0]

    base = scenario[scenario["scenario"] == "Base"].iloc[0]
    severe = scenario[scenario["scenario"] == "Severe Stress"].iloc[0]

    metrics = [
        {
            "section": "Dataset",
            "metric": "Clean modeling observations",
            "value": fmt_num(clean_rows),
            "plain_value": clean_rows,
        },
        {
            "section": "Dataset",
            "metric": "Observed default rate",
            "value": fmt_pct(default_rate),
            "plain_value": default_rate,
        },
        {
            "section": "Dataset",
            "metric": "Total EAD proxy in clean data",
            "value": fmt_usd_bn(total_ead_clean),
            "plain_value": total_ead_clean,
        },
        {
            "section": "Model performance",
            "metric": "Logistic Regression test AUC",
            "value": f"{logit_test['auc']:.3f}",
            "plain_value": logit_test["auc"],
        },
        {
            "section": "Model performance",
            "metric": "Logistic Regression test Gini",
            "value": f"{logit_test['gini']:.3f}",
            "plain_value": logit_test["gini"],
        },
        {
            "section": "Model performance",
            "metric": "XGBoost challenger test AUC",
            "value": f"{xgb_test['auc']:.3f}",
            "plain_value": xgb_test["auc"],
        },
        {
            "section": "Model performance",
            "metric": "XGBoost challenger test Gini",
            "value": f"{xgb_test['gini']:.3f}",
            "plain_value": xgb_test["gini"],
        },
        {
            "section": "Risk segmentation",
            "metric": "Low Risk actual default rate",
            "value": fmt_pct(low_risk["actual_default_rate"]),
            "plain_value": low_risk["actual_default_rate"],
        },
        {
            "section": "Risk segmentation",
            "metric": "Very High Risk actual default rate",
            "value": fmt_pct(very_high["actual_default_rate"]),
            "plain_value": very_high["actual_default_rate"],
        },
        {
            "section": "Risk segmentation",
            "metric": "Very High Risk exposure share",
            "value": fmt_pct(very_high["exposure_share"]),
            "plain_value": very_high["exposure_share"],
        },
        {
            "section": "Risk segmentation",
            "metric": "Very High Risk default share",
            "value": fmt_pct(very_high["default_share"]),
            "plain_value": very_high["default_share"],
        },
        {
            "section": "IFRS 9-style ECL",
            "metric": "Stage 1 exposure share",
            "value": fmt_pct(stage_1["exposure_share"]),
            "plain_value": stage_1["exposure_share"],
        },
        {
            "section": "IFRS 9-style ECL",
            "metric": "Stage 1 ECL share",
            "value": fmt_pct(stage_1["ecl_share"]),
            "plain_value": stage_1["ecl_share"],
        },
        {
            "section": "IFRS 9-style ECL",
            "metric": "Stage 2 + Stage 3 ECL share",
            "value": fmt_pct(stage_2["ecl_share"] + stage_3["ecl_share"]),
            "plain_value": stage_2["ecl_share"] + stage_3["ecl_share"],
        },
        {
            "section": "IFRS 9-style ECL",
            "metric": "Very High Risk ECL share",
            "value": fmt_pct(ecl_very_high["ecl_share"]),
            "plain_value": ecl_very_high["ecl_share"],
        },
        {
            "section": "IFRS 9-style ECL",
            "metric": "Base scenario total ECL",
            "value": fmt_usd_bn(base["total_ecl"]),
            "plain_value": base["total_ecl"],
        },
        {
            "section": "Stress testing",
            "metric": "Severe Stress total ECL",
            "value": fmt_usd_bn(severe["total_ecl"]),
            "plain_value": severe["total_ecl"],
        },
        {
            "section": "Stress testing",
            "metric": "Severe Stress ECL increase vs base",
            "value": fmt_pct(severe["ecl_increase_pct_vs_base"]),
            "plain_value": severe["ecl_increase_pct_vs_base"],
        },
    ]

    summary = pd.DataFrame(metrics)
    summary.to_csv(SUMMARY_PATH, index=False)

    print("Project key metrics summary saved to:")
    print(SUMMARY_PATH)
    print(summary[["section", "metric", "value"]])
    print("Project summary generation completed successfully.")


if __name__ == "__main__":
    main()