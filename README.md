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
  
  // 1. Create the Trip Node from the ID string
  MERGE (t:Trip {id: row.trip_id})
  
  // 2. Parse ID for Date (runs only when creating the node to save time)
  ON CREATE SET 
    t.date = split(row.trip_id, ':')[-1]
  
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
MATCH (t:Trip {id: 'OCEEA436129R5235_R:CTE:FR:Line::8440e055-0d15-4156-9e77-017af816441a::87313874:87296442:10:1215:20260213'})
MATCH (t)-[r:STOPS_AT]->(s:Station)
RETURN t.id, s.name, r.arrival_time
ORDER BY r.stop_sequence ASC
```