# Enterprise Data Reconciliation & Financial Audit

### Financial Reconciliation and Revenue Analytics Using Python, SQL, and Data Visualization

## 1. Project Overview

The Enterprise Data Reconciliation & Financial Audit project combines historical customer account records, unstructured server transaction logs, and daily EUR/USD exchange rates to produce an audit-ready transaction dataset.

The project uses Python, Pandas, SQLite, Regular Expressions, and Matplotlib to transform raw data into structured financial information.

The final outputs include reconciled transactions, monthly revenue summaries, top customer analysis, project metrics, and a financial dashboard.

This project demonstrates practical data analytics and data engineering skills, including data extraction, data cleaning, SQL querying, financial reconciliation, validation, and visualization.

---

## 2. Business Problem

Organizations often store customer information, transaction logs, and exchange-rate information in separate systems.

Combining these sources presents several challenges:

- Historical customer records may contain multiple account statuses.
- Transaction logs may contain unstructured text.
- Failed transactions must be excluded from valid transaction extraction.
- Missing exchange rates must be handled consistently.
- Transactions must be reconciled against the latest customer account status.
- Financial results must be summarized for reporting and analysis.

The objective is to build a repeatable data-processing pipeline that addresses these challenges and produces reliable financial summaries.

---

## 3. Project Objectives

The main objectives are:

1. Identify each customer's latest account status using SQL.
2. Extract transaction details from unstructured server logs using Regular Expressions.
3. Exclude error records from valid transaction extraction.
4. Clean transaction dates and numeric values.
5. Handle missing EUR/USD exchange rates.
6. Reconcile transactions with customers whose latest recorded status is Active.
7. Calculate transaction revenue in USD.
8. Generate monthly revenue and top-five customer summaries.
9. Validate the processed datasets and financial metrics.
10. Create a dashboard to communicate key findings.

---

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.10+ | Main programming language |
| Pandas | Data cleaning, transformation, merging, and aggregation |
| SQLite | Customer database queries |
| SQL | Historical customer status analysis |
| Regular Expressions (Regex) | Transaction information extraction |
| Matplotlib | Financial data visualization |
| Jupyter Notebook | Interactive, phase-by-phase analysis |
| CSV | Data exchange and report files |
| JSON | Structured project metrics |
| VS Code | Development environment |

---

## 5. Project Files

The project directory contains the following files:

```text
Enterprise_Data_Reconciliation/
│
├── Enterprise_Data_Reconciliation.ipynb
├── build_project.py
├── enterprise_database.db
├── server_logs.txt
├── daily_exchange_rates.csv
├── README.md
├── Enterprise_Data_Reconciliation_Report.pdf
│
└── output/
    ├── active_users.csv
    ├── clean_transactions.csv
    ├── final_reconciled_transactions.csv
    ├── monthly_revenue.csv
    ├── top_5_customers.csv
    ├── project_metrics.json
    └── cfo_dashboard.png
```

### Input files

**1. `enterprise_database.db`**

SQLite database containing historical customer account records, including customer IDs, names, statuses, and update timestamps.

**2. `server_logs.txt`**

Text file containing 100,000 raw server log records, plus a header line.

The log records include transaction information and error events.

**3. `daily_exchange_rates.csv`**

CSV file containing daily EUR/USD exchange rates for 2023.

### Main processing files

**4. `Enterprise_Data_Reconciliation.ipynb`**

Jupyter Notebook containing the documented analysis and data-processing workflow.

**5. `build_project.py`**

Python script intended to execute the complete data-processing pipeline and generate the project outputs.

### Output files

| File | Description |
|---|---|
| `active_users.csv` | Latest customer records whose current recorded status is Active |
| `clean_transactions.csv` | Extracted and cleaned transaction records |
| `final_reconciled_transactions.csv` | Transactions reconciled with exchange rates and active customer records |
| `monthly_revenue.csv` | Monthly revenue, transaction counts, and customer summaries |
| `top_5_customers.csv` | Five customers with the highest reconciled USD revenue |
| `project_metrics.json` | Key processing and reconciliation metrics |
| `cfo_dashboard.png` | Dashboard showing monthly revenue and top customers |

