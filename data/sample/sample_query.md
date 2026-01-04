**Loading Stations into Neo4j**

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

**Loading trips into Neo4j**

```cypher
:auto LOAD CSV WITH HEADERS FROM 'file:///stop_times.csv' AS row
CALL {
  WITH row
  
  // 1. Create the Trip Node
  MERGE (t:Trip {id: row.trip_id})
  
  // 2. Parse ID for Date
  ON CREATE SET t.date = split(row.trip_id, ':')[-1]
  
  // *** FIX IS HERE: Pass 't' and 'row' forward ***
  WITH t, row
  
  // 3. Find the Station
  MATCH (s:Station {id: row.stop_id})
  
  // 4. Connect them
  MERGE (t)-[r:STOPS_AT]->(s)
  SET r.arrival_time = row.arrival_time,
      r.departure_time = row.departure_time,
      r.stop_sequence = toInteger(row.stop_sequence)

} IN TRANSACTIONS OF 1000 ROWS
RETURN count(*) as RowsProcessed
```

**Test query**

```cypher
MATCH (t:Trip {id: 'OCEEA436010R5235_R:CTE:FR:Line::8440e055-0d15-4156-9e77-017af816441a::87296012:87296442:5:1052:20260116'})
MATCH (t)-[r:STOPS_AT]->(s:Station)
RETURN t.id, s.name, r.arrival_time
ORDER BY r.stop_sequence ASC
```