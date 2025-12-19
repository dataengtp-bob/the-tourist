import os
import requests
import zipfile
import pandas as pd

# ---------------------------
# Paths
# ---------------------------
LANDING_DIR = "data/landing"
STOPS_DIR = f"{LANDING_DIR}/train_stops"
GTFS_DIR = f"{LANDING_DIR}/gtfs"
METADATA_DIR = f"{LANDING_DIR}/metadata"
METADATA_FILE = f"{METADATA_DIR}/ingestion_log.csv"

# ---------------------------
# Source URLs
# ---------------------------
SNCF_STOPS_URL = (
    "https://data.sncf.com/api/explore/v2.1/catalog/"
    "datasets/gares-de-voyageurs/exports/csv"
)

GTFS_ZIP_URL = (
    "https://eu.ftp.opendatasoft.com/sncf/plandata/"
    "Export_OpenData_SNCF_GTFS_NewTripId.zip"
)

def create_directories():
    os.makedirs(STOPS_DIR, exist_ok=True)
    os.makedirs(GTFS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)

def download_file(url, output_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return os.path.getsize(output_path)

def ingest_train_stops():
    create_directories()
    output_path = f"{STOPS_DIR}/gares-de-voyageurs.csv"
    download_file(SNCF_STOPS_URL, output_path)


def ingest_gtfs():
    create_directories()
    zip_path = f"{GTFS_DIR}/raw_gtfs.zip"
    download_file(GTFS_ZIP_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(GTFS_DIR)

def log_metadata(records):
    df_new = pd.DataFrame(records)

    if os.path.exists(METADATA_FILE):
        df_existing = pd.read_csv(METADATA_FILE)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(METADATA_FILE, index=False)

def main():
    create_directories()

    metadata = []

    print("Ingesting SNCF train stations...")
    metadata.append(ingest_train_stops())

    print("Ingesting SNCF GTFS data...")
    metadata.append(ingest_gtfs())

    log_metadata(metadata)

    print("Pipeline 1 – Raw ingestion completed successfully.")

if __name__ == "__main__":
    main()
