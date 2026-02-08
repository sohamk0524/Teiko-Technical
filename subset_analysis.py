"""
Part 4: Data Subset Analysis
- Identify melanoma PBMC baseline samples treated with miraclib
- Breakdown by project, response, and sex
"""

import os
import pandas as pd

from database import get_connection, init_and_load, DB_PATH

BASELINE_SAMPLES_SQL = """
SELECT
    s.sample_id,
    s.subject_id,
    s.project,
    s.treatment,
    s.response,
    s.sample_type,
    s.time_from_treatment_start,
    sub.condition,
    sub.sex
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
  AND s.treatment = 'miraclib';
"""

SAMPLES_PER_PROJECT_SQL = """
SELECT s.project, COUNT(*) AS sample_count
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
  AND s.treatment = 'miraclib'
GROUP BY s.project
ORDER BY s.project;
"""

RESPONDERS_SQL = """
SELECT s.response, COUNT(DISTINCT s.subject_id) AS subject_count
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
  AND s.treatment = 'miraclib'
GROUP BY s.response;
"""

SEX_SQL = """
SELECT sub.sex, COUNT(DISTINCT s.subject_id) AS subject_count
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
  AND s.treatment = 'miraclib'
GROUP BY sub.sex;
"""


def get_baseline_samples(conn):
    """Return all melanoma PBMC baseline samples treated with miraclib."""
    return pd.read_sql_query(BASELINE_SAMPLES_SQL, conn)


def get_samples_per_project(conn):
    """Return sample counts per project for the baseline subset."""
    return pd.read_sql_query(SAMPLES_PER_PROJECT_SQL, conn)


def get_response_breakdown(conn):
    """Return responder/non-responder subject counts for the baseline subset."""
    return pd.read_sql_query(RESPONDERS_SQL, conn)


def get_sex_breakdown(conn):
    """Return male/female subject counts for the baseline subset."""
    return pd.read_sql_query(SEX_SQL, conn)


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        conn = init_and_load()
    else:
        conn = get_connection()

    pd.set_option("display.width", 140)
    pd.set_option("display.max_rows", 30)

    baseline = get_baseline_samples(conn)
    print(f"=== Melanoma PBMC Baseline Samples (miraclib) ===")
    print(f"Total samples: {len(baseline)}")
    print(f"Total unique subjects: {baseline['subject_id'].nunique()}\n")
    print(baseline.head(10).to_string(index=False))
    print("...\n")

    print("=== Samples per Project ===")
    print(get_samples_per_project(conn).to_string(index=False))

    print("\n=== Responders vs Non-Responders (unique subjects) ===")
    print(get_response_breakdown(conn).to_string(index=False))

    print("\n=== Sex Breakdown (unique subjects) ===")
    print(get_sex_breakdown(conn).to_string(index=False))

    conn.close()
