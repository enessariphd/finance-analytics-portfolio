# Credit Risk Analytics Mini-Model

## PD Estimation, Model Validation, IFRS 9-style ECL and Turkey Macro-Sector Overlay

This project develops a public-data credit risk analytics workflow using LendingClub loan-level data. The objective is to demonstrate how a credit portfolio can be analyzed through probability-of-default (PD) modeling, borrower risk segmentation, model validation, illustrative expected credit loss (ECL) calculation, stress scenario analysis and local macro-sector monitoring.

The project is designed as a portfolio case study for credit risk analytics, risk methodologies, model validation, IFRS 9-style ECL, credit portfolio monitoring, banking risk management and financial risk advisory roles.

---

## 1. Project Overview

The workflow combines three components:

1. Retail credit default prediction model  
   A borrower-level PD model is developed using public LendingClub accepted-loan data.

2. IFRS 9-style expected credit loss mini-framework  
   Predicted PDs are translated into an illustrative ECL framework using simplified LGD and EAD assumptions.

3. Compact portfolio monitoring and macro-sector overlay  
   Risk bands, stress scenarios, threshold simulations, risk migration and Turkish banking-sector indicators are used to create a management-style credit risk view.

The project is not intended to replicate a bank's internal IRB, regulatory IFRS 9 or production credit decisioning model. It is an illustrative credit risk analytics case built with public data.

---

## 2. Data Sources

### 2.1 LendingClub Loan-Level Data

The main modeling dataset is based on public LendingClub accepted-loan data. The raw file is not included in this repository because of file size and data redistribution constraints.

Users should place the accepted-loan file under:

    data/raw/accepted_2007_to_2018Q4.csv.gz

The model uses only variables observable at or near loan origination to reduce target leakage. Post-origination performance variables such as recoveries, total payments, last payment information and collection-related variables are excluded from PD model development.

### 2.2 BDDK / TCMB Turkey Macro-Sector Overlay

A separate local-market overlay is added using Turkish banking-sector and macro-financial indicators. This overlay is not used as an input to the LendingClub PD model. It is included only to connect the analytical workflow to the Turkish banking risk environment.

The overlay uses:

- BDDK loan data
- BDDK non-performing loan data
- BDDK NPL allowance / special provision data
- TCMB 1-week repo policy rate
- TCMB consumer price inflation

Users should place the relevant BDDK files under:

    data/raw/loans.xls
    data/raw/npl.xls

---

## 3. Default Definition

The binary default flag is constructed from LendingClub loan status.

Non-default class:

    Fully Paid
    Does not meet the credit policy. Status:Fully Paid

Default / bad class:

    Charged Off
    Default
    Late (31-120 days)
    Does not meet the credit policy. Status:Charged Off

Loans with unresolved or intermediate status such as Current, Issued, In Grace Period and short-term delinquency statuses are excluded from the binary modeling sample.

This produces a resolved-loan modeling sample suitable for an illustrative PD model and out-of-sample validation exercise.

---

## 4. Modeling Approach

### 4.1 Primary Model: Logistic Regression

The primary PD model is an interpretable logistic regression model. Logistic regression is retained as the main model because it is transparent, directionally interpretable and aligned with traditional credit scorecard logic.

The logistic regression model is used as the primary source of predicted PDs for:

- PD deciles
- Borrower risk bands
- Calibration analysis
- Illustrative ECL calculation
- Stress scenario analysis
- Approval-threshold simulation

### 4.2 Challenger Model: XGBoost

An XGBoost classifier is trained as a challenger model to test whether a non-linear machine learning model improves discriminatory power relative to the interpretable logistic benchmark.

The challenger model is used for model comparison and feature-importance analysis, but the logistic regression model remains the primary PD model due to interpretability and calibration performance.

### 4.3 Validation Metrics

The project evaluates model performance using:

- ROC / AUC
- Gini coefficient
- Confusion matrix
- Precision, recall and F1 score
- Calibration by PD decile
- Actual vs predicted default rate by decile
- Train-test PD score PSI
- Feature importance and logistic coefficient analysis

---

## 5. IFRS 9-style ECL Framework

The project calculates illustrative ECL using:

    ECL = PD x LGD x EAD

Where:

- PD = predicted probability of default from the primary logistic regression model
- LGD = assumed loss-given-default rate
- EAD = funded loan amount used as an exposure-at-default proxy

