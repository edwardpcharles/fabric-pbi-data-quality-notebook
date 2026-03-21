# Data Quality Validation System

Monitor semantic model consistency across your Fabric workspace. This system validates that the same metrics return the same values across multiple models, and alerts you when they diverge.

## Problem Solved

You manage 100+ reports across multiple semantic models. The same metric (e.g., "Total Sales") may be named differently in each model (`[Sales Amount]`, `[Total Revenue]`, `[Net Sales]`). You need daily validation that all models tie, even with these name differences.

Instead of manually comparing values, this system:
- Registers which DAX expression calculates each metric in each model
- Runs them daily and compares results
- Stores pass/fail history in a table
- Allows crash recovery and multiple runs per day

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│ Your Semantic Models (Finance, Sales AMER, Sales EMEA)  │
└────────────────────────┬────────────────────────────────┘
                         │ (DAX queries)
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Daily Validation Job (data_quality_validation_job)      │
│ - Load registered checks                                │
│ - Execute DAX for each model                            │
│ - Compare to baseline                                   │
│ - Write results                                         │
│ - Maintain tables                                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Lakehouse Tables (data_quality schema)                  │
│ - check_registry (what to validate)                     │
│ - validation_results (pass/fail history)                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Query results    │
              │ Find failures    │
              └──────────────────┘
