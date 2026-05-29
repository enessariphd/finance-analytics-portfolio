from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    auc,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
)


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "test_predictions.csv"

CHARTS_PATH = PROJECT_ROOT / "outputs" / "charts"
TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"

CHARTS_PATH.mkdir(parents=True, exist_ok=True)
TABLES_PATH.mkdir(parents=True, exist_ok=True)


TARGET = "default_flag"


def save_roc_curve(df: pd.DataFrame) -> None:
    """Save ROC curve for logistic regression and XGBoost models."""
    y_true = df[TARGET]

    plt.figure(figsize=(8, 6))

    for model_col, label in [
        ("pd_logistic", "Logistic Regression"),
        ("pd_xgboost", "XGBoost"),
    ]:
        fpr, tpr, _ = roc_curve(y_true, df[model_col])
        model_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f"{label} (AUC = {model_auc:.3f})")

    plt.plot([0, 1], [0, 1], linestyle="--", label="Random classifier")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve: PD Model Discriminatory Power")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "roc_curve.png", dpi=300)
    plt.close()


def save_confusion_matrix(df: pd.DataFrame, pd_col: str, model_name: str, threshold: float = 0.5) -> None:
    """Save confusion matrix at a selected PD threshold."""
    y_true = df[TARGET]
    y_pred = (df[pd_col] >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Non-default", "Default"])

    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, values_format=",d")
    ax.set_title(f"Confusion Matrix: {model_name} at {threshold:.2f} Threshold")
    plt.tight_layout()

    safe_name = model_name.lower().replace(" ", "_")
    plt.savefig(CHARTS_PATH / f"confusion_matrix_{safe_name}.png", dpi=300)
    plt.close()


def save_pd_distribution(df: pd.DataFrame) -> None:
    """Save predicted PD distribution chart for the primary model."""
    plt.figure(figsize=(8, 6))
    plt.hist(df["pd_primary"], bins=50)
    plt.xlabel("Predicted Probability of Default")
    plt.ylabel("Number of Loans")
    plt.title("Distribution of Predicted PDs: Primary Logistic Regression Model")
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "pd_distribution.png", dpi=300)
    plt.close()


def create_decile_validation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create actual-vs-predicted default validation table by PD decile.

    Decile 1 = lowest predicted PD.
    Decile 10 = highest predicted PD.
    """
    df = df.copy()

    df["pd_decile"] = pd.qcut(
        df["pd_primary"],
        q=10,
        labels=False,
        duplicates="drop",
    ) + 1

    decile = (
        df.groupby("pd_decile")
        .agg(
            loans=("default_flag", "size"),
            actual_defaults=("default_flag", "sum"),
            actual_default_rate=("default_flag", "mean"),
            avg_predicted_pd=("pd_primary", "mean"),
            exposure=("ead_proxy", "sum"),
        )
        .reset_index()
    )

    decile["exposure_share"] = decile["exposure"] / decile["exposure"].sum()

    return decile


def save_decile_charts(decile: pd.DataFrame) -> None:
    """Save calibration and actual vs predicted default rate charts."""
    # Actual vs predicted default by decile
    plt.figure(figsize=(9, 6))
    plt.plot(decile["pd_decile"], decile["actual_default_rate"], marker="o", label="Actual default rate")
    plt.plot(decile["pd_decile"], decile["avg_predicted_pd"], marker="o", label="Average predicted PD")
    plt.xlabel("PD Decile: 1 = Lowest Risk, 10 = Highest Risk")
    plt.ylabel("Default Rate / Predicted PD")
    plt.title("Actual vs Predicted Default Rate by PD Decile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "actual_vs_predicted_default_by_decile.png", dpi=300)
    plt.close()

    # Calibration scatter
    plt.figure(figsize=(7, 6))
    plt.scatter(decile["avg_predicted_pd"], decile["actual_default_rate"])
    max_value = max(decile["avg_predicted_pd"].max(), decile["actual_default_rate"].max())
    plt.plot([0, max_value], [0, max_value], linestyle="--")
    plt.xlabel("Average Predicted PD")
    plt.ylabel("Actual Default Rate")
    plt.title("Calibration Check by PD Decile")
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "calibration_by_decile.png", dpi=300)
    plt.close()


def create_risk_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create four PD-based risk bands.

    Bands are quantile-based for portfolio segmentation:
    - Low Risk
    - Medium Risk
    - High Risk
    - Very High Risk
    """
    df = df.copy()

    df["risk_band"] = pd.qcut(
        df["pd_primary"],
        q=4,
        labels=["Low Risk", "Medium Risk", "High Risk", "Very High Risk"],
        duplicates="drop",
    )

    risk_summary = (
        df.groupby("risk_band", observed=True)
        .agg(
            loans=("default_flag", "size"),
            exposure=("ead_proxy", "sum"),
            avg_pd=("pd_primary", "mean"),
            actual_default_rate=("default_flag", "mean"),
            defaults=("default_flag", "sum"),
        )
        .reset_index()
    )

    risk_summary["exposure_share"] = risk_summary["exposure"] / risk_summary["exposure"].sum()
    risk_summary["default_share"] = risk_summary["defaults"] / risk_summary["defaults"].sum()

    return df, risk_summary


