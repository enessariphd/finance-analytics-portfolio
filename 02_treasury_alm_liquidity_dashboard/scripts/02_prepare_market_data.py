"""
Prepare market, funding, FX/gold, yield-curve and reserves data for the
Turkey Treasury / ALM & Liquidity Risk Dashboard.

Raw data files are expected to remain outside the GitHub repository.

Usage:
    python scripts/02_prepare_market_data.py --raw-dir "/path/to/local/data_raw"

Outputs:
    outputs/tables/market_weekly_core.csv
    outputs/tables/latest_market_dashboard_snapshot.csv
    outputs/charts/tl_funding_conditions.png
    outputs/charts/fx_gold_liquidity_watch.png
    outputs/charts/yield_curve_conditions.png
    outputs/charts/reserves_watch.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


warnings.filterwarnings("ignore", category=UserWarning)


def clean_numeric(series: pd.Series) -> pd.Series:
    """
    Convert Turkish/Investing-style numeric strings into floats.

    Handles both:
    - Turkish decimal comma values such as 39,99
    - thousands comma values such as 45,579.80
    """
    s = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("−", "-", regex=False)
        .str.strip()
        .replace({"nan": np.nan, "": np.nan, "-": np.nan})
    )

    def convert_one(x):
        if pd.isna(x):
            return np.nan

        x = str(x).strip()

        # Case 1: both comma and dot exist, assume comma is thousands separator.
        # Example: 45,579.80 -> 45579.80
        if "," in x and "." in x:
            return float(x.replace(",", ""))

        # Case 2: comma exists but dot does not.
        # If there are exactly two digits after comma, treat comma as decimal separator.
        # Example: 39,99 -> 39.99
        if "," in x and "." not in x:
            parts = x.split(",")
            if len(parts) == 2 and len(parts[1]) in {1, 2, 3}:
                return float(x.replace(",", "."))
            return float(x.replace(",", ""))

        return float(x)

    return s.apply(convert_one)


def parse_date(series: pd.Series) -> pd.Series:
    """Robust date parser for mixed date formats."""
    return pd.to_datetime(series, errors="coerce", dayfirst=False)


def read_investing_csv(path: Path, date_col: str = "Date", value_col: str = "Price") -> pd.DataFrame:
    """Read market CSV files with Date and Price columns."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in {path.name}. Columns: {df.columns.tolist()}")
    if value_col not in df.columns:
        raise ValueError(f"Value column '{value_col}' not found in {path.name}. Columns: {df.columns.tolist()}")

    out = df[[date_col, value_col]].copy()
    out.columns = ["date", "value"]
    out["date"] = parse_date(out["date"])
    out["value"] = clean_numeric(out["value"])
    out = out.dropna(subset=["date", "value"]).sort_values("date")
    return out


def read_tlref_csv(path: Path) -> pd.DataFrame:
    """Read BIST TLREF historical data."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    # Turkish Investing export usually has Tarih and Şimdi.
    date_col = "Tarih" if "Tarih" in df.columns else df.columns[0]
    value_col = "Şimdi" if "Şimdi" in df.columns else df.columns[1]

    out = df[[date_col, value_col]].copy()
    out.columns = ["date", "tlref_pct"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce", dayfirst=True)
    out["tlref_pct"] = clean_numeric(out["tlref_pct"])
    out = out.dropna(subset=["date", "tlref_pct"]).sort_values("date")
    return out


def read_evds_xlsx(path: Path) -> pd.DataFrame:
    """Read TCMB/EVDS xlsx file."""
    df = pd.read_excel(path, sheet_name="EVDS")
    df.columns = [str(c).strip() for c in df.columns]
    if "Date" not in df.columns:
        # Some EVDS exports may use a Turkish date label or a corrupted first column.
        df = df.rename(columns={df.columns[0]: "Date"})
    df["date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
    return df.dropna(subset=["date"]).sort_values("date")


def to_weekly_last(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Convert daily/monthly data to Friday-ending weekly observations using last available value."""
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out = out.set_index(date_col).sort_index()
    weekly = out.resample("W-FRI").last().reset_index().rename(columns={date_col: "week_ending"})
    return weekly


