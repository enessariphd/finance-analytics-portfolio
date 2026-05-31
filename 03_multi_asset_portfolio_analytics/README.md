# Türkiye Multi-Asset Portfolio Analytics

A Türkiye-focused multi-asset portfolio analytics case using public-data asset proxies. The project converts a workbook-based portfolio analysis into a reproducible Python workflow that prepares cleaned return series, computes asset and portfolio risk-return metrics, evaluates downside risk, runs stylized scenario analysis, and performs an illustrative Monte Carlo simulation.

## Project objective

The objective is to demonstrate practical portfolio analytics skills using a compact Türkiye-focused asset universe.

The project is designed for roles related to:

- Portfolio analytics
- Asset management research
- Market risk monitoring
- Quantitative investment analysis
- Scenario analysis and risk reporting
- Investment strategy support

## Asset proxies

The analysis uses four asset proxies:

| Asset class | Proxy | Role in analysis |
|---|---|---|
| Gold | GAU/TRY | Inflation and depreciation hedge |
| FX | USD/TRY | TRY depreciation exposure / portfolio hedge |
| Equity | BIST 30 Futures | Risk asset / growth exposure |
| Fixed income | HST Bond Fund | Defensive / stabilizing allocation |

Sample period: 2 May 2023 to 29 April 2026.

## Model portfolios

| Portfolio | GAU/TRY | USD/TRY | BIST 30 Futures | HST Bond Fund |
|---|---:|---:|---:|---:|
| Balanced Multi-Asset | 15% | 20% | 35% | 30% |
| Conservative / Pension-like | 15% | 15% | 20% | 50% |
| FX & Gold Hedge Tilt | 25% | 30% | 25% | 20% |

## Main outputs

The workflow produces:

- Workbook sheet inventory
- Clean price, return and index datasets
- Asset-level risk-return summary
- Portfolio-level risk-return summary
- Correlation matrix
- Drawdown series
- Historical VaR and Expected Shortfall table
- Scenario analysis table
- Monte Carlo simulation summary
- Portfolio and asset charts

## Selected Python-recomputed results

Asset-level metrics:

| Asset | Annualized return | Annualized volatility | Max drawdown | Return / volatility |
|---|---:|---:|---:|---:|
| GAU/TRY | 74.5% | 21.2% | -19.0% | 3.52 |
| USD/TRY | 32.7% | 8.4% | -5.2% | 3.91 |
| BIST 30 Futures | 44.8% | 32.5% | -24.3% | 1.38 |
| HST Bond Fund | 30.6% | 6.4% | -6.8% | 4.81 |

Portfolio-level metrics:

| Portfolio | Annualized return | Annualized volatility | Max drawdown | Return / volatility |
|---|---:|---:|---:|---:|
| Balanced Multi-Asset | 50.3% | 10.9% | -7.2% | 4.60 |
| Conservative / Pension-like | 43.2% | 8.6% | -4.3% | 5.05 |
| FX & Gold Hedge Tilt | 47.6% | 11.8% | -6.4% | 4.04 |

## Repository structure

- README.md
- requirements.txt
- run_all.py
- data/README.md
- scripts/01_inspect_workbook.py
- scripts/02_prepare_asset_returns.py
- scripts/03_portfolio_risk_metrics.py
- scripts/04_scenario_monte_carlo.py
- outputs/charts/
- outputs/tables/
- memo/

## Data sources

Raw source exports are not included in this repository.

The Python workflow expects a locally stored public-data workbook containing cleaned and aligned asset price and return series. The underlying asset proxies are GAU/TRY, USD/TRY, BIST 30 Futures and HST Borrowing Instruments Fund NAV.

See data/README.md for additional notes.

## Method summary

The workflow proceeds in four stages:

1. `01_inspect_workbook.py` audits the local workbook and creates a sheet inventory.
2. `02_prepare_asset_returns.py` exports cleaned prices, returns, portfolio weights and workbook summary tables.
3. `03_portfolio_risk_metrics.py` recomputes risk-return metrics, drawdowns, correlations, VaR and Expected Shortfall from clean return series.
4. `04_scenario_monte_carlo.py` generates stylized scenario analysis and an illustrative one-year Monte Carlo simulation.

Risk metrics include:

- Annualized return
- Annualized volatility
- Maximum drawdown
- Return / volatility ratio
- Historical 95% and 99% VaR
- Historical 95% and 99% Expected Shortfall
- Rolling-risk-ready return and drawdown datasets

## Important caveats

This is a public-data portfolio analytics case study.

It does not represent:

- Investment advice
- A live trading strategy
- A regulatory model
- A production portfolio management system
- An optimized efficient-frontier allocation

Scenario analysis is stylized and should be interpreted as sensitivity testing rather than as a macro forecast. The Monte Carlo section is illustrative and uses historical daily return behavior without explicitly modelling regime shifts, fat tails or time-varying correlations.

## How to run

Create and activate a local Python environment, then install requirements:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Run the full workflow:

python run_all.py --workbook "/path/to/turkiye_multi_asset_analysis_risk_return_fixed.xlsx"

Outputs are written to:

- outputs/tables/
- outputs/charts/

## Memo

The accompanying memo summarizes the portfolio construction logic, asset and portfolio risk-return results, downside risk metrics, scenario analysis, Monte Carlo simulation and investment implications.

Prepared as a public-data multi-asset portfolio case. Not investment advice.