---

## 6. Installation and Setup

### Prerequisites

Install the following:

- Python 3.10 or newer
- Visual Studio Code or another Python editor
- Python extension for VS Code
- Jupyter extension for VS Code, if using the notebook

### Install dependencies

Open a terminal in the project directory and run:

```bash
python -m pip install pandas matplotlib jupyter
```

Verify the installation:

```bash
python --version
python -m pip show pandas
python -m pip show matplotlib
```

If the project uses a virtual environment, activate it before installing dependencies.

### Windows PowerShell virtual environment

Create a virtual environment if you do not already have one:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install pandas matplotlib jupyter
```

If `.venv` already exists, you do not need to create it again.

---

## 7. How to Run the Project

### Option 1: Run the complete Python pipeline

Open a terminal in the project root directory.

Execute:

```bash
python build_project.py
```

The script should process the input files and regenerate the output datasets, metrics, and dashboard.

Check the terminal for errors before treating the run as successful.

### Option 2: Run the Jupyter Notebook

1. Open `Enterprise_Data_Reconciliation.ipynb` in VS Code.
2. Select the project's Python interpreter.
3. Confirm that the required dependencies are installed.
4. Run the notebook cells from top to bottom.
5. Review the displayed outputs and validation results.
6. Confirm that the expected files exist in the `output/` directory.

The notebook and Python script should implement the same core processing logic.

---

## 8. Project Methodology

The pipeline consists of four main phases.

### Phase 1: Customer Database Analysis

The SQLite database contains historical records for customers.

A SQL window function assigns a row number to each record within its customer group:

```sql
ROW_NUMBER() OVER (
    PARTITION BY user_id
    ORDER BY updated_at DESC
)
```

The query selects the latest record for each customer and retains only records whose latest status is `Active`.

This prevents a customer from being treated as active merely because an older historical record had that status.

The selected records are exported to:

`output/active_users.csv`

### Phase 2: Server Log Processing

The server log file contains unstructured transaction text.

The pipeline:

1. Reads the log records.
2. Excludes records containing the `ERROR` log level.
3. Applies Regular Expressions to extract transaction fields.
4. Converts date and numeric fields to appropriate data types.
5. Checks the number of successfully parsed records.
6. Saves the extracted transaction dataset.

The main extracted fields are:

| Field | Description |
|---|---|
| `Date` | Transaction date |
| `User_ID` | Customer identifier |
| `Product_ID` | Product identifier |
| `EUR_Value` | Transaction value in euros |

The cleaned dataset is saved to:

`output/clean_transactions.csv`

### Phase 3: Exchange-Rate Processing and Reconciliation

The exchange-rate data is sorted by date.

Missing exchange-rate values are filled using forward-fill, which carries the most recent available rate forward.

The transaction dataset is left-joined with the exchange-rate data. This preserves transaction rows during the rate-joining stage so that missing matches can be identified and validated.

The transactions are then inner-joined with the latest active customer records.

Only transactions that match a customer whose latest recorded account status is Active are retained in the final reconciled dataset.

USD revenue is calculated as:

```python
USD_Revenue = EUR_Value * EUR_to_USD
```

A monthly period field is also derived from each transaction date.

The final dataset is saved to:

`output/final_reconciled_transactions.csv`

### Phase 4: Financial Analysis and Visualization

The reconciled dataset is used to calculate:

- Total revenue by month
- Transaction counts by month
- Unique customer counts by month
- Total revenue by customer
- Top five customers by reconciled USD revenue

The project generates a dashboard containing:

1. Monthly Reconciled Revenue
2. Top 5 Customers by Revenue

The dashboard is saved to:

`output/cfo_dashboard.png`

---

## 9. Data Quality and Validation

The project includes checks to assess whether the processing results are consistent.

Important checks include:

- Verifying the number of raw log records.
- Counting excluded error records.
- Comparing non-error records with successfully parsed transactions.
- Checking missing exchange rates after filling.
- Verifying customer reconciliation results.
- Checking the number of final transaction records.
- Calculating total reconciled revenue.
- Confirming that the expected output files exist.

The reconciliation process also uses merge validation to help verify the expected relationship between transactions, exchange rates, and customer records.

These checks support reproducibility and make the results easier to audit.

---

## 10. Key Results

The following results were observed for the supplied dataset.

| Metric | Result |
|---|---:|
| Raw server log records | 100,000 |
| Error records excluded | 5,098 |
| Successfully parsed transactions | 94,902 |
| Historical customer records | 47,464 |
| Distinct customers in database | 25,000 |
| Latest active customers | 14,183 |
| Exchange-rate records | 365 |
| Missing exchange-rate values filled | 104 |
| Reconciled transactions | 53,899 |
| Customers with reconciled transactions | 13,888 |
| Monthly revenue summary records | 12 |
| Top customers reported | 5 |
| Total reconciled USD revenue | $148,274,622.91 |

The processing time depends on the computer, Python environment, and execution conditions.

---

## 11. Financial Dashboard

The project generates a dashboard with two visualizations:

### Monthly Reconciled Revenue

Shows how the total reconciled USD revenue changes from month to month during 2023.

This chart can help identify monthly revenue patterns and periods of relatively higher or lower revenue.

### Top Five Customers by Revenue

Compares the five customers with the highest total reconciled USD revenue.

This chart helps identify the customers contributing the most revenue within the reconciled dataset.

### Dashboard file

The generated dashboard is available at:

`output/cfo_dashboard.png`

Open the image in VS Code or another image viewer to inspect the charts.

---

## 12. Important Interpretation Notes

### Customer eligibility

The final reconciled dataset includes transactions only for customers whose latest recorded account status is `Active`.

Therefore, the final dataset contains fewer rows than the successfully parsed transaction dataset.

### Exchange-rate handling

Forward-fill carries the previous available exchange rate into missing dates.

If missing values occur before the first available rate, they require special handling because no earlier rate exists. Any fallback method should be documented.

### Revenue interpretation

The reported USD revenue is calculated from the supplied EUR transaction values and the exchange rates in the provided dataset.

It represents the calculated revenue of the reconciled records, not necessarily audited or recognized revenue under a company's accounting policies.

### Error records

The 5,098 error records are excluded from valid transaction extraction according to the project's processing rule.

Their exclusion does not establish whether the underlying business transactions were reversed, retried, or recorded elsewhere.

---

## 13. Limitations and Future Improvements

Potential improvements include:

1. Add automated unit tests for parsing and reconciliation.
2. Create a formal data-quality report for malformed records.
3. Add a configurable audit log for every processing stage.
4. Compare reconciliation totals against an independent financial control total.
5. Improve dashboard design with additional business KPIs.
6. Add filters for months, customers, and product categories.
7. Package dependencies in a `requirements.txt` file.
8. Add a GitHub Actions workflow for automated testing.
9. Add explicit handling and reporting for exchange rates missing at the beginning of the date range.
10. Add a reproducibility check that compares notebook and script outputs.

---

## 14. Skills Demonstrated

This project demonstrates practical experience with:

- Python programming
- Pandas data transformation
- SQL window functions
- SQLite database querying
- Regular Expressions
- Unstructured log parsing
- Data cleaning and validation
- Handling missing values
- Joining multiple datasets
- Financial reconciliation
- Currency conversion
- Grouped aggregation
- Matplotlib visualization
- Jupyter Notebook development
- Reproducible data pipelines
- Technical documentation

---

## 15. Conclusion

The Enterprise Data Reconciliation & Financial Audit project demonstrates how historical customer data, unstructured transaction logs, and exchange-rate information can be combined into a structured financial dataset.

The pipeline identifies the latest active customer records, extracts transaction details, handles missing exchange rates, reconciles transactions, calculates USD revenue, and produces financial summaries and visualizations.

The resulting datasets, project metrics, and dashboard provide a foundation for financial analysis and further audit-oriented validation.

**Project status:** Core pipeline implemented; results should be reproduced and validated before the project is published or submitted.