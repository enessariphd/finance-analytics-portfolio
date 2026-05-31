# Finance Analytics Portfolio

This repository contains a set of public-data finance analytics portfolio projects developed to demonstrate applied skills in credit risk analytics, treasury/ALM monitoring, public company valuation, multi-asset portfolio analytics and growth capital screening.

## Projects

1. **[Credit Risk Analytics Mini-Model](01_credit_risk_analytics/)**  
   PD estimation, model validation, IFRS 9-style ECL, stress testing and Turkey macro-sector overlay.

2. **[Turkey Treasury / ALM & Liquidity Risk Dashboard](02_treasury_alm_liquidity_dashboard/)**  
   Public-data treasury and ALM monitoring workflow using Python to audit raw sources, prepare market and banking-sector indicators, build a weekly dashboard dataset, and generate a calibrated composite liquidity stress score.

3. **[Türkiye Multi-Asset Portfolio Analytics](03_multi_asset_portfolio_analytics/)**  
   Python portfolio analytics workflow covering cleaned return series, risk-return metrics, drawdowns, VaR/ES, scenario testing and Monte Carlo simulation across Türkiye-focused asset proxies.

4. **[Ford Otosan Public Company Valuation Case](04_froto_public_company_valuation/)**  
   Public-company valuation case with IAS29-consistent real DCF, trading comparables, WACC/beta sensitivity, valuation-method divergence and memo-ready Python charts.

5. **[Fortis Energy Growth Capital Screening Memo](05_fortis_growth_capital_screening/)**  
   Renewable energy growth capital screening case with project economics, IRR/payback sensitivity, platform assessment and memo-ready Python charts.

## How to read this portfolio

This portfolio is organized so that different reviewers can start with the projects most relevant to their role focus:

| Role focus | Suggested starting points |
|---|---|
| Credit risk / banking analytics | Project 01: Credit Risk Analytics Mini-Model; Project 02: Treasury / ALM Dashboard |
| Treasury / ALM / market risk | Project 02: Treasury / ALM Dashboard; Project 03: Multi-Asset Portfolio Analytics |
| Portfolio analytics / asset management | Project 03: Multi-Asset Portfolio Analytics |
| Corporate finance / valuation | Project 04: Ford Otosan Valuation Case; Project 05: Fortis Growth Capital Screening |
| Growth capital / investment screening | Project 05: Fortis Growth Capital Screening; Project 04: Ford Otosan Valuation Case |
| Data analytics / Python workflow review | Projects 01, 02 and 03 provide the strongest reproducible Python workflow signals |

## Scope

All projects are built using publicly available data and are intended as analytical portfolio case studies. They do not represent investment advice, regulatory models, internal bank models, or production financial systems.
