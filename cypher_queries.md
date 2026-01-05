# Cypher Queries for The Tourist

Here are some useful Cypher queries to explore and analyze your rail network graph.

## 1. Loading data into Neo4j

### Clean slate

```
MATCH (n) DETACH DELETE n
```

### Create Index

```
CREATE CONSTRAINT FOR (s:Station) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT FOR (t:Trip) REQUIRE t.id IS UNIQUE;
```

### Loading Stations into Neo4j

```cypher
LOAD CSV WITH HEADERS FROM 'file:///stations.csv' AS row
UNWIND split(row.stop_id, ';') AS station_id
MERGE (s:Station {id: station_id})
SET s.name = row.name,
    s.abbreviation = row.abbrev,
    s.insee_code = row.code_insee,
    s.latitude = toFloat(row.lat),
    s.longitude = toFloat(row.lon)
RETURN count(s) as StationsImported
```

### Loading trips into Neo4j

```cypher
:auto LOAD CSV WITH HEADERS FROM 'file:///stop_times.csv' AS row
CALL {
  WITH row
  
  // 1. Create the Trip Node
  MERGE (t:Trip {id: row.trip_id})
  
  // 2. Parse ID for Date (runs only once per trip creation)
  ON CREATE SET t.date = split(row.trip_id, ':')[-1]
  
  // 3. Pass variables forward to the next step
  WITH t, row
  
  // 4. Find the Station
  MATCH (s:Station {id: row.stop_id})
  
  // 5. Connect them
  MERGE (t)-[r:STOPS_AT]->(s)
  SET r.arrival_time = row.arrival_time,
      r.departure_time = row.departure_time,
      r.stop_sequence = toInteger(row.stop_sequence)

} IN TRANSACTIONS OF 1000 ROWS
RETURN count(*) as RowsProcessed
```

### Link origin and desitnation
```cypher
MATCH (t:Trip)
// Parse the ID string: ID format ...:OriginID:DestID:Metadata:Date
WITH t, split(t.id, ':') AS parts
WITH t, 
     parts[-5] AS origin_id, 
     parts[-4] AS dest_id

// Link Origin
MATCH (start:Station {id: origin_id})
MERGE (t)-[:STARTS_AT]->(start)

// Link Destination
WITH t, dest_id
MATCH (end:Station {id: dest_id})
MERGE (t)-[:ENDS_AT]->(end)

RETURN count(t) as TripsLinked
```

### Create NEXT_STOP chain
```cypher
// 1. Match the pattern again
MATCH (t:Trip)-[r1:STOPS_AT]->(s1:Station)
MATCH (t)-[r2:STOPS_AT]->(s2:Station)
// Find cases where s2 is immediately after s1
WHERE r2.stop_sequence = r1.stop_sequence + 1

// 2. Find the existing NEXT_STOP edge between them for this trip
MERGE (s1)-[ns:NEXT_STOP {trip_id: t.id}]->(s2)

// 3. Copy the times from the STOPS_AT relationships onto the NEXT_STOP edge
SET ns.departure_time = r1.departure_time,
    ns.arrival_time = r2.arrival_time,
    ns.date = t.date
```

## 2. Basic queries

### Visualize Trip Stops
Retrieve all stops for a specific trip.

```cypher
MATCH (t:Trip)-[r:STOPS_AT]->(s:Station)
WHERE t.id = 'OCESN6122F1187_F:OUI:FR:Line::BAF1DE9A-72EC-4064-8BE9-C4EFF292CB6A::87751008:87686006:4:1819:20260503' // e.g., pick one from the DB
RETURN t, r, s
```

### Topological Shortest Path
Find the shortest path between two stations based solely on the number of stops (hops), disregarding physical distance or trip schedules.

```cypher
MATCH (start:Station {name: 'Nantes'}), (end:Station {name: 'Marseille Saint-Charles'})
MATCH p = shortestPath((start)-[:NEXT_STOP*]-(end))
RETURN p
```

