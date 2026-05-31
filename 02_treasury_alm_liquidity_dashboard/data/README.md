# Data Notes

This project is designed as a public-data treasury / ALM analytics workflow.

Raw data files are not included in the repository. The scripts expect the user to place the required public-source files in a local raw-data directory and pass that directory path when running the pipeline.

Main data blocks used in the project:

- TCMB / EVDS policy rate, CPI, deposit rates, loan rates and reserves
- BIST TLREF historical data
- USD/TRY, EUR/TRY and GAU/TRY market histories
- Turkey 2Y, 5Y and 10Y yield histories
- BDDK / BRSA banking-sector data on loans, deposits, securities and FX position
- Garanti BBVA public financial statements and investor materials for the bank-level ALM proxy extension

The analysis standardizes daily, monthly, weekly and quarterly public data into a weekly monitoring frame. The resulting dashboard indicators are analytical proxies and should not be interpreted as regulatory LCR, internal FTP, behavioral ALM cash-flow ladders or internal NII simulations.
