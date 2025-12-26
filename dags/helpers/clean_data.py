import os
import pandas as pd

STAGING_DIR = "data/staging"
LANDING_DIR = "data/landing"
STOPS_DIR = f"{LANDING_DIR}/stations"
GTFS_DIR = f"{LANDING_DIR}/gtfs"


def create_staging_directories():
    os.makedirs(STOPS_DIR, exist_ok=True)
    os.makedirs(GTFS_DIR, exist_ok=True)
    os.makedirs(STAGING_DIR, exist_ok=True)


def clean_and_stage_stations():
    create_staging_directories()
    df = pd.read_csv(f"{STOPS_DIR}/gares-de-voyageurs.csv", sep=";", dtype=str)

    df = df.rename(
        columns={
            "codes_uic": "stop_id",
            "nom": "name",
            "libellecourt": "abbrev",
            "codeinsee": "code_insee",
        }
    )

    # Split lat / lon
    df[["lat", "lon"]] = (
        df["position_geographique"].str.split(",", expand=True).astype(float)
    )

    # Keep only expected columns
    df = df[
        [
            "stop_id",
            "name",
            "abbrev",
            "code_insee",
            "lat",
            "lon",
        ]
    ]

    # Drop invalid rows
    df = df.dropna(subset=["stop_id", "lat", "lon"])

    # Persist
    df.to_csv(f"{STAGING_DIR}/stations.csv", index=False)


def clean_and_stage_stop_times():
    create_staging_directories()

    df = pd.read_csv(f"{GTFS_DIR}/stop_times.txt")

    df = df[
        [
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
        ]
    ]

    # Drop invalid rows
    df = df.dropna(
        subset=["trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"]
    )

    # ----------------------------------------
    # Extract service date from trip_id
    # ----------------------------------------
    # Last 8 digits are YYYYMMDD
    df["service_date"] = df["trip_id"].str.extract(r"(\d{8})$")

    df["service_date"] = pd.to_datetime(
        df["service_date"], format="%Y%m%d", errors="coerce"
    )

    # ----------------------------------------
    # Normalize stop_id
    # StopPoint:OCETrain TER-87713040 -> 87713040
    # ----------------------------------------
    df["stop_id"] = df["stop_id"].str.split("-").str[-1]

    # ----------------------------------------
    # Build full timestamps
    # ----------------------------------------
    df["arrival_time"] = pd.to_datetime(
        df["service_date"].astype(str) + " " + df["arrival_time"], errors="coerce"
    )

    df["departure_time"] = pd.to_datetime(
        df["service_date"].astype(str) + " " + df["departure_time"], errors="coerce"
    )

    # ----------------------------------------
    # Clean & order
    # ----------------------------------------
    df["stop_sequence"] = df["stop_sequence"].astype(int)

    df = df.dropna(subset=["arrival_time", "departure_time", "service_date"])

    df = df.sort_values(["trip_id", "stop_sequence"])

    # Finalise schema
    df = df[
        [
            "trip_id",
            "stop_id",
            "stop_sequence",
            "arrival_time",
            "departure_time",
        ]
    ]

    # Persist staging table
    df.to_csv(f"{STAGING_DIR}/stop_times.csv", index=False)


if __name__ == "__main__":
    clean_and_stage_stations()