### Reconstruct Trip Path from NEXT_STOP
Reconstruct the full traversal path of a specific trip using the `NEXT_STOP` relationships that link its sequence of stations.

```cypher
MATCH (t:Trip)-[r1:STARTS_AT]->(start:Station)
MATCH (t)-[r2:ENDS_AT]->(end:Station)
MATCH path = (start)-[:NEXT_STOP*]->(end)
WHERE all(r in relationships(path) WHERE r.trip_id = t.id)
RETURN t, path, r1,r2
LIMIT 1
```

### Isolates
Find stations that have no trips connected to them (orphan nodes).

```cypher
MATCH (s:Station)
WHERE NOT (s)<-[:STOPS_AT]-(:Trip)
RETURN s.name, s.id
```

## 3. Analytical Questions Implementation

These queries directly address the analytical questions posed in the README.

### 1. Identify Route Variations

Group all trips between two cities by their unique sequence of intermediate stops to identify distinct route variations.

```cypher
MATCH (start:Station {name: 'Paris Gare de Lyon'})<-[:STARTS_AT]-(t:Trip)-[:ENDS_AT]->(end:Station {name: 'Marseille Saint-Charles'})
MATCH (t)-[r:STOPS_AT]->(s:Station)
WITH t, s ORDER BY r.stop_sequence
WITH t, collect(s) as stops
// Group by the specific sequence of stations to find unique routes
WITH stops, head(collect(t)) as representative_trip, count(t) as frequency
ORDER BY size(stops) DESC
// You can uncomment the next line to limit the number of variations shown
// LIMIT 5

// Now fetch the full graph structure for these representative trips (Query 1 style)
MATCH (representative_trip)-[r:STOPS_AT]->(s:Station)
OPTIONAL MATCH (s)-[ns:NEXT_STOP]->(next:Station)
WHERE ns.trip_id = representative_trip.id

RETURN representative_trip, r, s, ns, next
```

### 2. Analyze Station Role (Volume vs Connectivity)

Calculate total stop volume and the number of distinct connecting stations to classify stations (e.g., major hubs vs. busy commuter stops).

```cypher
MATCH (s:Station)
// Metric 1: Volume - Count total train stops
OPTIONAL MATCH (s)<-[r:STOPS_AT]-(:Trip)
WITH s, count(r) as TotalStopEvents

// Metric 2: Connectivity - Count distinct neighboring stations
OPTIONAL MATCH (s)-[:NEXT_STOP]-(neighbor)
WITH s, TotalStopEvents, count(DISTINCT neighbor) as DistinctConnections

RETURN s.name, TotalStopEvents, DistinctConnections
ORDER BY TotalStopEvents DESC
LIMIT 20
```

### 3. Strongest Direct Connections

Identify the most frequent direct segments between station pairs by counting the number of `NEXT_STOP` relationships.

```cypher
MATCH (a:Station)-[r:NEXT_STOP]->(b:Station)
RETURN a.name as From, b.name as To, count(r) as Frequency
ORDER BY Frequency DESC
LIMIT 20
```

### 4. Which stations are central in the railway network?

This calculates Degree Centrality based on the network structure (`NEXT_STOP` relationships) rather than just trip volume. It highlights stations that are topologically central.

```cypher
MATCH (s:Station)
// Count incoming and outgoing topological connections
OPTIONAL MATCH (s)-[r:NEXT_STOP]-()
RETURN s.name, count(r) as NetworkDegree
ORDER BY NetworkDegree DESC
LIMIT 10
```

> **Note:** For more advanced centrality metrics like PageRank or Betweenness Centrality (which are better for detecting "detours" and influence), you should use the **Neo4j Graph Data Science (GDS)** library if available.

#### Example: PageRank with GDS (if installed)
```cypher
CALL gds.graph.project(
  'railGraph',
  'Station',
  'NEXT_STOP'
)
YIELD graphName;

CALL gds.pageRank.stream('railGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS Station, score
ORDER BY score DESC
LIMIT 10;
```