```

---

## Getting Started (5 minutes)

### 1. Run Setup (One-Time)

Open **`data_quality_setup_notebook.ipynb`** in Fabric:

1. Change `LAKEHOUSE_NAME` to your existing Lakehouse (e.g., `"MyLakehouse"`)
2. (Optional) Change `SCHEMA_NAME` if you prefer a different schema name
3. **Run All** — creates two tables: `check_registry` and `validation_results`

✓ Done. Your tables are ready.

### 2. Register Your First Checks

Open **`data_quality_add_checks_notebook.ipynb`**:

1. Set `LAKEHOUSE_NAME` and `SCHEMA_NAME` to match above
2. Find the `checks = [...]` list (around line 20)
3. Add one row per model per metric:

```python
checks = [
    # (check_name,         model_name,       workspace_name,       dataset_name,         dax_expression,                            run_frequency)
    ("Total Sales",        "Finance",        "Finance WS",         "Finance Model",      'EVALUATE ROW("value", [Sales Amount])',  "ONCE_PER_DAY"),
    ("Total Sales",        "Sales AMER",     "Sales WS",           "Sales AMER Model",   'EVALUATE ROW("value", [Total Revenue])',"ONCE_PER_DAY"),
    ("Total Sales",        "Sales EMEA",     "Sales WS",           "Sales EMEA Model",   'EVALUATE ROW("value", [Net Sales])',    "ONCE_PER_DAY"),
]
```

**Key Rules:**
- **check_name** must be identical across all models for that metric (e.g., "Total Sales")
- **DAX expression** must return a **single number**, e.g. `EVALUATE ROW("value", [Sales Amount])`
- **run_frequency**: 
  - `"ONCE_PER_DAY"` (default) — check runs max once per calendar day
  - `"MULTIPLE_PER_DAY"` — can execute this check multiple times per day
- The **first model listed** for each check_name becomes the baseline for comparison

4. **Run All** — checks are registered

✓ You now have 3 checks registered.

### 3. Run the Daily Job (Manually or Scheduled)

Open **`data_quality_validation_job_notebook.ipynb`**:

1. Set `LAKEHOUSE_NAME` and `SCHEMA_NAME`
2. **Run All**

The job will:
- Load your checks from `check_registry`
- Execute each DAX expression
- Compare all models to their baseline
- Write results to `validation_results` with PASS/FAIL/ERROR status
- Show failures at the end
- Automatically maintain (optimize, vacuum, analyze) the tables

✓ Results are in the table.

**To Schedule Daily:**
In Fabric, create a Job Scheduler → select this notebook → set to run daily at your preferred time.

---

## Notebooks Reference

### `data_quality_setup_notebook.ipynb`
**Purpose:** One-time initialization  
**When to run:** Once when you first set up the system  
**What it does:**
- Creates the `data_quality` schema
- Creates `check_registry` table (where you put your checks)
- Creates `validation_results` table (where results are stored)

**Config:**
```python
LAKEHOUSE_NAME = "MyLakehouse"   # Your existing Lakehouse
SCHEMA_NAME    = "data_quality"  # New schema to create
```

---

### `data_quality_add_checks_notebook.ipynb`
**Purpose:** Register and update checks  
**When to run:** Anytime you want to add, change, or enable checks  
**What it does:**
- Edit the `checks = [...]` list with your model names and DAX expressions
- UPSERT them into `check_registry` (safe to re-run — won't create duplicates)
- Show you what's registered

**Key Column:** `run_frequency`
- `"ONCE_PER_DAY"` — skips if already ran today
- `"MULTIPLE_PER_DAY"` — allows multiple runs per day

**Safe to re-run anytime** — it only updates changed rows.

---

### `data_quality_delete_checks_notebook.ipynb`
**Purpose:** Manage (deactivate or delete) checks  
**When to run:** When you want to stop validating a check  
**What it does:**
- Shows all registered checks
- Lets you soft-delete (set `is_active = false`) or hard-delete (remove permanently)
- Shows remaining active checks

**Options:**
```python
DELETE_METHOD = "soft"  # "soft" (is_active=false) or "hard" (permanent delete)
```

**Soft delete is safer** — keeps historical data but won't run in future jobs.

---

### `data_quality_validation_job_notebook.ipynb`
**Purpose:** Daily validation execution  
**When to run:** Every day (schedule in Fabric Job Scheduler)  
**What it does:**
1. Loads all active checks from `check_registry`
2. Skips checks that already ran today (if `run_frequency = "ONCE_PER_DAY"`)
3. Executes each DAX expression for each model
4. Compares results to the baseline (first model for that check)
5. Writes PASS/FAIL/ERROR to `validation_results`
6. Shows summary of failures
7. Optimizes tables (consolidates small files, removes old versions, computes stats)

**Key Features:**
- **Crash-safe:** If it fails partway, re-run it and it picks up where it left off
- **Idempotent:** Won't duplicate results if run twice
- **Incremental writes:** Each result is written immediately (not batched)
- **Automatic maintenance:** OPTIMIZE, VACUUM, ANALYZE run every day

**Error Handling:**
- Bad DAX expressions → captured as ERROR status with error message
- Empty results → ERROR with "DAX returned empty result"
- Execution continues on errors (doesn't stop the whole job)

---

### `power_bi_queries_notebook.ipynb`
**Purpose:** Sample SQL queries for Power BI analytics  
**When to use:** When building dashboards in Power BI Desktop  
**What it contains:**
- **Dimension tables:** Models, Checks, Calendar dates
- **Fact tables:** All validation results, failures only, daily trends with pass rates
- **Power BI setup guide:** Connection steps, relationship mapping, visualization suggestions

**Included Queries:**
- `Dim_Models` — List all models with baseline markers
- `Dim_Checks` — List all registered checks with model counts
- `Dim_Date` — Calendar dimension with year/month/day-of-week
- `Fact_ValidationResults` — All results with computed flags (is_pass, is_fail, is_error, abs_delta_pct)
- `Fact_Failures` — Subset of results where status = FAIL or ERROR
- `Fact_Trends` — Daily aggregated results: pass_count, fail_count, error_count, pass_rate_pct

**How to use:**
1. Open the notebook in Fabric
2. Copy any SQL query that interests you
3. Paste into Power BI Desktop → New Source → SQL
4. Load the data and create relationships based on `check_name` and `run_date`
5. Build dashboards with cards (pass rate %), tables (failures), trends (line charts)

**Sample Visualizations:**
- Health Dashboard: Pass rate % card, trend line by date
- Failure Detail: Table of failed checks with delta values
- Model Comparison: Matrix of checks × models
- Trend Analysis: Pass rate over time, sliced by check or model

---

## Querying Results

Once the validation job runs, results are in `validation_results`. You can query them in a notebook:

### View Today's Results
```sql
SELECT check_name, model_name, result_value, baseline_value, delta_pct, status
FROM MyLakehouse.data_quality.validation_results
WHERE run_date = CAST(CURRENT_DATE() AS DATE)
ORDER BY check_name, model_name
```

### View Failures Only
```sql
SELECT check_name, model_name, result_value, baseline_value, delta_pct, status, error_message
FROM MyLakehouse.data_quality.validation_results
WHERE run_date = CAST(CURRENT_DATE() AS DATE) AND status != 'PASS'
```

### View Trend (Last 7 Days)
```sql
SELECT check_name, model_name, run_date, status, result_value, baseline_value, delta_pct
FROM MyLakehouse.data_quality.validation_results
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY check_name, model_name, run_date DESC
```

### View a Specific Run
```sql
SELECT * FROM MyLakehouse.data_quality.validation_results
WHERE run_id = '12345678-abcd-1234-abcd-1234567890ab'
```

---

## How It Works

### Comparison Logic

1. **Baseline:** For each `check_name`, the first `model_name` listed in `check_registry` is the baseline.
   
2. **Delta Calculation:**
   ```
   absolute_delta = result_value - baseline_value
   relative_pct   = (absolute_delta / baseline_value) * 100
   ```

3. **Pass/Fail Threshold:**
   - PASS: `|relative_pct| <= 0.01%` (i.e., nearly identical)
   - FAIL: `|relative_pct| > 0.01%`
   - ERROR: DAX expression threw an exception or returned empty

### Crash Recovery

If the job crashes partway:

```
Run started... 
  ✓ Check A (Finance)
  ✓ Check A (Sales AMER)
  ✓ Check B (Finance)
  ✗ Connection timeout