def find_one(raw_dir: Path, *patterns: str) -> Path:
    """Find the first file matching one of several glob patterns."""
    for pattern in patterns:
        matches = sorted(raw_dir.rglob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No file found for patterns: {patterns}")


def build_market_weekly_core(raw_dir: Path) -> pd.DataFrame:
    # TLREF
    tlref_path = find_one(raw_dir, "*TLREF*csv", "*Referans Faiz*csv", "*Gecelik*csv")
    tlref = read_tlref_csv(tlref_path)
    tlref_w = to_weekly_last(tlref)

    # FX and gold
    usd_path = find_one(raw_dir, "*USD_TRY*csv")
    eur_path = find_one(raw_dir, "*EUR_TRY*csv")
    gold_path = find_one(raw_dir, "*GAU_TRY*csv")

    usd = read_investing_csv(usd_path).rename(columns={"value": "usdtry"})
    eur = read_investing_csv(eur_path).rename(columns={"value": "eurtry"})
    gold = read_investing_csv(gold_path).rename(columns={"value": "gram_gold_try"})

    usd_w = to_weekly_last(usd)
    eur_w = to_weekly_last(eur)
    gold_w = to_weekly_last(gold)

    # Yields
    y2_path = find_one(raw_dir, "*2-Year*csv")
    y5_path = find_one(raw_dir, "*5-Year*csv")
    y10_path = find_one(raw_dir, "*10-Year*csv")

    y2 = read_investing_csv(y2_path).rename(columns={"value": "yield_2y_pct"})
    y5 = read_investing_csv(y5_path).rename(columns={"value": "yield_5y_pct"})
    y10 = read_investing_csv(y10_path).rename(columns={"value": "yield_10y_pct"})

    y2_w = to_weekly_last(y2)
    y5_w = to_weekly_last(y5)
    y10_w = to_weekly_last(y10)

    # EVDS deposit / loan rates
    dep_path = find_one(raw_dir, "*Deposit_Rate*.xlsx")
    loan_path = find_one(raw_dir, "*Loan_Rate*.xlsx")
    reserves_path = find_one(raw_dir, "*Reserves*.xlsx")

    dep = read_evds_xlsx(dep_path)
    loan = read_evds_xlsx(loan_path)
    reserves = read_evds_xlsx(reserves_path)

    # Deposit proxy: average of TRY deposit columns where available.
    dep_cols = [c for c in dep.columns if c.startswith("TP_TRY_MT")]
    dep["deposit_rate_proxy_pct"] = dep[dep_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)

    # Loan proxy: average of TRY loan-rate columns where available.
    loan_cols = [c for c in loan.columns if c.startswith("TP_BKR_TRY")]
    loan["loan_rate_proxy_pct"] = loan[loan_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)

    dep_w = to_weekly_last(dep[["date", "deposit_rate_proxy_pct"]])
    loan_w = to_weekly_last(loan[["date", "loan_rate_proxy_pct"]])

    # Reserves: keep numeric EVDS columns and infer gold/fx/total labels if possible.
    reserve_numeric_cols = [c for c in reserves.columns if c not in {"Date", "date"}]
    for c in reserve_numeric_cols:
        reserves[c] = pd.to_numeric(reserves[c], errors="coerce")

    reserves_w = to_weekly_last(reserves[["date"] + reserve_numeric_cols])

    # Rename reserve columns conservatively.
    reserve_rename = {}
    if len(reserve_numeric_cols) >= 1:
        reserve_rename[reserve_numeric_cols[0]] = "gold_reserves_usd_mn"
    if len(reserve_numeric_cols) >= 2:
        reserve_rename[reserve_numeric_cols[1]] = "fx_reserves_usd_mn"
    if len(reserve_numeric_cols) >= 3:
        reserve_rename[reserve_numeric_cols[2]] = "total_reserves_usd_mn"
    reserves_w = reserves_w.rename(columns=reserve_rename)

    # Merge all weekly blocks.
    frames = [tlref_w, usd_w, eur_w, gold_w, y2_w, y5_w, y10_w, dep_w, loan_w, reserves_w]
    weekly = frames[0]
    for frame in frames[1:]:
        weekly = weekly.merge(frame, on="week_ending", how="outer")

    weekly = weekly.sort_values("week_ending")

    # Forward-fill slow-moving or missing weekly observations after merge.
    value_cols = [c for c in weekly.columns if c != "week_ending"]
    weekly[value_cols] = weekly[value_cols].ffill()

    # Policy rate is entered as a transparent public dashboard assumption.
    # The memo data-through date uses 37.0% as the policy anchor.
    weekly["policy_rate_pct"] = 37.0

    # Derived indicators.
    weekly["tlref_policy_spread_pp"] = weekly["tlref_pct"] - weekly["policy_rate_pct"]
    weekly["loan_deposit_spread_pp"] = weekly["loan_rate_proxy_pct"] - weekly["deposit_rate_proxy_pct"]
    weekly["curve_slope_10y_2y_pp"] = weekly["yield_10y_pct"] - weekly["yield_2y_pct"]
    weekly["curve_slope_5y_2y_pp"] = weekly["yield_5y_pct"] - weekly["yield_2y_pct"]

    for col, idx_col in [
        ("usdtry", "usdtry_index"),
        ("eurtry", "eurtry_index"),
        ("gram_gold_try", "gold_index"),
    ]:
        first_valid = weekly[col].dropna().iloc[0]
        weekly[idx_col] = weekly[col] / first_valid * 100

    weekly["usdtry_return_wow_pct"] = weekly["usdtry"].pct_change() * 100
    weekly["gold_return_wow_pct"] = weekly["gram_gold_try"].pct_change() * 100
    weekly["usdtry_vol_12w_pct"] = weekly["usdtry_return_wow_pct"].rolling(12).std()
    weekly["gold_vol_12w_pct"] = weekly["gold_return_wow_pct"].rolling(12).std()

    return weekly


def latest_dashboard_snapshot(weekly: pd.DataFrame) -> pd.DataFrame:
    latest = weekly.dropna(subset=["week_ending"]).iloc[-1]

    rows = [
        ("Policy rate", latest.get("policy_rate_pct"), "%", "Monetary policy anchor"),
        ("TLREF", latest.get("tlref_pct"), "%", "Overnight TL funding proxy"),
        ("TLREF-policy spread", latest.get("tlref_policy_spread_pp"), "pp", "Short-term funding pressure signal"),
        ("USD/TRY", latest.get("usdtry"), "", "FX pressure monitor"),
        ("Gram gold", latest.get("gram_gold_try"), "TRY", "FX/gold liquidity watch"),
        ("Deposit rate proxy", latest.get("deposit_rate_proxy_pct"), "%", "Average TRY deposit-rate proxy"),
        ("Loan rate proxy", latest.get("loan_rate_proxy_pct"), "%", "Average TRY loan-rate proxy"),
        ("10Y-2Y slope", latest.get("curve_slope_10y_2y_pp"), "pp", "Curve shape / rate-risk signal"),
        ("Total reserves", latest.get("total_reserves_usd_mn"), "USD mn", "FX-gold buffer proxy"),
    ]

    return pd.DataFrame(rows, columns=["metric", "latest_reading", "unit", "interpretation"])


def save_line_chart(df: pd.DataFrame, x: str, y_cols: list[str], title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(10, 5.5))
    for col in y_cols:
        if col in df.columns:
            plt.plot(df[x], df[col], label=col)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True, help="Local raw-data directory path")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).expanduser().resolve()
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    project_dir = Path(__file__).resolve().parents[1]
    tables_dir = project_dir / "outputs" / "tables"
    charts_dir = project_dir / "outputs" / "charts"
    tables_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    weekly = build_market_weekly_core(raw_dir)
    weekly_path = tables_dir / "market_weekly_core.csv"
    weekly.to_csv(weekly_path, index=False)

    snapshot = latest_dashboard_snapshot(weekly)
    snapshot_path = tables_dir / "latest_market_dashboard_snapshot.csv"
    snapshot.to_csv(snapshot_path, index=False)

    save_line_chart(
        weekly,
        "week_ending",
        ["policy_rate_pct", "tlref_pct", "tlref_policy_spread_pp"],
        "TL Funding Conditions: Policy Rate, TLREF and Spread",
        "Percent / percentage points",
        charts_dir / "tl_funding_conditions.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["usdtry_index", "eurtry_index", "gold_index"],
        "FX and Gold Liquidity Watch: Indexed USD/TRY, EUR/TRY and Gram Gold",
        "Index = 100 at first observation",
        charts_dir / "fx_gold_liquidity_watch.png",
    )

    save_line_chart(
        weekly,
        "week_ending",
        ["yield_2y_pct", "yield_5y_pct", "yield_10y_pct", "curve_slope_10y_2y_pp"],
        "Yield Curve Conditions: 2Y, 5Y, 10Y and 10Y-2Y Slope",
        "Percent / percentage points",
        charts_dir / "yield_curve_conditions.png",
    )

    reserve_cols = [c for c in ["gold_reserves_usd_mn", "fx_reserves_usd_mn", "total_reserves_usd_mn"] if c in weekly.columns]
    save_line_chart(
        weekly,
        "week_ending",
        reserve_cols,
        "CBRT Reserves Watch",
        "USD mn",
        charts_dir / "reserves_watch.png",
    )

    print(f"Weekly market dashboard dataset written to: {weekly_path}")
    print(f"Latest dashboard snapshot written to: {snapshot_path}")
    print(f"Charts written to: {charts_dir}")
    print("\nLatest snapshot:")
    print(snapshot.to_string(index=False))


if __name__ == "__main__":
    main()
