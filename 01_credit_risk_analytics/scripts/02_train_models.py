from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from xgboost import XGBClassifier


warnings.filterwarnings("ignore")


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "clean" / "lendingclub_clean_model_data.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "test_predictions.csv"
TRAIN_PREDICTIONS_PATH = PROJECT_ROOT / "data" / "interim" / "train_predictions.csv"

TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"
MODELS_PATH = PROJECT_ROOT / "outputs" / "models"

TABLES_PATH.mkdir(parents=True, exist_ok=True)
MODELS_PATH.mkdir(parents=True, exist_ok=True)
PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Modeling configuration
# ------------------------------------------------------------

TARGET = "default_flag"

ID_COLUMNS = [
    "id",
    "issue_date",
    "loan_status",
]

EAD_COLUMN = "ead_proxy"


NUMERIC_FEATURES = [
    "loan_amnt",
    "funded_amnt",
    "term_months",
    "int_rate",
    "installment",
    "emp_length_years",
    "annual_inc",
    "dti",
    "delinq_2yrs",
    "credit_history_months",
    "fico_avg",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
    "mort_acc",
    "pub_rec_bankruptcies",
]


CATEGORICAL_FEATURES = [
    "grade",
    "sub_grade",
    "home_ownership",
    "verification_status",
    "purpose",
]


FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


RANDOM_STATE = 42
TEST_SIZE = 0.30


def gini_from_auc(auc: float) -> float:
    """Convert AUC to Gini coefficient."""
    return 2 * auc - 1


def evaluate_model(y_true, y_proba, threshold=0.5):
    """
    Evaluate binary classifier using probability outputs.

    threshold = probability cutoff used to convert predicted PD into 0/1 class.
    """
    y_pred = (y_proba >= threshold).astype(int)

    auc = roc_auc_score(y_true, y_proba)
    gini = gini_from_auc(auc)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "auc": auc,
        "gini": gini,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "threshold": threshold,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
    }


def main():
    print("Reading clean LendingClub model data...")
    print(f"Clean data path: {CLEAN_DATA_PATH}")

    if not CLEAN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Clean data not found at {CLEAN_DATA_PATH}. "
            "Please run scripts/01_prepare_data.py first."
        )

    df = pd.read_csv(CLEAN_DATA_PATH, low_memory=False)

    print(f"Clean data shape: {df.shape}")
    print(f"Default rate: {df[TARGET].mean():.4f}")

    # Keep only required columns to reduce memory use
    model_cols = ID_COLUMNS + [TARGET, EAD_COLUMN] + FEATURES
    df = df[model_cols].copy()

    X = df[FEATURES]
    y = df[TARGET].astype(int)

    # Stratify preserves default/non-default ratio in train and test samples
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X,
        y,
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"Train shape: {X_train.shape}")
    print(f"Test shape: {X_test.shape}")
    print(f"Train default rate: {y_train.mean():.4f}")
    print(f"Test default rate: {y_test.mean():.4f}")

    # ------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    # ------------------------------------------------------------
    # Logistic Regression PD model
    # ------------------------------------------------------------

    print("Training logistic regression PD model...")

    logistic_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    solver="lbfgs",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    logistic_model.fit(X_train, y_train)

    logit_train_pd = logistic_model.predict_proba(X_train)[:, 1]
    logit_test_pd = logistic_model.predict_proba(X_test)[:, 1]

    logit_train_perf = evaluate_model(y_train, logit_train_pd)
    logit_test_perf = evaluate_model(y_test, logit_test_pd)

    # ------------------------------------------------------------
    # XGBoost challenger model
    # ------------------------------------------------------------

    print("Training XGBoost challenger model...")

    xgb_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=250,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.80,
                    colsample_bytree=0.80,
                    objective="binary:logistic",
                    eval_metric="auc",
                    tree_method="hist",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    xgb_model.fit(X_train, y_train)

    xgb_train_pd = xgb_model.predict_proba(X_train)[:, 1]
    xgb_test_pd = xgb_model.predict_proba(X_test)[:, 1]

    xgb_train_perf = evaluate_model(y_train, xgb_train_pd)
    xgb_test_perf = evaluate_model(y_test, xgb_test_pd)

    # ------------------------------------------------------------
    # Save performance table
    # ------------------------------------------------------------

    performance_rows = []

    for model_name, sample_name, metrics in [
        ("Logistic Regression", "Train", logit_train_perf),
        ("Logistic Regression", "Test", logit_test_perf),
        ("XGBoost", "Train", xgb_train_perf),
        ("XGBoost", "Test", xgb_test_perf),
    ]:
        row = {
            "model": model_name,
            "sample": sample_name,
        }
        row.update(metrics)
        performance_rows.append(row)

    performance = pd.DataFrame(performance_rows)
    performance.to_csv(TABLES_PATH / "model_performance.csv", index=False)

    print("Model performance:")
    print(performance[["model", "sample", "auc", "gini", "precision", "recall", "f1"]])

    # ------------------------------------------------------------
    # Save test predictions for validation, risk bands and ECL
    # ------------------------------------------------------------

    train_predictions = df_train[ID_COLUMNS + [TARGET, EAD_COLUMN]].copy()
    train_predictions["pd_logistic"] = logit_train_pd
    train_predictions["pd_xgboost"] = xgb_train_pd
    train_predictions["pd_primary"] = train_predictions["pd_logistic"]
    train_predictions["sample"] = "Train"

    test_predictions = df_test[ID_COLUMNS + [TARGET, EAD_COLUMN]].copy()
    test_predictions["pd_logistic"] = logit_test_pd
    test_predictions["pd_xgboost"] = xgb_test_pd
    test_predictions["pd_primary"] = test_predictions["pd_logistic"]
    test_predictions["sample"] = "Test"

    train_predictions.to_csv(TRAIN_PREDICTIONS_PATH, index=False)
    test_predictions.to_csv(PREDICTIONS_PATH, index=False)

    # ------------------------------------------------------------
    # Save models
    # ------------------------------------------------------------

    joblib.dump(logistic_model, MODELS_PATH / "logistic_pd_model.joblib")
    joblib.dump(xgb_model, MODELS_PATH / "xgboost_pd_model.joblib")

    print("Saved outputs:")
    print(TABLES_PATH / "model_performance.csv")
    print(PREDICTIONS_PATH)
    print(TRAIN_PREDICTIONS_PATH)
    print(MODELS_PATH / "logistic_pd_model.joblib")
    print(MODELS_PATH / "xgboost_pd_model.joblib")
    print("Model training completed successfully.")


if __name__ == "__main__":
    main()