A simplified staging proxy is used:

    Stage 1: Low and Medium Risk non-default loans
    Stage 2: High and Very High Risk non-default loans
    Stage 3: Observed defaulted loans

This is an illustrative approximation and should not be interpreted as a regulatory IFRS 9 implementation.

Important limitations:

- Lifetime PD is approximated through a simplified multiplier for Stage 2.
- Stage 3 is proxied using observed default status in the resolved-loan test sample.
- LGD is assumed rather than estimated from collateral, recovery and workout data.
- EAD is proxied by funded loan amount.

---

## 6. Stress Scenario Design

The ECL framework is evaluated under four scenarios:

| Scenario | PD Multiplier | LGD Assumption | EAD Assumption |
|---|---:|---:|---:|
| Base | 1.00x | 45% | 1.00x |
| Mild Deterioration | 1.15x | 50% | 1.00x |
| Adverse | 1.25x | 55% | 1.00x |
| Severe Stress | 1.50x | 60% | 1.00x |

The scenarios are designed to illustrate how portfolio ECL responds to worsening credit conditions. They are not intended to represent official regulatory stress scenarios.

---

## 7. Model Stability and Strategy Simulation

In addition to standard model validation, the project includes three portfolio-monitoring extensions.

### 7.1 PSI / Stability Check

The train-test predicted PD distribution is compared using Population Stability Index (PSI).

Interpretation rule of thumb:

    PSI < 0.10: stable / no material shift
    0.10 <= PSI < 0.25: moderate distribution shift
    PSI >= 0.25: significant distribution shift

### 7.2 Approval Threshold Simulation

The project simulates simple PD cutoff strategies:

    Approve loans with PD <= threshold
    Reject or manually review loans with PD > threshold

This is not an underwriting recommendation. It is an illustrative strategy analysis showing the trade-off between approval volume, exposure retained and default capture.

### 7.3 Risk Band Migration under Stress

The project applies stressed PD multipliers and reassigns loans to risk bands using base PD cutoffs. This produces an illustrative migration matrix showing how exposure moves from lower to higher risk bands under adverse and severe stress conditions.

---

## 8. Key Results

Selected project outputs:

| Area | Result |
|---|---:|
| Clean modeling observations | 1,369,164 |
| Observed default rate | 21.23% |
| Total EAD proxy in clean data | USD 19.77bn |
| Logistic Regression test AUC | 0.709 |
| Logistic Regression test Gini | 0.417 |
| XGBoost challenger test AUC | 0.718 |
| XGBoost challenger test Gini | 0.436 |
| Low Risk actual default rate | 7.37% |
| Very High Risk actual default rate | 38.86% |
| Very High Risk exposure share | 31.21% |
| Very High Risk default share | 45.75% |
| Stage 1 exposure share | 40.05% |
| Stage 1 ECL share | 8.69% |
| Stage 2 + Stage 3 ECL share | 91.31% |
| Very High Risk ECL share | 53.05% |
| Base scenario total ECL | USD 1.34bn |
| Severe Stress total ECL | USD 2.17bn |
| Severe Stress ECL increase vs base | 61.43% |
| Train-test PD score PSI | Stable / no material shift |

The final logistic PD model shows strong calibration by decile, with predicted PDs closely tracking realized default rates across the risk distribution.

---

## 9. Turkey Macro-Sector Overlay

The Turkey overlay is included to provide local banking-sector relevance. It is not used in model estimation.

Latest selected overlay date: 2026-05-08

| Indicator | Value |
|---|---:|
| Total NPL ratio | 2.78% |
| Consumer NPL ratio | 4.63% |
| Commercial NPL ratio | 2.18% |
| SME NPL ratio | 3.61% |
| Coverage ratio | 75.42% |
| Policy rate | 37.00% |
| CPI YoY | 32.37% |
| Total loan growth since first selected date | 41.93% |
| NPL growth since first selected date | 157.20% |

The overlay shows that NPL growth outpaced total loan growth over the selected period, supporting the relevance of portfolio monitoring, stress testing and ECL-style analysis in a local banking context.

---

## 10. Repository Structure

    credit-risk-analytics-mini-model/
    |
    |-- data/
    |   |-- raw/
    |   |-- interim/
    |   |-- clean/
    |
    |-- outputs/
    |   |-- charts/
    |   |-- tables/
    |   |-- models/
    |
    |-- scripts/
    |   |-- 01_prepare_data.py
    |   |-- 02_train_models.py
    |   |-- 03_model_validation.py
    |   |-- 04_ecl_scenarios.py
    |   |-- 05_model_interpretability.py
    |   |-- 06_generate_project_summary.py
    |   |-- 07_stability_and_strategy.py
    |   |-- 08_turkey_macro_overlay.py
    |
    |-- memo/
    |-- run_all.py
    |-- requirements.txt
    |-- requirements_freeze.txt
    |-- README.md
    |-- .gitignore