def save_risk_band_charts(risk_summary: pd.DataFrame) -> None:
    """Save exposure and default rate charts by risk band."""
    risk_order = ["Low Risk", "Medium Risk", "High Risk", "Very High Risk"]
    risk_summary = risk_summary.copy()
    risk_summary["risk_band"] = pd.Categorical(
        risk_summary["risk_band"],
        categories=risk_order,
        ordered=True,
    )
    risk_summary = risk_summary.sort_values("risk_band")

    # Exposure distribution by risk band
    plt.figure(figsize=(8, 6))
    plt.bar(risk_summary["risk_band"].astype(str), risk_summary["exposure"] / 1_000_000_000)
    plt.xlabel("Risk Band")
    plt.ylabel("Exposure / EAD Proxy, USD billion")
    plt.title("Portfolio Exposure Distribution by Risk Band")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "exposure_by_risk_band.png", dpi=300)
    plt.close()

    # Actual default rate by risk band
    plt.figure(figsize=(8, 6))
    plt.bar(risk_summary["risk_band"].astype(str), risk_summary["actual_default_rate"])
    plt.xlabel("Risk Band")
    plt.ylabel("Actual Default Rate")
    plt.title("Actual Default Rate by Risk Band")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "default_rate_by_risk_band.png", dpi=300)
    plt.close()

    # Average PD by risk band
    plt.figure(figsize=(8, 6))
    plt.bar(risk_summary["risk_band"].astype(str), risk_summary["avg_pd"])
    plt.xlabel("Risk Band")
    plt.ylabel("Average Predicted PD")
    plt.title("Average Predicted PD by Risk Band")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "average_pd_by_risk_band.png", dpi=300)
    plt.close()


def main():
    print("Reading test predictions...")
    print(f"Predictions path: {PREDICTIONS_PATH}")

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Predictions file not found at {PREDICTIONS_PATH}. "
            "Please run scripts/02_train_models.py first."
        )

    df = pd.read_csv(PREDICTIONS_PATH)

    print(f"Predictions shape: {df.shape}")
    print(f"Observed test default rate: {df[TARGET].mean():.4f}")
    print(f"Average logistic PD: {df['pd_logistic'].mean():.4f}")
    print(f"Average XGBoost PD: {df['pd_xgboost'].mean():.4f}")

    save_roc_curve(df)
    save_confusion_matrix(df, "pd_logistic", "Logistic Regression", threshold=0.5)
    save_confusion_matrix(df, "pd_xgboost", "XGBoost", threshold=0.5)
    save_pd_distribution(df)

    decile = create_decile_validation(df)
    decile.to_csv(TABLES_PATH / "validation_by_decile.csv", index=False)
    save_decile_charts(decile)

    df_with_bands, risk_summary = create_risk_bands(df)
    risk_summary.to_csv(TABLES_PATH / "risk_band_summary.csv", index=False)
    df_with_bands.to_csv(PROJECT_ROOT / "data" / "interim" / "test_predictions_with_risk_bands.csv", index=False)

    save_risk_band_charts(risk_summary)

    print("Saved validation tables:")
    print(TABLES_PATH / "validation_by_decile.csv")
    print(TABLES_PATH / "risk_band_summary.csv")

    print("Saved validation charts to:")
    print(CHARTS_PATH)

    print("Model validation completed successfully.")


if __name__ == "__main__":
    main()