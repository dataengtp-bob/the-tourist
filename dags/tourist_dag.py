from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import timedelta
import pendulum
import logging
from helpers.ingest_raw import (
    download_sncf_stations_csv,
    download_and_extract_sncf_gtfs,
)
from helpers.clean_data import (
    clean_and_stage_stations,
    clean_and_stage_stop_times,
)

logger = logging.getLogger(__name__)  # Airflow captures this per task
output_folder = "/opt/airflow/data"  # ensure this folder exists and is writable


# --- Failure callback for rich console logs ---
def failure_alert(context):
    exc = context.get("exception")
    ti = context.get("ti")
    logger.error(
        "Task FAILED: dag=%s task=%s run_id=%s try=%s",
        getattr(ti, "dag_id", "?"),
        getattr(ti, "task_id", "?"),
        context.get("run_id"),
        getattr(ti, "try_number", "?"),
    )
    # Full traceback in the task log:
    logger.exception(exc)


# --- DAG config ---
START_DATE = pendulum.datetime(2024, 1, 1, tz="UTC")

with DAG(
    dag_id="tourist_dag",
    start_date=START_DATE,
    schedule="0 0 * * *",  # daily at 00:00 UTC
    catchup=False,
    max_active_tasks=1,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": failure_alert,
    },
    template_searchpath=["/opt/airflow/data/"],
    tags=["example"],
) as dag:

    start = EmptyOperator(task_id="start")

    download_stations_task = PythonOperator(
        task_id="download_sncf_stations", python_callable=download_sncf_stations_csv
    )

    download_gtfs_task = PythonOperator(
        task_id="download_sncf_gtfs", python_callable=download_and_extract_sncf_gtfs
    )

    stage_stations_task = PythonOperator(
        task_id="stage_stations", python_callable=clean_and_stage_stations
    )

    stage_stop_times_task = PythonOperator(
        task_id="stage_stop_times", python_callable=clean_and_stage_stop_times
    )

    end = EmptyOperator(task_id="end")

    # -------- Graph --------
    start >> [download_stations_task, download_gtfs_task]

    download_gtfs_task >> stage_stop_times_task
    download_stations_task >> stage_stations_task

    [stage_stations_task, stage_stop_times_task] >> end
