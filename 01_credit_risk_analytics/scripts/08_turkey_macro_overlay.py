from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOANS_PATH = PROJECT_ROOT / "data" / "raw" / "loans.xls"
NPL_PATH = PROJECT_ROOT / "data" / "raw" / "npl.xls"

TABLES_PATH = PROJECT_ROOT / "outputs" / "tables"
CHARTS_PATH = PROJECT_ROOT / "outputs" / "charts"

TABLES_PATH.mkdir(parents=True, exist_ok=True)
CHARTS_PATH.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Selected dates for compact Turkey macro-sector overlay
# ------------------------------------------------------------

SELECTED_DATES = [
    "2024-03-29",
    "2024-06-28",
    "2024-09-27",
    "2024-12-27",
    "2025-03-28",
    "2025-06-27",
    "2025-09-26",
    "2025-12-26",
    "2026-03-27",
    "2026-04-30",
    "2026-05-08",
]


# ------------------------------------------------------------
# Macro values manually mapped from TCMB public pages
# CPI YoY is matched to the relevant month.
# Policy rate is the 1-week repo rate effective as of the BDDK date.
# ------------------------------------------------------------

MACRO_OVERLAY = {
    "2024-03-29": {"policy_rate": 50.00, "cpi_yoy": 68.50},
    "2024-06-28": {"policy_rate": 50.00, "cpi_yoy": 71.60},
    "2024-09-27": {"policy_rate": 50.00, "cpi_yoy": 49.38},
    "2024-12-27": {"policy_rate": 47.50, "cpi_yoy": 44.38},
    "2025-03-28": {"policy_rate": 42.50, "cpi_yoy": 38.10},
    "2025-06-27": {"policy_rate": 46.00, "cpi_yoy": 35.05},
    "2025-09-26": {"policy_rate": 40.50, "cpi_yoy": 33.29},
    "2025-12-26": {"policy_rate": 38.00, "cpi_yoy": 30.89},
    "2026-03-27": {"policy_rate": 37.00, "cpi_yoy": 30.87},
    "2026-04-30": {"policy_rate": 37.00, "cpi_yoy": 32.37},
    "2026-05-08": {"policy_rate": 37.00, "cpi_yoy": 32.37},  # latest available CPI: 04-2026
}


def parse_bddk_date(value):
    """
    Parse BDDK date values exported from Excel/HTML.

    The HTML-exported .xls files may convert dates like:
    - '8.05.2026' into '8052026'
    - '30.04.2026' into '30042026'

    This function handles both cases.
    """
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    # If already includes separators, parse directly
    if "." in text:
        return pd.to_datetime(text, format="%d.%m.%Y", errors="coerce")

    # Remove non-digits
    digits = re.sub(r"\D", "", text)

    if len(digits) < 7:
        return pd.NaT

    year = digits[-4:]
    month = digits[-6:-4]
    day = digits[:-6]

    if len(day) == 1:
        day = "0" + day

    date_str = f"{year}-{month}-{day}"
    return pd.to_datetime(date_str, errors="coerce")


