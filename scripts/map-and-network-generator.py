import json
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import shape


def create_combined_map(json_file_path):
    # --- PART 1: LOAD RAILWAY LINES (export.json) ---
    print(f"Loading railway lines from {json_file_path}...")

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        df_lines = pd.DataFrame(data)
        # Drop rows with missing geometry and convert to Shape objects
        df_lines = df_lines.dropna(subset=["geometry"])
        df_lines["geometry"] = df_lines["geometry"].apply(lambda x: shape(x))

        gdf_lines = gpd.GeoDataFrame(df_lines, geometry="geometry")
        gdf_lines.set_crs(epsg=4326, inplace=True)
        print(f"Loaded {len(gdf_lines)} railway segments.")

    except FileNotFoundError:
        print(
            f"Error: '{json_file_path}' not found. Please download it from data.gouv.fr first."
        )
        return

    # --- PART 2: LOAD STATIONS (GTFS stops.txt) ---
    try:
        # Read stops.txt directly
        with open("data/sncf-gtfs-theorique/stops.txt") as stops_file:
            df_stops = pd.read_csv(stops_file)

        print(f"GTFS stops loaded. Total raw stops: {len(df_stops)}")

        # Filter for StopAreas only
        # In GTFS, location_type == 1 means "Station" (StopArea)
        df_stations = df_stops[df_stops["location_type"] == 1].copy()

        print(f"Filtered for StopAreas. Found {len(df_stations)} stations.")

    except Exception as e:
        print(f"Error fetching or processing GTFS data: {e}")
        return

    # --- PART 3: CREATE MAP ---
    print("Generating map...")

    # Center on France
    m = folium.Map(
        location=[46.603354, 1.888334], zoom_start=6, tiles="CartoDB positron"
    )

    # 1. Add Railway Lines
    folium.GeoJson(
        gdf_lines,
        name="Réseau Ferré",
        style_function=lambda x: {"color": "#003399", "weight": 2, "opacity": 0.6},
        tooltip=folium.GeoJsonTooltip(
            fields=["nomLigne", "statut"], aliases=["Ligne:", "Statut:"], localize=True
        ),
    ).add_to(m)

    # 2. Add Stations (using MarkerCluster for performance)
    marker_cluster = MarkerCluster(name="Gares (StopAreas)").add_to(m)

    for idx, row in df_stations.iterrows():
        # Ensure lat/lon are valid numbers
        if pd.notnull(row["stop_lat"]) and pd.notnull(row["stop_lon"]):
            folium.CircleMarker(
                location=[row["stop_lat"], row["stop_lon"]],
                radius=4,
                color="red",
                fill=True,
                fill_color="white",
                fill_opacity=1,
                popup=row["stop_name"],
                tooltip=f"Gare: {row['stop_name']}",
            ).add_to(marker_cluster)

    # Add layer control to toggle lines/stations
    folium.LayerControl().add_to(m)

    output_file = "data-reports/carte_reseau_et_gares.html"
    m.save(output_file)
    print(f"Map saved to {output_file}.")


if __name__ == "__main__":
    # Ensure export.json is in the folder
    create_combined_map("data/datagouv-reseau-ferroviere.json")
