# Data Notes

This project is a Türkiye-focused multi-asset portfolio analytics case study.

Raw data files are not included in this repository. The Python workflow expects a locally stored public-data workbook containing cleaned and aligned asset price series.

The original asset proxies used in the case are:

- GAU/TRY as a gram gold / precious-metal proxy
- USD/TRY as an FX hedge proxy
- BIST 30 Futures as an equity-market risk proxy
- HST Borrowing Instruments Fund NAV as a TRY fixed-income / bond-fund proxy

The workflow uses a local workbook with sheets such as:

- Clean_Prices
- Daily_Returns
- Index_100
- Portfolio_Weights
- Portfolio_Returns
- Portfolio_Summary
- Asset_Summary

The repository includes scripts, generated outputs and the final memo, but excludes raw source exports and intermediate Excel files.

This is an analytical portfolio case study and is not investment advice.