---

## 11. How to Run

### Step 1: Create and activate virtual environment

    python3 -m venv .venv
    source .venv/bin/activate

### Step 2: Install dependencies

    pip install -r requirements.txt

### Step 3: Add raw data

Place the following files under data/raw/:

    accepted_2007_to_2018Q4.csv.gz
    loans.xls
    npl.xls

### Step 4: Run full pipeline

    python run_all.py

This runs all scripts from data preparation to model training, validation, ECL calculation, stability analysis and Turkey macro-sector overlay.

---

## 12. Script Pipeline

| Script | Purpose |
|---|---|
| 01_prepare_data.py | Reads LendingClub accepted loans, applies default definition and creates clean modeling data |
| 02_train_models.py | Trains logistic regression primary PD model and XGBoost challenger model |
| 03_model_validation.py | Generates ROC, confusion matrix, calibration, decile validation and risk bands |
| 04_ecl_scenarios.py | Builds illustrative IFRS 9-style ECL and stress scenario outputs |
| 05_model_interpretability.py | Extracts logistic coefficients and XGBoost feature importance |
| 06_generate_project_summary.py | Creates key project metrics summary |
| 07_stability_and_strategy.py | Adds PSI, approval-threshold simulation and risk band migration |
| 08_turkey_macro_overlay.py | Builds Turkey BDDK/TCMB macro-sector overlay |

---

## 13. Main Outputs

### Tables

    outputs/tables/model_performance.csv
    outputs/tables/validation_by_decile.csv
    outputs/tables/risk_band_summary.csv
    outputs/tables/ecl_by_risk_band.csv
    outputs/tables/scenario_ecl_summary.csv
    outputs/tables/psi_summary.csv
    outputs/tables/threshold_strategy_simulation.csv
    outputs/tables/risk_band_migration_under_stress.csv
    outputs/tables/turkey_macro_sector_overlay_summary.csv
    outputs/tables/project_key_metrics.csv

### Charts

    outputs/charts/roc_curve.png
    outputs/charts/calibration_by_decile.png
    outputs/charts/actual_vs_predicted_default_by_decile.png
    outputs/charts/default_rate_by_risk_band.png
    outputs/charts/ecl_by_risk_band.png
    outputs/charts/scenario_ecl_comparison.png
    outputs/charts/train_test_pd_distribution.png
    outputs/charts/approval_threshold_simulation.png
    outputs/charts/adverse_risk_band_migration.png
    outputs/charts/turkey_segment_npl_ratios.png
    outputs/charts/turkey_loan_growth_vs_npl_growth.png

---

## 14. Limitations

This project has several important limitations:

1. Public-data limitation  
   The project uses public LendingClub data rather than internal bank credit data.

2. Resolved-loan sample  
   The modeling sample is restricted to loans with observed or default-like outcomes.

3. Simplified ECL framework  
   The ECL calculation is illustrative and does not represent a regulatory IFRS 9 implementation.

4. Assumed LGD  
   LGD is assumed rather than estimated from collateral, recovery and workout data.

5. EAD proxy  
   Funded loan amount is used as a simplified EAD proxy.

6. Turkey overlay is contextual  
   Turkish BDDK/TCMB indicators are used only as a local macro-sector overlay and are not model inputs.

7. No production deployment  
   The project is designed as an analytical portfolio case, not a production credit decisioning system.

---

## 15. Intended Use

This project is intended to demonstrate skills relevant to:

- Credit Risk Analytics
- Credit Risk Validation
- Risk Methodologies
- IFRS 9 / ECL Analytics
- Credit Portfolio Monitoring
- Collection Analytics
- Financial Risk Management Advisory
- Banking Risk Management
- Risk Analytics Data Science

---

## 16. Suggested Portfolio Description

Built a public-data credit risk analytics mini-model using LendingClub loan-level data, combining an interpretable logistic regression PD model, XGBoost challenger model, model validation, calibration, risk segmentation, illustrative IFRS 9-style ECL, stress scenarios and Turkey banking-sector macro overlay.
