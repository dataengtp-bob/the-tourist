from datetime import datetime
import os
import requests
import zipfile
import pandas as pd
from ingest_raw import STOPS_DIR, GTFS_DIR

STAGING_DIR = "data/staging"

def clean_stops():
    df = pd.read_csv(f"{STOPS_DIR}/gares-de-voyageurs.csv")

    df = df.rename(columns={
        "id": "stop_id",
        "nom": "name",
        "commune": "city",
        "lat": "lat",
        "lon": "lon"
    })

    df = df[["stop_id", "name", "city", "lat", "lon"]]
    df = df.drop_duplicates(subset=["stop_id"])
    df = df.dropna(subset=["stop_id", "lat", "lon"])

    df.to_parquet(f"{STAGING_DIR}/stops_staging.parquet", index=False)

def clean_stop_times():
    df = pd.read_csv(f"{GTFS_DIR}/stop_times.txt")

    df = df[["trip_id", "stop_id", "stop_sequence"]]
    df = df.dropna(subset=["trip_id", "stop_id", "stop_sequence"])
    df["stop_sequence"] = df["stop_sequence"].astype(int)
    df = df.sort_values(["trip_id", "stop_sequence"])

    df.to_parquet(f"{STAGING_DIR}/stop_times_clean.parquet", index=False)

def clean_trips():
    trips_path = f"{GTFS_DIR}/trips.txt"
    if not os.path.exists(trips_path):
        return

    df = pd.read_csv(trips_path)
    df = df[["trip_id", "route_id"]].drop_duplicates()

    df.to_parquet(f"{STAGING_DIR}/trips_staging.parquet", index=False)

def enrich_and_persist():
    stops = pd.read_parquet(f"{STAGING_DIR}/stops_staging.parquet")
    stop_times = pd.read_parquet(f"{STAGING_DIR}/stop_times_clean.parquet")

    enriched = stop_times.merge(stops, on="stop_id", how="inner")

    enriched.to_parquet(
        f"{STAGING_DIR}/stop_times_staging.parquet",
        index=False
    )
