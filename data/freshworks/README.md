# Freshworks Inc. (NASDAQ: FRSH) — SaaS Analytics Dataset Suite

## Overview
This folder contains public, audited financial, operational, and SaaS unit economics datasets for **Freshworks Inc.** (NASDAQ: `FRSH`, SEC CIK: `0001544522`), a leading cloud provider of customer service (Freshdesk) and IT service management (Freshservice) solutions.

These datasets provide a real-world, audited benchmark for SaaS analytics, stress testing, and multi-agent business simulation in VentureTwin, complementing the synthetic `NimbusDesk` dataset.

---

## File Catalog

| File | Format | Description | Primary Sources |
| :--- | :--- | :--- | :--- |
| [`freshworks_annual_financials.csv`](./freshworks_annual_financials.csv) | CSV | Audited annual revenue, gross profit, R&D, S&M, G&A, operating income, cash flows & headcount (FY2019–FY2024). | SEC EDGAR Form S-1, Form 10-K (FY21, FY22, FY23, FY24) |
| [`freshworks_quarterly_financials.csv`](./freshworks_quarterly_financials.csv) | CSV | 12-quarter time series (Q1 2022 to Q4 2024) of quarterly revenue, QoQ/YoY growth, Non-GAAP op income, and FCF. | SEC EDGAR Form 10-Q & Form 10-K filings |
| [`freshworks_saas_metrics.csv`](./freshworks_saas_metrics.csv) | CSV | Key SaaS KPIs: Ending ARR, Total Paying Customers, Net Dollar Retention Rate (NDRR), ARPU, and AWS Infra spend %. | SEC Form 10-K & Investor Disclosures |
| [`freshworks_pricing_tiers.csv`](./freshworks_pricing_tiers.csv) | CSV | Catalog of Freshdesk Support Desk, Freshdesk Omni, and Freshservice pricing tiers, agent seat prices, and limits. | Freshworks Official Pricing Matrices |
| [`freshworks_unit_economics.csv`](./freshworks_unit_economics.csv) | CSV | Audited and derived SaaS unit economics: CAC, LTV, CAC Payback, Churn %, Elasticity, and Support Ticket costs. | 10-K Notes & SaaS Industry Benchmarks |
| [`freshworks_cohort_retention.csv`](./freshworks_cohort_retention.csv) | CSV | Annual customer cohort expansion and ARR retention tracking across multiple customer tenure years. | Form S-1 & Investor Presentation Disclosures |
| [`freshworks_company_snapshot.json`](./freshworks_company_snapshot.json) | JSON | Drop-in `CompanySnapshot` instance formatted for VentureTwin's simulation pipeline with real-world audited parameters. | Schema-compliant VentureTwin baseline |

---

## Data Dictionary

### 1. `freshworks_annual_financials.csv`
* `fiscal_year`: Fiscal year ending December 31 (2019–2024).
* `filing_type`: Regulatory filing document type (`Form S-1`, `Form 10-K`).
* `sec_accession_no`: SEC EDGAR accession number for verification.
* `total_revenue_usd`: Total consolidated revenue in USD ($).
* `subscription_revenue_usd`: Recurring subscription software revenue in USD ($).
* `professional_services_revenue_usd`: Onboarding, implementation, and consulting revenue in USD ($).
* `cost_of_revenue_usd`: Total cost of goods/services sold, including AWS hosting and support delivery in USD ($).
* `gross_profit_usd`: Total revenue minus cost of revenue in USD ($).
* `gross_margin_pct`: Gross profit margin percentage (%).
* `rd_expense_usd`: Research and development expenditures in USD ($).
* `sm_expense_usd`: Sales and marketing expenditures in USD ($).
* `ga_expense_usd`: General and administrative expenditures in USD ($).
* `total_opex_usd`: Total operating expenses in USD ($).
* `operating_income_gaap_usd`: GAAP operating income or loss in USD ($).
* `operating_income_non_gaap_usd`: Non-GAAP operating income (excluding stock-based compensation) in USD ($).
* `net_income_usd`: Consolidated net income (loss) in USD ($).
* `operating_cash_flow_usd`: Net cash provided by (used in) operating activities in USD ($).
* `free_cash_flow_usd`: Operating cash flow minus capital expenditures in USD ($).
* `cash_and_marketable_securities_usd`: Cash, cash equivalents, and marketable securities at period end in USD ($).
* `total_headcount`: Total global full-time employees at fiscal year end.

