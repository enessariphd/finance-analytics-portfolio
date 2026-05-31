# Turkey Treasury / ALM & Liquidity Risk Dashboard

A public-data treasury and ALM monitoring case for Turkey. The project converts a manually developed Excel-based dashboard and memo into a reproducible Python workflow that audits raw public data, prepares market and banking-sector indicators, builds a weekly dashboard dataset, and generates a calibrated composite liquidity stress score.

## Project objective

The objective is to demonstrate how public market, macro-financial, banking-sector and selected bank financial statement data can be translated into a concise treasury / ALM monitoring dashboard.

The project is designed for roles related to treasury analytics, ALM and liquidity risk, market risk monitoring, banking-sector analytics, financial risk reporting, and treasury technology / dashboarding.

## Main outputs

The workflow produces:

- Raw public-data source inventory
- Weekly market and funding dashboard dataset
- Weekly banking-sector liquidity dataset
- Combined treasury / ALM dashboard dataset
- Latest dashboard snapshot
- Composite liquidity stress score and component table
- Garanti BBVA public-data ALM proxy tables
- Dashboard charts for funding, FX/gold, yield curve, reserves, banking liquidity, deposit structure, bank ALM proxy and stress score

## Latest dashboard snapshot

Selected latest readings from the Python workflow:

| Metric | Latest reading | Interpretation |
|---|---:|---|
| Policy rate | 37.0% | Monetary policy anchor |
| TLREF | 39.99% | Overnight TL funding proxy |
| TLREF-policy spread | 2.99 pp | Short-term funding pressure signal |
| USD/TRY | 45.58 | FX pressure monitor |
| Loan/deposit ratio | 88.1% | Sector funding balance proxy |
| FX deposit share | 40.5% | Dollarization / funding mix proxy |
| Total reserves | USD 171.5bn | FX-gold buffer proxy |
| Liquidity stress score | 57.0 / 100 | Elevated dashboard signal |

## Repository structure

- README.md
- requirements.txt
- run_all.py
- data/README.md
- scripts/01_inspect_raw_sources.py
- scripts/02_prepare_market_data.py
- scripts/03_prepare_banking_data.py
- scripts/04_build_dashboard_dataset.py
- scripts/05_prepare_bank_alm_proxy.py
- outputs/charts/
- outputs/tables/
- memo/

## Data sources

Raw data files are not included in this repository.

The workflow is designed to use locally stored public-source files from:

- TCMB / EVDS
- BIST TLREF
- BDDK / BRSA banking-sector data
- Public USD/TRY, EUR/TRY and GAU/TRY histories
- Public Turkey 2Y, 5Y and 10Y yield histories
- Garanti BBVA public financial statements and investor materials for the memo extension

See data/README.md for additional notes.

## Method summary

The workflow proceeds in four stages:

1. 01_inspect_raw_sources.py audits available raw files and produces a source inventory.
2. 02_prepare_market_data.py prepares market, FX/gold, yield, funding and reserves data.
3. 03_prepare_banking_data.py parses BDDK / BRSA HTML-exported .xls files and builds sector liquidity indicators.
4. 04_build_dashboard_dataset.py merges market and banking indicators, constructs stress components and generates the composite liquidity stress score.
5. 05_prepare_bank_alm_proxy.py optionally prepares a Garanti BBVA public-data ALM proxy extension from a local financial statement extract.

The composite liquidity stress score combines:

- TLREF-policy spread
- USD/TRY 12-week volatility
- Gold 12-week volatility
- Yield-curve inversion pressure
- Loan-deposit growth gap
- FX deposit share change
- Reserve decline pressure

The score is a calibrated management dashboard signal. It is not a regulatory liquidity metric.

## Important caveats

This is a public-data portfolio case study.

It does not claim to reproduce:

- A bank internal ALM model
- Regulatory LCR
- Internal FTP curves
- Behavioral cash-flow ladders
- Internal net interest income simulations
- Confidential bank-level treasury data

The Garanti BBVA section in the memo is a public-data-calibrated ALM proxy extension based on public financial statement information. It should be interpreted as a transparent analytical exercise, not as an internal bank model.

## How to run

Create and activate a local Python environment, then install requirements:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Run the full workflow:

python run_all.py --raw-dir "/path/to/local/data_raw"

Optional Garanti BBVA ALM proxy extension:

python run_all.py --raw-dir "/path/to/local/data_raw" --bank-pack "/path/to/treasury_alm_data_pack_4_bank_alm_extension.xlsx"

Outputs are written to:

- outputs/tables/
- outputs/charts/

## Memo

The accompanying memo summarizes the dashboard logic, key findings, stress score construction and Garanti BBVA ALM proxy extension.

Prepared as a treasury / ALM portfolio case study. Not investment advice.
