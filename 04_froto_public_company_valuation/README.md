# Ford Otosan / FROTO Public Company Valuation Case

A public-company valuation case study for Ford Otosan (FROTO), combining an IAS29-consistent real DCF framework, trading comparables, valuation sensitivity analysis, beta/WACC sensitivity, and a final business memo.

## Project objective

The objective is to demonstrate practical valuation, corporate finance and investment analysis skills through a public-data company case.

The project is designed for roles related to:

- Corporate finance
- Valuation
- Investment banking analysis
- Equity research support
- FP&A / strategic finance
- Investment screening
- Financial modelling and business case analysis

## Valuation date

15 May 2026.

## Main valuation references

| Reference point | Value | Interpretation |
|---|---:|---|
| Current price | TRY 91.45 | Market reference as of valuation date |
| Base real DCF | TRY 90.45 | Intrinsic value anchor |
| Bear real DCF | TRY 62.43 | Downside real DCF case |
| Bull real DCF | TRY 123.17 | Upside real DCF case |
| Şeker Invest target price | TRY 149.30 | External sanity check only |
| Broader BIST auto P/E comps | TRY 172.55 | Secondary earnings-based check |
| Core EV/EBITDA comps | TRY 202.11 | Preferred relative valuation signal |

## Main analytical conclusion

The case does not force a single target price. The more defensible interpretation is valuation-method divergence:

- Conservative IAS29-consistent real DCF is close to the current market price.
- Local trading comparables imply a more constructive relative valuation signal.
- The gap is driven by WACC/beta assumptions, IAS29 treatment, peer comparability, EBITDA definitions and forward earnings assumptions.

## Repository structure

- README.md
- requirements.txt
- run_all.py
- data/README.md
- scripts/01_inspect_workbook.py
- scripts/02_extract_valuation_outputs.py
- scripts/03_generate_valuation_charts.py
- outputs/charts/
- outputs/tables/
- memo/

## Main outputs

The workflow produces:

- Workbook sheet inventory
- Valuation methods summary
- Bear/base/bull real DCF case table
- WACC × terminal growth sensitivity table
- Peer multiple summary
- Beta sensitivity table
- Python-generated valuation overview chart
- Real DCF case range chart
- WACC × terminal growth sensitivity heatmap
- Peer multiple summary chart
- Beta sensitivity chart

## Method summary

The workflow proceeds in three stages:

1. `01_inspect_workbook.py` audits the local valuation workbook and creates a sheet inventory.
2. `02_extract_valuation_outputs.py` extracts memo-ready valuation outputs from the local workbook.
3. `03_generate_valuation_charts.py` generates valuation charts from the extracted tables.

## Data and model notes

Raw source files and Excel model versions are not included in this repository.

The Python workflow expects a locally stored final valuation workbook containing cleaned valuation outputs and sensitivity tables. The original case used public information including:

- Ford Otosan annual reports and financial statements
- Ford Otosan 2025YE and 1Q26 earnings releases
- BIST market price data
- Selected automotive peer financial statements
- Public macro and WACC reference data
- External broker target price as a sanity check only

## Important caveats

This is a public-data valuation case study.

It does not represent:

- Investment advice
- A sell-side recommendation
- A production valuation model
- A target price recommendation
- A complete due diligence report

The external broker target price is used only as a sanity check and methodological comparison point. The trading comparables output should be interpreted directionally because the local peer set is heterogeneous.

Prepared as a public-company valuation case study. Not investment advice.
