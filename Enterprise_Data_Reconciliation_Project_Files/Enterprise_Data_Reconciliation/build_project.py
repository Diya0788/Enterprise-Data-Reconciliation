from pathlib import Path
import pandas as pd, sqlite3, re, time, shutil, json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
OUT = BASE / 'output'
OUT.mkdir(exist_ok=True)
DB = BASE / 'enterprise_database.db'
LOGS = BASE / 'server_logs.txt'
RATES = BASE / 'daily_exchange_rates.csv'

start = time.perf_counter()

# PHASE 1 — Latest account status per user using SQL window functions
with sqlite3.connect(DB) as conn:
    sql = '''
    WITH ranked_users AS (
        SELECT user_id, name, status, updated_at,
               ROW_NUMBER() OVER (
                   PARTITION BY user_id
                   ORDER BY updated_at DESC
               ) AS rn
        FROM users
    )
    SELECT user_id, name, status, updated_at
    FROM ranked_users
    WHERE rn = 1 AND status = 'Active'
    '''
    df_active_users = pd.read_sql_query(sql, conn)
df_active_users.to_csv(OUT / 'active_users.csv', index=False)

# PHASE 2 — Load the 100,000 raw log records and parse vectorially
raw_logs = pd.read_csv(LOGS, dtype=str, keep_default_na=False)
log_col = 'Raw_Server_Log' if 'Raw_Server_Log' in raw_logs.columns else raw_logs.columns[0]
raw = raw_logs[log_col].astype('string')
error_mask = raw.str.contains(r'\bERROR\b', regex=True, na=False)
error_count = int(error_mask.sum())
info_logs = raw.loc[~error_mask]
pattern = (
    r'\[(?P<Date>\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}\]'
    r'.*?"u":"(?P<User_ID>U-\d+)"'
    r'.*?"item_code":"(?P<Product_ID>PRD-\d+)"'
    r'.*?"eur_val":(?P<EUR_Value>\d+(?:\.\d+)?)'
)
extracted_data = info_logs.str.extract(pattern)
extracted_data = extracted_data.dropna(subset=['Date','User_ID','Product_ID','EUR_Value']).copy()
extracted_data['Date'] = pd.to_datetime(extracted_data['Date'], errors='coerce')
extracted_data['EUR_Value'] = pd.to_numeric(extracted_data['EUR_Value'], errors='coerce')
extracted_data = extracted_data.dropna(subset=['Date','EUR_Value'])
extracted_data = extracted_data.reset_index(drop=True)
extracted_data.to_csv(OUT / 'clean_transactions.csv', index=False)

# PHASE 3 — Fill missing daily FX values, merge transactions and active users
rates = pd.read_csv(RATES, parse_dates=['Date']).sort_values('Date').copy()
missing_rates_before = int(rates['EUR_to_USD'].isna().sum())
rates['EUR_to_USD'] = rates['EUR_to_USD'].ffill()
# Guard against leading missing values that forward-fill cannot resolve.
if rates['EUR_to_USD'].isna().any():
    rates['EUR_to_USD'] = rates['EUR_to_USD'].bfill()

# Left join ensures no valid parsed transaction is lost at the FX stage.
with_rates = extracted_data.merge(rates, on='Date', how='left', validate='many_to_one')
if with_rates['EUR_to_USD'].isna().any():
    raise ValueError('Exchange rates are missing for one or more transaction dates.')

# Reconcile only to users whose latest account status is Active.
df_final = with_rates.merge(
    df_active_users[['user_id','name','status','updated_at']],
    left_on='User_ID', right_on='user_id', how='inner', validate='many_to_one'
)
df_final['USD_Revenue'] = df_final['EUR_Value'] * df_final['EUR_to_USD']
df_final['Month'] = df_final['Date'].dt.to_period('M').astype(str)
df_final.to_csv(OUT / 'final_reconciled_transactions.csv', index=False)

# PHASE 4 — Aggregations
monthly_revenue = (df_final.groupby('Month', as_index=False)['USD_Revenue']
                   .sum().sort_values('Month'))
monthly_revenue['USD_Revenue'] = monthly_revenue['USD_Revenue'].round(2)
monthly_revenue.to_csv(OUT / 'monthly_revenue.csv', index=False)

top_customers = (df_final.groupby(['User_ID','name'], as_index=False)['USD_Revenue']
                 .sum().sort_values('USD_Revenue', ascending=False).head(5))
top_customers['USD_Revenue'] = top_customers['USD_Revenue'].round(2)
top_customers.to_csv(OUT / 'top_5_customers.csv', index=False)

# Dashboard charts
plt.rcParams.update({'font.size': 10})
fig, axes = plt.subplots(1, 2, figsize=(14, 5.6))
axes[0].plot(monthly_revenue['Month'], monthly_revenue['USD_Revenue'] / 1_000_000, marker='o', linewidth=2)
axes[0].set_title('Monthly Reconciled Revenue (USD)')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Revenue (USD millions)')
axes[0].tick_params(axis='x', rotation=45)
axes[0].grid(True, alpha=0.25)
axes[1].barh(top_customers['name'][::-1], top_customers['USD_Revenue'][::-1] / 1000)
axes[1].set_title('Top 5 Customers by USD Revenue')
axes[1].set_xlabel('Revenue (USD thousands)')
axes[1].set_ylabel('Customer')
axes[1].grid(axis='x', alpha=0.25)
fig.suptitle('Enterprise Data Reconciliation — CFO Dashboard', fontsize=14, fontweight='bold')
fig.tight_layout()
fig.savefig(OUT / 'cfo_dashboard.png', dpi=180, bbox_inches='tight')
plt.close(fig)

# Additional concise metrics for report and QA
all_user_count = 0
with sqlite3.connect(DB) as conn:
    all_user_count = conn.execute('SELECT COUNT(DISTINCT user_id) FROM users').fetchone()[0]
    historical_rows = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
metrics = {
    'raw_log_records': int(len(raw_logs)),
    'error_log_records_excluded': error_count,
    'non_error_log_records': int((~error_mask).sum()),
    'parsed_valid_transactions': int(len(extracted_data)),
    'unparsed_non_error_records': int((~error_mask).sum() - len(extracted_data)),
    'historical_user_records': int(historical_rows),
    'distinct_users_in_database': int(all_user_count),
    'latest_active_users': int(len(df_active_users)),
    'exchange_rate_days': int(len(rates)),
    'missing_exchange_rates_filled': missing_rates_before,
    'transactions_after_active_user_reconciliation': int(len(df_final)),
    'unique_active_customers_with_transactions': int(df_final['User_ID'].nunique()),
    'total_reconciled_usd_revenue': round(float(df_final['USD_Revenue'].sum()), 2),
    'processing_seconds': round(time.perf_counter() - start, 3),
}
(OUT / 'project_metrics.json').write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics, indent=2))
print('\nMONTHLY REVENUE\n', monthly_revenue.to_string(index=False))
print('\nTOP CUSTOMERS\n', top_customers.to_string(index=False))
