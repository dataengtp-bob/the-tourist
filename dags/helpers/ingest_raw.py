import os
import requests
import zipfile

# ---------------------------
# Paths
# ---------------------------
LANDING_DIR = "data/landing"
STOPS_DIR = f"{LANDING_DIR}/stations"
GTFS_DIR = f"{LANDING_DIR}/gtfs"

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


def create_landing_directories():
    os.makedirs(STOPS_DIR, exist_ok=True)
    os.makedirs(GTFS_DIR, exist_ok=True)


def download_file_from_url(url, output_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return os.path.getsize(output_path)


def download_sncf_stations_csv():
    create_landing_directories()
    output_path = f"{STOPS_DIR}/gares-de-voyageurs.csv"
    download_file_from_url(SNCF_STOPS_URL, output_path)


def download_and_extract_sncf_gtfs():
    create_landing_directories()
    zip_path = f"{GTFS_DIR}/raw_gtfs.zip"
    download_file_from_url(GTFS_ZIP_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(GTFS_DIR)


def main():
    create_landing_directories()

    print("Downloading SNCF train stations...")
    download_sncf_stations_csv()

    print("Downloading SNCF GTFS data...")
    download_and_extract_sncf_gtfs()

    print("Pipeline 1 – Raw ingestion completed successfully.")


if __name__ == "__main__":
    main()
