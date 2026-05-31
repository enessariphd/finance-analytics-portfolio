# Fortis Energy Growth Capital Screening Memo

A screening-level renewable energy growth capital case study based on public information, project-level solar economics, sensitivity analysis, and platform-level investment assessment.

## Project objective

The objective is to demonstrate growth capital screening, project economics, renewable energy investment analysis, and memo-style investment reasoning.

The project is designed for roles related to:

- Growth capital analysis
- Investment screening
- Renewable energy finance
- Infrastructure and project finance
- Corporate finance
- Development finance
- Investment banking / advisory support

## Case positioning

This is a screening-level investment case, not a full valuation or due diligence exercise.

The analysis evaluates Fortis Energy as a potentially scalable renewable energy developer / IPP platform, using the Tokça Solar Power Plant as a representative project-level benchmark.

## Main project economics

| Metric | Value | Interpretation |
|---|---:|---|
| Installed capacity | 6.9 MWp | Tokça SPP benchmark |
| Expected annual generation | 12,000 MWh | Over 12 GWh annual production |
| Investment cost | TRY 167.1m | Public project-cost benchmark |
| CAPEX / MWp | TRY 24.2m/MWp | Derived unit-cost benchmark |
| Specific production | 1,739 MWh/MWp/year | Generation efficiency proxy |
| Capacity factor | 19.9% | Screening-level solar production metric |
| Base PTF | TRY 2,619.81/MWh | 2025 average PTF assumption |
| First-year revenue | TRY 31.4m | Base merchant-price case |
| First-year EBITDA | TRY 28.1m | Revenue less screening O&M assumption |
| Simple payback | 5.9 years | CAPEX / first-year EBITDA |
| Screening project IRR | 15.4% | 20-year unlevered model with degradation |
| NPV @ 15% | TRY 3.6m | Screening-level base-case NPV |

## Main analytical conclusion

Fortis Energy is conditionally attractive as a growth capital opportunity.

The strongest case is not generic merchant solar exposure. The more attractive investment angle is scaling projects with visible offtake quality, municipal or C&I-linked demand, self-consumption economics, or storage-supported revenue resilience.

## Repository structure

- README.md
- requirements.txt
- run_all.py
- data/README.md
- scripts/01_project_economics.py
- outputs/charts/
- outputs/tables/
- memo/

## Main outputs

The workflow produces:

- Project economics summary
- Power-price and CAPEX sensitivity table
- Screening scorecard
- Project economics snapshot chart
- IRR sensitivity chart
- Payback sensitivity chart
- Growth capital screening scorecard chart

## Method summary

The Python workflow builds a screening-level solar project model using transparent assumptions:

- Tokça SPP benchmark capacity, generation and investment cost
- 2025 average PTF base price
- 2% of CAPEX annual O&M assumption
- 0.5% annual degradation
- 20-year project horizon
- 15% discount-rate NPV check
- Scenario sensitivity across power-price and CAPEX cases

## Important caveats

This is a public-data growth capital screening case study.

It does not represent:

- Investment advice
- A formal valuation
- A complete due diligence report
- A bankable project finance model
- A legal, tax, technical or regulatory assessment

The project economics are intentionally simplified to support screening-level investment reasoning. A full investment decision would require detailed diligence on permits, grid connection, offtake, financing, EPC contracts, operating costs, project debt, tax treatment and country-specific regulatory risk.

Prepared as a public-data growth capital memo. Not investment advice.