def read_bddk_html_xls(path):
    """
    Read BDDK HTML-exported .xls file.

    The files are HTML tables saved with .xls extension.
    We use Turkish number formatting:
    - thousands separator: .
    - decimal separator: ,
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_html(path, encoding="utf-8", thousands=".", decimal=",")[0]

    return df


def prepare_loans_data(path):
    """
    Prepare BDDK loan denominator data.

    Uses TOPLAM columns:
    - total loans
    - consumer loans and consumer credit cards
    - commercial and other loans
    - SME loans
    """
    df = read_bddk_html_xls(path)

    # Data rows begin after the first three header rows
    data = df.iloc[3:].copy()

    output = pd.DataFrame(
        {
            "date": data.iloc[:, 0].apply(parse_bddk_date),
            "total_loans_total": pd.to_numeric(data.iloc[:, 3], errors="coerce"),
            "consumer_loans_total": pd.to_numeric(data.iloc[:, 6], errors="coerce"),
            "commercial_loans_total": pd.to_numeric(data.iloc[:, 9], errors="coerce"),
            "sme_loans_total": pd.to_numeric(data.iloc[:, 12], errors="coerce"),
        }
    )

    output = output.dropna(subset=["date"])
    output["date"] = output["date"].dt.strftime("%Y-%m-%d")

    return output


def prepare_npl_data(path):
    """
    Prepare BDDK NPL numerator and allowance data.

    Uses TOPLAM columns:
    - total NPL
    - consumer NPL
    - commercial NPL
    - SME NPL
    - NPL allowance / special provisions
    """
    df = read_bddk_html_xls(path)

    data = df.iloc[3:].copy()

    output = pd.DataFrame(
        {
            "date": data.iloc[:, 0].apply(parse_bddk_date),
            "npl_total": pd.to_numeric(data.iloc[:, 3], errors="coerce"),
            "consumer_npl_total": pd.to_numeric(data.iloc[:, 6], errors="coerce"),
            "commercial_npl_total": pd.to_numeric(data.iloc[:, 9], errors="coerce"),
            "sme_npl_total": pd.to_numeric(data.iloc[:, 12], errors="coerce"),
            "npl_allowance_total": pd.to_numeric(data.iloc[:, 15], errors="coerce"),
        }
    )

    output = output.dropna(subset=["date"])
    output["date"] = output["date"].dt.strftime("%Y-%m-%d")

    return output


def add_macro_overlay(df):
    """Add manually mapped TCMB policy rate and CPI YoY."""
    macro = (
        pd.DataFrame.from_dict(MACRO_OVERLAY, orient="index")
        .reset_index()
        .rename(columns={"index": "date"})
    )

    return df.merge(macro, on="date", how="left")


def calculate_ratios(df):
    """Calculate NPL and coverage ratios."""
    df = df.copy()

    df["total_npl_ratio"] = df["npl_total"] / df["total_loans_total"]
    df["consumer_npl_ratio"] = df["consumer_npl_total"] / df["consumer_loans_total"]
    df["commercial_npl_ratio"] = df["commercial_npl_total"] / df["commercial_loans_total"]
    df["sme_npl_ratio"] = df["sme_npl_total"] / df["sme_loans_total"]
    df["coverage_ratio"] = df["npl_allowance_total"] / df["npl_total"]

    df["total_loan_growth_since_start"] = (
        df["total_loans_total"] / df["total_loans_total"].iloc[0] - 1
    )

    df["npl_growth_since_start"] = (
        df["npl_total"] / df["npl_total"].iloc[0] - 1
    )

    return df


def save_turkey_overlay_charts(df):
    """Save Turkey banking-sector overlay charts."""

    # Total NPL ratio and coverage ratio
    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["total_npl_ratio"], marker="o", label="Total NPL ratio")
    plt.plot(df["date"], df["coverage_ratio"], marker="o", label="Coverage ratio")
    plt.xlabel("Date")
    plt.ylabel("Ratio")
    plt.title("Turkey Banking Sector: NPL Ratio and Coverage Ratio")
    plt.xticks(rotation=35, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "turkey_npl_coverage_overlay.png", dpi=300)
    plt.close()

    # Segment NPL ratios
    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["consumer_npl_ratio"], marker="o", label="Consumer")
    plt.plot(df["date"], df["commercial_npl_ratio"], marker="o", label="Commercial")
    plt.plot(df["date"], df["sme_npl_ratio"], marker="o", label="SME")
    plt.xlabel("Date")
    plt.ylabel("NPL Ratio")
    plt.title("Turkey Banking Sector: NPL Ratio by Segment")
    plt.xticks(rotation=35, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "turkey_segment_npl_ratios.png", dpi=300)
    plt.close()

    # Loan and NPL growth since start
    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["total_loan_growth_since_start"], marker="o", label="Total loan growth")
    plt.plot(df["date"], df["npl_growth_since_start"], marker="o", label="NPL growth")
    plt.xlabel("Date")
    plt.ylabel("Growth since first selected date")
    plt.title("Turkey Banking Sector: Loan Growth vs NPL Growth")
    plt.xticks(rotation=35, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "turkey_loan_growth_vs_npl_growth.png", dpi=300)
    plt.close()

    # Macro backdrop
    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["policy_rate"] / 100, marker="o", label="Policy rate")
    plt.plot(df["date"], df["cpi_yoy"] / 100, marker="o", label="CPI YoY")
    plt.xlabel("Date")
    plt.ylabel("Rate")
    plt.title("Turkey Macro Backdrop: Policy Rate and Inflation")
    plt.xticks(rotation=35, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_PATH / "turkey_policy_rate_inflation_overlay.png", dpi=300)
    plt.close()


def main():
    print("Reading BDDK loans and NPL data...")

    loans = prepare_loans_data(LOANS_PATH)
    npl = prepare_npl_data(NPL_PATH)

    print(f"Loans data shape: {loans.shape}")
    print(f"NPL data shape: {npl.shape}")

    df = loans.merge(npl, on="date", how="inner")

    df = df[df["date"].isin(SELECTED_DATES)].copy()
    df = df.sort_values("date").reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "No selected dates found after merging loans and NPL data. "
            "Please check date formats and selected dates."
        )

    df = add_macro_overlay(df)
    df = calculate_ratios(df)

    output_path = TABLES_PATH / "turkey_macro_sector_overlay.csv"
    df.to_csv(output_path, index=False)

    latest = df.iloc[-1]
    summary = pd.DataFrame(
        [
            {
                "metric": "Latest selected date",
                "value": latest["date"],
            },
            {
                "metric": "Latest total NPL ratio",
                "value": f"{latest['total_npl_ratio']:.2%}",
            },
            {
                "metric": "Latest consumer NPL ratio",
                "value": f"{latest['consumer_npl_ratio']:.2%}",
            },
            {
                "metric": "Latest commercial NPL ratio",
                "value": f"{latest['commercial_npl_ratio']:.2%}",
            },
            {
                "metric": "Latest SME NPL ratio",
                "value": f"{latest['sme_npl_ratio']:.2%}",
            },
            {
                "metric": "Latest coverage ratio",
                "value": f"{latest['coverage_ratio']:.2%}",
            },
            {
                "metric": "Latest policy rate",
                "value": f"{latest['policy_rate']:.2f}%",
            },
            {
                "metric": "Latest CPI YoY",
                "value": f"{latest['cpi_yoy']:.2f}%",
            },
            {
                "metric": "Total loan growth since first selected date",
                "value": f"{latest['total_loan_growth_since_start']:.2%}",
            },
            {
                "metric": "NPL growth since first selected date",
                "value": f"{latest['npl_growth_since_start']:.2%}",
            },
        ]
    )

    summary_path = TABLES_PATH / "turkey_macro_sector_overlay_summary.csv"
    summary.to_csv(summary_path, index=False)

    save_turkey_overlay_charts(df)

    print("Turkey macro-sector overlay saved to:")
    print(output_path)
    print(summary_path)

    print("Saved charts:")
    print(CHARTS_PATH / "turkey_npl_coverage_overlay.png")
    print(CHARTS_PATH / "turkey_segment_npl_ratios.png")
    print(CHARTS_PATH / "turkey_loan_growth_vs_npl_growth.png")
    print(CHARTS_PATH / "turkey_policy_rate_inflation_overlay.png")

    print("Turkey macro-sector overlay completed successfully.")
    print(summary)


if __name__ == "__main__":
    main()