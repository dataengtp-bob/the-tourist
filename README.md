# the-tourist

## Getting started

**Setting up environment**
```bash
python3.9 -m venv .venv
.venv\Scripts\activate
pip install -U pandas geopandas shapely sqlalchemy psycopg2 geoalchemy2
```

**Loading stops into Neo4j**
```cypher
// 1. Load the CSV
LOAD CSV WITH HEADERS FROM 'file:///stops.txt' AS row

// 2. Filter and Extract ID
WITH row
WHERE row.location_type = '1'

// Split the string "StopArea:OCE71043075" by "OCE" -> ["StopArea:", "71043075"]
// We select index [1] to get the number part
WITH row, split(row.stop_id, 'OCE')[1] AS clean_id

// 3. Create the Node using the clean number
MERGE (s:Stop {id: clean_id})

// 4. Set properties
SET s.name = row.stop_name,
    s.latitude = toFloat(row.stop_lat),
    s.longitude = toFloat(row.stop_lon)

RETURN s
```

**Loading trips into Neo4j**
```cypher
// 1. Load the CSV
LOAD CSV WITH HEADERS FROM 'file:///trips.txt' AS row

// 2. Parse string
WITH row, split(row.trip_id, ':') AS parts

WITH row,
     parts[-5] AS origin_id, 
     parts[-4] AS dest_id
    //  parts[-1] AS date_str,
    //  parts[-2] AS time_str,

// 3. Create the Trip Node
MERGE (t:Trip {id: row.route_id})
SET t.headsign = row.trip_headsign
    // t.date = date_str,
    // t.time = time_str

// 4. Link Origin
WITH t, origin_id, dest_id
MATCH (start:Stop {id: origin_id})
MERGE (t)-[:STARTS_AT]->(start)

// 5. Link Destination
// *** FIX IS HERE: We must pass 'start' forward to use it later ***
WITH t, dest_id, start
MATCH (end:Stop {id: dest_id})
MERGE (t)-[:ENDS_AT]->(end)

RETURN t.id, start.name, end.name
```