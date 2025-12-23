from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import timedelta
import pendulum
import logging
from helpers.ingest_raw import ingest_train_stops, ingest_gtfs
from helpers.clean_data import clean_stops, clean_stop_times, clean_trips, enrich_and_persist   

logger = logging.getLogger(__name__)  # Airflow captures this per task
output_folder = "/opt/airflow/data"   # ensure this folder exists and is writable

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
    schedule="0 0 * * *",         # daily at 00:00 UTC
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

    ingest_stations = PythonOperator(
        task_id="ingest_sncf_train_stations",
        python_callable=ingest_train_stops
    )

    ingest_gtfs = PythonOperator(
        task_id="ingest_sncf_gtfs",
        python_callable=ingest_gtfs
    )

    end_ingest = EmptyOperator(task_id="end_ingest")

    clean_stops_task = PythonOperator(
        task_id="clean_stops",
        python_callable=clean_stops
    )

    clean_stop_times_task = PythonOperator(
        task_id="clean_stop_times",
        python_callable=clean_stop_times
    )

    clean_trips_task = PythonOperator(
        task_id="clean_trips",
        python_callable=clean_trips
    )

    enrich_task = PythonOperator(
        task_id="enrich_and_persist_staging",
        python_callable=enrich_and_persist
    )

    end = EmptyOperator(task_id="end")

    # -------- Graph --------
    start >> [ingest_stations, ingest_gtfs]

    ingest_gtfs >> [clean_stop_times_task, clean_trips_task]
    ingest_stations >> clean_stops_task

    [clean_stops_task, clean_stop_times_task] >> enrich_task
    enrich_task >> end