"""Shared configuration for Data Quality notebooks.

Keep environment-specific values in one place and import from notebooks.
"""

LAKEHOUSE_NAME = "MyLakehouse"
SCHEMA_NAME = "data_quality"

DELTA_PCT_THRESHOLD = 0.01
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 2
DAX_TIMEOUT_SECONDS = 60

RUN_TABLE_MAINTENANCE = False
MAINTENANCE_DAY_UTC = 6


def full_schema(lakehouse_name: str = LAKEHOUSE_NAME, schema_name: str = SCHEMA_NAME) -> str:
    return f"{lakehouse_name}.{schema_name}"