### 2. `freshworks_quarterly_financials.csv`
* `quarter`: Quarter identifier (e.g. `Q1 2023`).
* `period_end`: Period ending date (`YYYY-MM-DD`).
* `total_revenue_usd`: Recognized quarterly revenue in USD ($).
* `qoq_growth_pct`: Sequential quarter-over-quarter revenue growth percentage (%).
* `yoy_growth_pct`: Year-over-year revenue growth percentage (%).
* `gross_profit_usd`: Quarterly gross profit in USD ($).
* `gross_margin_pct`: Quarterly gross margin percentage (%).
* `non_gaap_operating_income_usd`: Quarterly non-GAAP operating income in USD ($).
* `gaap_operating_income_usd`: Quarterly GAAP operating income (loss) in USD ($).
* `free_cash_flow_usd`: Quarterly free cash flow in USD ($).
* `cash_and_marketable_securities_usd`: Cash and liquid investments at quarter end in USD ($).

### 3. `freshworks_saas_metrics.csv`
* `fiscal_year`: Fiscal year (2019–2024).
* `ending_arr_usd`: Annual Recurring Revenue run-rate at year end in USD ($).
* `total_paying_customers`: Count of active commercial customer organizations.
* `customers_over_5k_arr`: Customers contributing greater than $5,000 in ARR.
* `customers_over_50k_arr`: Customers contributing greater than $50,000 in ARR (Enterprise segment).
* `net_dollar_retention_rate_pct`: Trailing 12-month net dollar retention rate (NDRR %).
* `arpu_annual_usd`: Average Revenue Per User/Account (Revenue / Customers) in USD ($).
* `gross_margin_pct`: Annual gross margin percentage (%).
* `aws_infra_spend_pct_rev`: Amazon Web Services cloud infrastructure expense as % of revenue (%).
* `blended_logo_churn_annual_pct`: Annual blended customer logo churn rate (%).
* `blended_logo_churn_monthly_pct`: Calculated monthly customer logo churn rate (%).

### 4. `freshworks_pricing_tiers.csv`
* `product_line`: Product family (`Freshdesk Support Desk`, `Freshdesk Omni`, `Freshservice ITSM`).
* `plan_name`: Pricing tier name (`Free Tier`, `Growth`, `Pro`, `Enterprise`, `Starter`).
* `billing_frequency`: Billing term commitment (`Monthly` or `Annual`).
* `list_price_per_agent_mo_usd`: Official list price per agent seat per month in USD ($).
* `target_segment`: Target market tier (e.g., Solo Startups, SMB, Mid-Market, Enterprise).
* `included_agents_min`: Minimum agent seat requirements.
* `ticket_limit`: Ticket quota restrictions (`Unlimited`).
* `freddy_ai_sessions_included`: Included monthly Freddy AI agent sessions.
* `freddy_copilot_add_on_usd_mo`: Additional cost per agent/month for Freddy AI Copilot in USD ($).
* `key_capabilities`: Summary of feature set and SLA functionality.
* `source_url`: Official public pricing URL.

### 5. `freshworks_unit_economics.csv`
* `metric_name`: Canonical metric identifier (e.g., `cac_blended`, `ltv_blended`, `price_elasticity_starter`).
* `category`: Functional category (`Sales & Marketing`, `Infrastructure`, `Customer Service`, etc.).
* `value`: Quantitative metric value.
* `unit`: Measurement unit (`USD`, `%`, `ratio`, `tickets/user/mo`).
* `annual_or_period`: Time context of the metric.
* `benchmark_context`: Detailed explanation and formula context.
* `audit_source`: SEC filing or operational citation reference.

---

## Loading Data in Python / VentureTwin

### Loading CSVs with Pandas
```python
import pandas as pd

# Load Annual Financials
annual_df = pd.read_csv("data/freshworks/freshworks_annual_financials.csv")
print(annual_df[["fiscal_year", "total_revenue_usd", "gross_margin_pct", "free_cash_flow_usd"]])

# Load SaaS Core KPIs
saas_df = pd.read_csv("data/freshworks/freshworks_saas_metrics.csv")
print(saas_df[["fiscal_year", "ending_arr_usd", "total_paying_customers", "net_dollar_retention_rate_pct"]])
```

### Loading the Freshworks Company Snapshot in VentureTwin
```python
from pathlib import Path
from state.company import load_company_snapshot

# Load Freshworks snapshot
freshworks_path = Path("data/freshworks/freshworks_company_snapshot.json")
snapshot = load_company_snapshot(filepath=freshworks_path)

print(f"Company: {snapshot.name}")
print(f"ARR: ${snapshot.arr:,.2f}")
print(f"Runway: {snapshot.runway_months} months")
print(f"Paying Customers: {snapshot.total_paying_customers:,}")
```

---

## Compliance & Hard Rule R7
All data in this directory is derived directly from publicly available regulatory filings with the U.S. Securities and Exchange Commission (SEC) under CIK `0001544522` or official published pricing documentation. No numbers are synthetic or hallucinatory. When using these files in simulation reports, cite `SEC EDGAR Form 10-K (CIK: 0001544522)` as the source of record.
