from pathlib import Path
import pandas as pd
import numpy as np


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "accepted_2007_to_2018Q4.csv.gz"
CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "clean" / "lendingclub_clean_model_data.csv"
TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"

TABLES_PATH.mkdir(parents=True, exist_ok=True)
CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Columns selected for an application-time PD model
# ------------------------------------------------------------

SELECTED_COLUMNS = [
    "id",
    "issue_d",
    "loan_amnt",
    "funded_amnt",
    "term",
    "int_rate",
    "installment",
    "grade",
    "sub_grade",
    "emp_length",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "purpose",
    "dti",
    "delinq_2yrs",
    "earliest_cr_line",
    "fico_range_low",
    "fico_range_high",
    "inq_last_6mths",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "total_acc",
    "mort_acc",
    "pub_rec_bankruptcies",
    "loan_status",
]


GOOD_STATUSES = [
    "Fully Paid",
    "Does not meet the credit policy. Status:Fully Paid",
]

BAD_STATUSES = [
    "Charged Off",
    "Default",
    "Does not meet the credit policy. Status:Charged Off",
    "Late (31-120 days)",
]


def clean_percentage_column(series: pd.Series) -> pd.Series:
    """Convert percentage strings such as '13.56%' to numeric values."""
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def clean_term(series: pd.Series) -> pd.Series:
    """Convert terms such as '36 months' to numeric 36."""
    return (
        series.astype(str)
        .str.replace(" months", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def clean_emp_length(series: pd.Series) -> pd.Series:
    """Convert employment length strings to numeric years."""
    cleaned = (
        series.astype(str)
        .str.replace(" years", "", regex=False)
        .str.replace(" year", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.replace("< 1", "0", regex=False)
        .str.strip()
    )
    cleaned = cleaned.replace({"nan": np.nan, "n/a": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def parse_month_year(series: pd.Series) -> pd.Series:
    """Parse LendingClub month-year strings such as 'Dec-2015'."""
    return pd.to_datetime(series, format="%b-%Y", errors="coerce")


def main():
    print("Reading LendingClub accepted loans data...")
    print(f"Raw data path: {RAW_DATA_PATH}")

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find raw file at: {RAW_DATA_PATH}\n"
            "Please check the exact filename in data/raw."
        )

    df = pd.read_csv(
        RAW_DATA_PATH,
        usecols=SELECTED_COLUMNS,
        low_memory=False,
    )

    print(f"Raw selected data shape: {df.shape}")

    # Save basic data audit outputs
    loan_status_dist = (
        df["loan_status"]
        .value_counts(dropna=False)
        .rename_axis("loan_status")
        .reset_index(name="count")
    )
    loan_status_dist["share"] = loan_status_dist["count"] / loan_status_dist["count"].sum()
    loan_status_dist.to_csv(TABLES_PATH / "loan_status_distribution_raw.csv", index=False)

    missing_summary = (
        df.isna()
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "column", 0: "missing_rate"})
    )
    missing_summary.to_csv(TABLES_PATH / "missing_values_raw.csv", index=False)

    # Keep only loans with observed final/default-like outcomes
    df = df[df["loan_status"].isin(GOOD_STATUSES + BAD_STATUSES)].copy()

    df["default_flag"] = np.where(df["loan_status"].isin(BAD_STATUSES), 1, 0)

    print(f"Modeling sample after status filter: {df.shape}")
    print("Default rate:", round(df["default_flag"].mean(), 4))

    # Basic cleaning
    df["int_rate"] = clean_percentage_column(df["int_rate"])
    df["revol_util"] = clean_percentage_column(df["revol_util"])
    df["term_months"] = clean_term(df["term"])
    df["emp_length_years"] = clean_emp_length(df["emp_length"])

    df["issue_date"] = parse_month_year(df["issue_d"])
    df["earliest_credit_date"] = parse_month_year(df["earliest_cr_line"])

    df["credit_history_months"] = (
        (df["issue_date"].dt.year - df["earliest_credit_date"].dt.year) * 12
        + (df["issue_date"].dt.month - df["earliest_credit_date"].dt.month)
    )

    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2

    # EAD proxy for illustrative ECL
    df["ead_proxy"] = df["funded_amnt"]

    # Keep final modeling columns
    final_columns = [
        "id",
        "issue_date",
        "loan_status",
        "default_flag",
        "loan_amnt",
        "funded_amnt",
        "ead_proxy",
        "term_months",
        "int_rate",
        "installment",
        "grade",
        "sub_grade",
        "emp_length_years",
        "home_ownership",
        "annual_inc",
        "verification_status",
        "purpose",
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

    df_model = df[final_columns].copy()

    # Remove observations with missing values in core fields
    core_fields = ["annual_inc", "dti", "fico_avg", "ead_proxy", "default_flag"]
    for col in core_fields:
        df_model = df_model[df_model[col].notna()]

    # Remove impossible or clearly problematic values
    df_model = df_model[df_model["annual_inc"] > 0]
    df_model = df_model[df_model["ead_proxy"] > 0]
    df_model = df_model[df_model["credit_history_months"].isna() | (df_model["credit_history_months"] >= 0)]

    # Save clean data
    df_model.to_csv(CLEAN_DATA_PATH, index=False)

    clean_status_dist = (
        df_model["loan_status"]
        .value_counts(dropna=False)
        .rename_axis("loan_status")
        .reset_index(name="count")
    )
    clean_status_dist["share"] = clean_status_dist["count"] / clean_status_dist["count"].sum()
    clean_status_dist.to_csv(TABLES_PATH / "loan_status_distribution_clean.csv", index=False)

    summary = pd.DataFrame(
        {
            "metric": [
                "raw_selected_rows_after_status_filter",
                "selected_columns",
                "clean_model_rows",
                "clean_model_columns",
                "default_rate",
                "total_ead_proxy",
            ],
            "value": [
                df.shape[0],
                len(SELECTED_COLUMNS),
                df_model.shape[0],
                df_model.shape[1],
                df_model["default_flag"].mean(),
                df_model["ead_proxy"].sum(),
            ],
        }
    )
    summary.to_csv(TABLES_PATH / "data_preparation_summary.csv", index=False)

    print("Clean model data saved to:")
    print(CLEAN_DATA_PATH)
    print(f"Clean model data shape: {df_model.shape}")
    print(f"Clean default rate: {df_model['default_flag'].mean():.4f}")
    print("Data preparation completed successfully.")


if __name__ == "__main__":
    main()