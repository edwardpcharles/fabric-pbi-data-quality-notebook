"""
Data Quality Configuration

This file should be placed in your Fabric Lakehouse at:
  /Files/code/config.py

Then imported in notebooks using:
  import sys
  sys.path.append("/lakehouse/default/Files/code")
  from config import LAKEHOUSE_NAME, SCHEMA_NAME, MAX_RETRY_ATTEMPTS, ...

Edit values here to control environment and shared runtime behavior globally.
Row-level fail thresholds are stored in check_registry.fail_delta_pct_threshold, not here.
"""

# Environment
LAKEHOUSE_NAME = "MyLakehouse"
SCHEMA_NAME = "data_quality"

# Validation retry and execution behavior
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 2
DAX_TIMEOUT_SECONDS = 60

# Maintenance behavior
RUN_TABLE_MAINTENANCE = False
MAINTENANCE_DAY_UTC = 6

# Derived (computed)
FULL_SCHEMA = f"{LAKEHOUSE_NAME}.{SCHEMA_NAME}"
