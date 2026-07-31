from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path("/opt/airflow/project")
sys.path.append(str(PROJECT_ROOT / "src"))

from warehouse_etl import run_pipeline  # noqa: E402


default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="netflix_analytics_warehouse_etl",
    description="Load Netflix analytics CSV data into PostgreSQL warehouse and marts.",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["netflix", "analytics", "warehouse"],
) as dag:
    load_warehouse = PythonOperator(
        task_id="load_postgres_warehouse",
        python_callable=run_pipeline,
    )
