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
from helpers.neo4j_loader import (
    create_constraints,
    load_stations,
    load_trips,
    link_origin_destination,
    create_next_stop_chain,
    clear_database,
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
    dag_id="trains_dag",
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

    # --- Neo4j loading tasks (Production Zone) ---
    clear_neo4j_task = PythonOperator(
        task_id="clear_neo4j_database", python_callable=clear_database
    )

    neo4j_constraints_task = PythonOperator(
        task_id="create_neo4j_constraints", python_callable=create_constraints
    )

    load_stations_neo4j_task = PythonOperator(
        task_id="load_stations_to_neo4j", python_callable=load_stations
    )

    load_trips_neo4j_task = PythonOperator(
        task_id="load_trips_to_neo4j", python_callable=load_trips
    )

    link_endpoints_task = PythonOperator(
        task_id="link_trip_endpoints", python_callable=link_origin_destination
    )

    next_stop_chain_task = PythonOperator(
        task_id="create_next_stop_chain", python_callable=create_next_stop_chain
    )

    end = EmptyOperator(task_id="end")

    # -------- Graph --------
    # Landing zone
    start >> [download_stations_task, download_gtfs_task]

    # Staging zone
    download_gtfs_task >> stage_stop_times_task
    download_stations_task >> stage_stations_task

    # Production zone (Neo4j)
    [stage_stations_task, stage_stop_times_task] >> clear_neo4j_task
    clear_neo4j_task >> neo4j_constraints_task
    neo4j_constraints_task >> load_stations_neo4j_task
    load_stations_neo4j_task >> load_trips_neo4j_task
    load_trips_neo4j_task >> link_endpoints_task
    link_endpoints_task >> next_stop_chain_task
    next_stop_chain_task >> end
