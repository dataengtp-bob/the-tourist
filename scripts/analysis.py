import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:password@localhost:5432/tourist_db")

# This SQL query does the heavy lifting
sql_query = """
SELECT 
    s.stop_name, 
    a."Nom_du_POI" as attraction,
    a."Categories_de_POI" as category,
    -- Calculate distance in meters (casting to geography uses curved earth math)
    ST_Distance(s.geometry::geography, a.geometry::geography) as distance_meters
FROM 
    stops s
JOIN 
    attractions a
ON 
    -- THE MAGIC: Join only if they are within 1000 meters (1km)
    ST_DWithin(s.geometry::geography, a.geometry::geography, 20000)
WHERE 
    s.stop_name = 'Lyon Part Dieu' -- Let's test with a famous station
ORDER BY 
    distance_meters ASC;
"""

# Execute query and load directly into a dataframe
results = pd.read_sql(sql_query, engine)

print("--- Attractions near Gare de Lyon ---")
print(results.head(10))