```

Just re-run the job. It will:
1. Check what already ran today (by comparing `run_date`)
2. Skip checks with `ONCE_PER_DAY` that already have results
3. Continue with remaining checks and complete the run

### Multiple Runs Per Day

If you set a check to `MULTIPLE_PER_DAY`, the job **won't skip it** on re-runs. This is useful for:
- Real-time metrics (e.g., orders processed)
- Testing (validating models multiple times while changing them)
- High-frequency validation (multiple runs per day on a schedule)

---

## Configuration Reference

### check_registry Columns

| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| check_name | STRING | ✓ | "Total Sales" | Must be identical across all models for that metric |
| model_name | STRING | ✓ | "Finance GAAP" | Your label for this model |
| workspace_name | STRING | ✓ | "Finance Workspace" | Fabric workspace name |
| dataset_name | STRING | ✓ | "Finance Model" | Semantic model name |
| dax_expression | STRING | ✓ | `EVALUATE ROW("value", [Sales Amount])` | Must return single number |
| run_frequency | STRING | ✓ | "ONCE_PER_DAY" | "ONCE_PER_DAY" or "MULTIPLE_PER_DAY" |
| is_active | BOOLEAN | ✓ | true | Set to false to skip without deleting |

### validation_results Columns

| Column | Type | Purpose |
|--------|------|---------|
| run_id | STRING | UUID identifying this run (for crash recovery) |
| run_date | DATE | Calendar date (partition key) |
| run_timestamp | TIMESTAMP | Exact time of execution |
| check_name | STRING | The metric being validated |
| model_name | STRING | Which model this result is for |
| result_value | DOUBLE | The DAX result for this model |
| baseline_model | STRING | Name of the baseline model |
| baseline_value | DOUBLE | The DAX result for baseline |
| absolute_delta | DOUBLE | result_value - baseline_value |
| delta_pct | DOUBLE | (absolute_delta / baseline_value) × 100 |
| status | STRING | PASS / FAIL / ERROR |
| error_message | STRING | Exception message if ERROR |

---

## Troubleshooting

### Job Fails with "Bad DAX Expression"
- Check the error message in `validation_results` table (`error_message` column)
- Verify the DAX works in Power BI or Analysis Services directly
- Common issue: referencing measure/column names that don't exist in that model

### Job Takes Too Long
- Too many checks? (if you have 100s, consider batching runs)
- DAX queries are slow? Optimize them in your semantic models
- First-time run includes OPTIMIZE/VACUUM — subsequent runs are faster

### Job Silently Completes but No Results
- Check `run_timestamp` — did it actually run today?
- Check `is_active = true` in `check_registry` — maybe all checks are deactivated?
- Review `error_message` column — the job may have errored on baseline execution

### Same Metric Different Names Across Models
- This is intentional! Register them with the same `check_name`:
  ```python
  ("Total Sales", "Finance", ..., 'EVALUATE ROW("value", [Sales Amount])'),
  ("Total Sales", "Sales AMER", ..., 'EVALUATE ROW("value", [Total Revenue])'),
  ```
  The job compares both to Finance's value automatically.

### Want to Re-Validate Today
- If check is `ONCE_PER_DAY`: Change it to `MULTIPLE_PER_DAY`, re-run job, change back
- Or: Query and delete results from today manually, then re-run job

---

## Next Steps

1. **Add 3-5 key metrics** you validate manually today
2. **Schedule the validation job** to run daily (e.g., 6am)
3. **Share the results table** with your team (they can query `validation_results`)
4. **Optional — Build Power BI Dashboard:** 
   - Open `power_bi_queries_notebook.ipynb` in Fabric
   - Copy the dimension and fact queries to Power BI Desktop
   - Connect to OneLake and load the tables
   - Create relationships and build visualizations for a live health dashboard

---

## Architecture Notes

**Why this design?**

- **Lakehouse Delta tables:** Immutable history, easy to partition by date, integrates with Fabric job scheduler
- **Incremental writes:** Each result written immediately, so crashes don't lose partial progress
- **ONCE_PER_DAY default:** Avoids redundant re-runs while supporting high-frequency validation
- **Soft delete:** Lets you pause checks without losing history
- **Automatic maintenance:** OPTIMIZE/VACUUM keep table lean without manual intervention
- **run_id for idempotency:** Multiple runs of the same job don't create duplicates

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the DAX expressions in Power BI directly to ensure they work
- Verify Fabric workspace credentials are valid
- Check notebook error logs for detailed error messages

---

**Version:** 1.0  
**Last Updated:** March 20, 2026
