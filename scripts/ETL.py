import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

# --- 1. Load SNCF Data ---
stops_df = pd.read_csv(
    "sncf-gtfs-theorique/stops.txt",
    usecols=["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type"],
    dtype={"stop_id": str},
)

# Filter for Parent Stations (1) and drop bad coords
stops_df = stops_df[stops_df["location_type"] == 1]
stops_df = stops_df.dropna(subset=["stop_lat", "stop_lon"])

# Convert to GeoDataFrame
gdf_stops = gpd.GeoDataFrame(
    stops_df,
    geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
    crs="EPSG:4326",
)

print(f"SNCF Stations ready: {len(gdf_stops)}")

# --- 2. Load Tourism Data ---
# Note: DataTourisme files are large. If this crashes memory, use chunksize.
tourism_df = pd.read_csv(
    "datagouv-tourist/datatourisme.csv",
    # sep=";",  # <--- CRITICAL: French CSVs usually use semicolons
    usecols=["Nom_du_POI", "Description", "Latitude", "Longitude", "Categories_de_POI"],
    dtype={"Categories_de_POI": str},  # prevent mix-type errors
)

tourism_df = tourism_df.dropna(subset=["Latitude", "Longitude"])

# Convert to GeoDataFrame
gdf_tourism = gpd.GeoDataFrame(
    tourism_df,
    geometry=gpd.points_from_xy(tourism_df.Longitude, tourism_df.Latitude),
    crs="EPSG:4326",
)

print(f"Attractions ready: {len(gdf_tourism)}")

# --- 3. Load to Database ---
engine = create_engine("postgresql://user:password@localhost:5432/tourist_db")

# Use method='multi' for faster inserts on large datasets
gdf_stops.to_postgis("stops", engine, if_exists="replace", index=False)
gdf_tourism.to_postgis(
    "attractions", engine, if_exists="replace", index=False, chunksize=1000
)

print("ETL Complete: Data loaded to PostGIS.")
