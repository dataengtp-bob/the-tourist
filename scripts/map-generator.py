import pandas as pd
import folium
from folium.plugins import FastMarkerCluster
import os


def generate_stops_map():
    print("Generating stops map...")
    try:
        with open("sncf-gtfs-theorique/stops.txt") as f:
            stops = pd.read_csv(f)
    except FileNotFoundError:
        print("Error: sncf-gtfs-theorique/stops.txt not found.")
        return

    stations = stops[stops["location_type"] == 1]

    if stations.empty:
        print("No stations found.")
        return

    # create map
    m = folium.Map(
        location=[stations["stop_lat"].mean(), stations["stop_lon"].mean()],
        zoom_start=6,
    )

    # add points
    for _, row in stations.iterrows():
        folium.CircleMarker(
            location=[row["stop_lat"], row["stop_lon"]],
            radius=2,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            popup=f"{row['stop_name']}\nid: {row['stop_id']})",
        ).add_to(m)

    # save to HTML
    output_path = "data-reports/map-stops.html"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    print(f"Saved: {output_path}")


def generate_tourist_map():
    print("Generating tourist map...")
    data_path = "datagouv-tourist/datatourisme.csv"
    output_path = "data-reports/map-tourism.html"

    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: {data_path} not found.")
        return

    # Filter invalid coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    if df.empty:
        print("No valid tourist data to plot.")
        return

    # Create map centered on mean of data
    m = folium.Map(
        location=[df["Latitude"].mean(), df["Longitude"].mean()], zoom_start=6
    )

    # Prepare data for FastMarkerCluster
    marker_data = []
    for idx, row in df.iterrows():
        name = str(row.get("Nom_du_POI", "Unknown"))
        marker_data.append([row["Latitude"], row["Longitude"], name])

    FastMarkerCluster(data=marker_data).add_to(m)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    print(f"Saved: {output_path}")


def main():
    generate_stops_map()
    print("-" * 20)
    generate_tourist_map()
    print("All maps generated.")


if __name__ == "__main__":
    main()
