import pandas as pd
import os

# Define file path - verify path relative to script execution
# Assuming script runs from project root
file_path = os.path.join("data", "staging", "stop_times.csv")

if not os.path.exists(file_path):
    # Try absolute path just in case
    file_path = r"c:\Users\louis\insa\the-tourist\data\staging\stop_times.csv"

print(f"Reading file: {file_path}")

try:
    df = pd.read_csv(file_path)

    # 1. Total number of trips
    num_trips = df["trip_id"].nunique()
    print(f"\nTotal number of unique trips: {num_trips}")

    # 2. Time frame
    # Convert to datetime objects for accurate min/max finding
    # The format seems to be "YYYY-MM-DD HH:MM:SS" based on previous `view_file`
    df["arrival_time"] = pd.to_datetime(df["arrival_time"])
    df["departure_time"] = pd.to_datetime(df["departure_time"])

    earliest_arrival = df["arrival_time"].min()
    latest_departure = df["departure_time"].max()

    print("Time Frame:")
    print(f"  Earliest Arrival:   {earliest_arrival}")
    print(f"  Latest Departure:   {latest_departure}")
    print(f"  Span:               {latest_departure - earliest_arrival}")

    # 3. Other interesting metrics
    print("\nTrip Statistics:")

    # Group by trip_id to find stats per trip
    trip_stats = df.groupby("trip_id").agg(
        num_stops=("stop_id", "count"),
        start_time=("departure_time", "min"),
        end_time=("arrival_time", "max"),
    )

    trip_stats["duration"] = trip_stats["end_time"] - trip_stats["start_time"]

    avg_duration = trip_stats["duration"].mean()
    min_duration = trip_stats["duration"].min()
    max_duration = trip_stats["duration"].max()

    print(f"  Average Trip Duration: {avg_duration}")
    print(f"  Min Trip Duration:     {min_duration}")
    print(f"  Max Trip Duration:     {max_duration}")

    avg_stops = trip_stats["num_stops"].mean()
    print(f"  Average Stops per Trip: {avg_stops:.2f}")

    # Most common stop count
    common_stop_counts = trip_stats["num_stops"].value_counts().head(5)
    print("\nMost Common Number of Stops per Trip:")
    print(common_stop_counts.to_string())

    # 4. Trips per day
    print("\nTrips per Day:")
    # Create a column for just the date
    df["date"] = df["departure_time"].dt.date
    # Deduplicate trips per day (one row per trip_id per day) - actually trip_id should be unique per day?
    # Let's count unique trip_ids per date.
    daily_trips = df.groupby("date")["trip_id"].nunique()

    print(f"  Average Trips per Day: {daily_trips.mean():.2f}")
    print(f"  Min Trips per Day:     {daily_trips.min()}")
    print(f"  Max Trips per Day:     {daily_trips.max()}")
    print("\nDaily Trip Counts (First 5 days):")
    print(daily_trips.head().to_string())
    print("\nDaily Trip Counts (Description):")
    print(daily_trips.describe().to_string())


except Exception as e:
    print(f"An error occurred: {e}")
