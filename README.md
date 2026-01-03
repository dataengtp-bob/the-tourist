# the-tourist

## Getting started

### Prepare for Airflow

#### First step: Setting up environment

First, create the **.env** file if not yet existed:

```
_AIRFLOW_VERSION=3.1.0
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
_PIP_ADDITIONAL_REQUIREMENTS=xlsx2csv==0.7.8 faker==8.12.1 apache-airflow-providers-postgres==6.3.0

AIRFLOW_GID=0
AIRFLOW_UID=TODO_CHANGE_ME
AIRFLOW_API_AUTH_JWT_SECRET=TODO_CHANGE_ME

PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=root
PGADMIN_PORT=5050

POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=airflow

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

Now get your **id** :

```sh
id -u
```

And create JWT secret, using this [website](https://jwtsecrets.com/)
or look [here](https://www.willhaley.com/blog/generate-jwt-with-bash/).

Now edit the **.env** file and swap out `AIRFLOW_UID` and `AIRFLOW_API_AUTH_JWT_SECRET` for your own.

### Second step: Running docker compose

Run the following command to create the volumes needed in order to send data to airflow:

```sh
mkdir -p ./dags ./logs
```

And run this **once**:

```sh
docker-compose up airflow-init
```

If the exit code is 0 then it's all good.

**Running Airflow**

```sh
docker-compose up -d
```

### Loading data into Neo4j

**Clean slate**

```
MATCH (n) DETACH DELETE n
```

**Create Index**

```
CREATE CONSTRAINT FOR (s:Station) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT FOR (t:Trip) REQUIRE t.id IS UNIQUE;
```

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

**Link origin and desitnation**
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

**Create NEXT_STOP chain**
```cypher
// 1. Match the pattern again
MATCH (t:Trip)-[r1:STOPS_AT]->(s1:Station)
MATCH (t)-[r2:STOPS_AT]->(s2:Station)
// Find cases where s2 is immediately after s1
WHERE r2.stop_sequence = r1.stop_sequence + 1

// 2. Find the existing NEXT_STOP edge between them for this trip
MATCH (s1)-[ns:NEXT_STOP {trip_id: t.id}]->(s2)

// 3. Copy the times from the STOPS_AT relationships onto the NEXT_STOP edge
SET ns.departure_time = r1.departure_time,
    ns.arrival_time = r2.arrival_time,
    ns.date = t.date
```

**Test query**

```cypher
MATCH (t:Trip)-[:STARTS_AT]->(start:Station)
MATCH (t)-[:ENDS_AT]->(end:Station)
MATCH path = (start)-[:NEXT_STOP*]->(end)
WHERE all(r in relationships(path) WHERE r.trip_id = t.id)
RETURN t, path
LIMIT 1
```