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
MERGE (s:Station {id: row.stop_id})
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

## 2. Interesting queries

### Shortest path

```cypher
MATCH (start:Station {name: 'Paris Gare de Lyon'}), (end:Station {name: 'Marseille Saint-Charles'})
MATCH p = shortestPath((start)-[:NEXT_STOP*]-(end))
RETURN p
```

### Travel time path finding

```cypher
MATCH (t:Trip)-[:STARTS_AT]->(start:Station)
MATCH (t)-[:ENDS_AT]->(end:Station)
MATCH path = (start)-[:NEXT_STOP*]->(end)
WHERE all(r in relationships(path) WHERE r.trip_id = t.id)
RETURN t, path
LIMIT 1
```

### Basic Stats
Check the size of your graph.

```cypher
// Count Stations and Trips
MATCH (n) 
RETURN labels(n) as Label, count(*) as Count
```

### Find a Station
Look up a station by name (partial match).

```cypher
MATCH (s:Station) 
WHERE s.name CONTAINS 'Paris' 
RETURN s.name, s.id, s.abbreviation 
LIMIT 10
```

### Visualize a Trip
See a single trip and its sequence of stops.

```cypher
MATCH (t:Trip)-[r:STOPS_AT]->(s:Station)
WHERE t.id = 'YOUR_TRIP_ID_HERE' // e.g., pick one from the DB
RETURN t, r, s
ORDER BY r.stop_sequence
```

### Shortest Path (Number of Hops)
Find the fewest stops between two stations using the `NEXT_STOP` relationship.

```cypher
MATCH (start:Station {name: 'Paris Gare de Lyon'}), (end:Station {name: 'Marseille Saint-Charles'})
MATCH p = shortestPath((start)-[:NEXT_STOP*]-(end))
RETURN p
```

### Travel Time Path finding
Find a route based on time (simple example, strictly following next connections).

```cypher
MATCH (start:Station {name: 'Paris Montparnasse'}), (end:Station {name: 'Bordeaux St-Jean'})
MATCH p = (start)-[:NEXT_STOP*1..5]->(end)
RETURN p, 
       reduce(totalTime = 0, r in relationships(p) | totalTime + toInteger(duration.between(r.departure_time, r.arrival_time).seconds)) as DurationSeconds
ORDER BY DurationSeconds ASC
LIMIT 1
```

### Busiest Stations
Find stations with the most stop events.

```cypher
MATCH (s:Station)<-[r:STOPS_AT]-(:Trip)
RETURN s.name, count(r) as connections
ORDER BY connections DESC
LIMIT 10
```

### Isolates
Find stations that have no trips connected to them (orphan nodes).

```cypher
MATCH (s:Station)
WHERE NOT (s)<-[:STOPS_AT]-(:Trip)
RETURN s.name, s.id
```
