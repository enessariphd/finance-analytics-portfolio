from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOGISTIC_MODEL_PATH = PROJECT_ROOT / "outputs" / "models" / "logistic_pd_model.joblib"
XGBOOST_MODEL_PATH = PROJECT_ROOT / "outputs" / "models" / "xgboost_pd_model.joblib"

TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"
CHARTS_PATH = PROJECT_ROOT / "outputs" / "charts"

TABLES_PATH.mkdir(parents=True, exist_ok=True)
CHARTS_PATH.mkdir(parents=True, exist_ok=True)


TOP_N = 20


def get_feature_names_from_pipeline(model_pipeline):
    """
    Extract transformed feature names from the ColumnTransformer inside the model pipeline.
    """
    preprocessor = model_pipeline.named_steps["preprocessor"]

    numeric_features = preprocessor.transformers_[0][2]

    categorical_pipeline = preprocessor.named_transformers_["cat"]
    onehot = categorical_pipeline.named_steps["onehot"]
    categorical_features = preprocessor.transformers_[1][2]

    categorical_feature_names = onehot.get_feature_names_out(categorical_features)

    feature_names = list(numeric_features) + list(categorical_feature_names)

    return np.array(feature_names)


def extract_logistic_coefficients(logistic_model):
    """
    Extract logistic regression coefficients after preprocessing.

    Positive coefficient = associated with higher predicted default probability.
    Negative coefficient = associated with lower predicted default probability.
    """
    feature_names = get_feature_names_from_pipeline(logistic_model)
    classifier = logistic_model.named_steps["classifier"]

    coefficients = classifier.coef_[0]

    coef_df = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "abs_coefficient": np.abs(coefficients),
        }
    )

    coef_df = coef_df.sort_values("abs_coefficient", ascending=False)

    return coef_df


def extract_xgboost_importance(xgb_model):
    """
    Extract XGBoost feature importance after preprocessing.

    Importance type is the default importance score from XGBoost sklearn wrapper.
    """
    feature_names = get_feature_names_from_pipeline(xgb_model)
    classifier = xgb_model.named_steps["classifier"]

    importance = classifier.feature_importances_

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importance,
        }
    )

    importance_df = importance_df.sort_values("importance", ascending=False)

    return importance_df


def save_logistic_coefficient_chart(coef_df):
    """
    Save chart of top positive and negative logistic regression coefficients.

    This shows which variables are most associated with higher or lower PD.
    """
    top_positive = coef_df.sort_values("coefficient", ascending=False).head(10)
    top_negative = coef_df.sort_values("coefficient", ascending=True).head(10)

    plot_df = pd.concat([top_negative, top_positive], axis=0)
    plot_df = plot_df.sort_values("coefficient")

    plt.figure(figsize=(10, 8))
    plt.barh(plot_df["feature"], plot_df["coefficient"])
    plt.xlabel("Logistic Regression Coefficient")
    plt.ylabel("Feature")
    plt.title("Top Logistic Regression Coefficients: Direction of PD Impact")
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "logistic_top_coefficients.png", dpi=300)
    plt.close()


def save_xgboost_importance_chart(importance_df):
    """Save chart of top XGBoost feature importances."""
    plot_df = importance_df.head(TOP_N).sort_values("importance", ascending=True)

    plt.figure(figsize=(10, 8))
    plt.barh(plot_df["feature"], plot_df["importance"])
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title("Top XGBoost Feature Importances")
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "xgboost_feature_importance.png", dpi=300)
    plt.close()


def create_interpretability_notes(coef_df, xgb_importance_df):
    """
    Create a compact text-like table with interpretability notes for the memo.
    """
    top_positive = coef_df.sort_values("coefficient", ascending=False).head(10)
    top_negative = coef_df.sort_values("coefficient", ascending=True).head(10)
    top_xgb = xgb_importance_df.head(10)

    notes = []

    notes.append(
        {
            "section": "Logistic positive coefficients",
            "interpretation": (
                "Features with positive coefficients are associated with higher predicted PD, "
                "holding other model inputs constant after preprocessing."
            ),
            "top_features": "; ".join(top_positive["feature"].astype(str).tolist()),
        }
    )

    notes.append(
        {
            "section": "Logistic negative coefficients",
            "interpretation": (
                "Features with negative coefficients are associated with lower predicted PD, "
                "holding other model inputs constant after preprocessing."
            ),
            "top_features": "; ".join(top_negative["feature"].astype(str).tolist()),
        }
    )

    notes.append(
        {
            "section": "XGBoost feature importance",
            "interpretation": (
                "XGBoost feature importance identifies the variables most used by the challenger model "
                "for non-linear risk separation."
            ),
            "top_features": "; ".join(top_xgb["feature"].astype(str).tolist()),
        }
    )

    return pd.DataFrame(notes)


def main():
    print("Loading trained models...")

    if not LOGISTIC_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Logistic model not found at {LOGISTIC_MODEL_PATH}. "
            "Please run scripts/02_train_models.py first."
        )

    if not XGBOOST_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"XGBoost model not found at {XGBOOST_MODEL_PATH}. "
            "Please run scripts/02_train_models.py first."
        )

    logistic_model = joblib.load(LOGISTIC_MODEL_PATH)
    xgb_model = joblib.load(XGBOOST_MODEL_PATH)

    print("Extracting logistic regression coefficients...")
    coef_df = extract_logistic_coefficients(logistic_model)

    print("Extracting XGBoost feature importance...")
    xgb_importance_df = extract_xgboost_importance(xgb_model)

    coef_df.to_csv(TABLES_PATH / "logistic_coefficients.csv", index=False)
    coef_df.head(TOP_N).to_csv(TABLES_PATH / "logistic_top_coefficients.csv", index=False)

    xgb_importance_df.to_csv(TABLES_PATH / "xgboost_feature_importance.csv", index=False)

    notes_df = create_interpretability_notes(coef_df, xgb_importance_df)
    notes_df.to_csv(TABLES_PATH / "model_interpretability_notes.csv", index=False)

    save_logistic_coefficient_chart(coef_df)
    save_xgboost_importance_chart(xgb_importance_df)

    print("Saved interpretability outputs:")
    print(TABLES_PATH / "logistic_coefficients.csv")
    print(TABLES_PATH / "logistic_top_coefficients.csv")
    print(TABLES_PATH / "xgboost_feature_importance.csv")
    print(TABLES_PATH / "model_interpretability_notes.csv")
    print(CHARTS_PATH / "logistic_top_coefficients.png")
    print(CHARTS_PATH / "xgboost_feature_importance.png")

    print("Model interpretability analysis completed successfully.")


if __name__ == "__main__":
    main()