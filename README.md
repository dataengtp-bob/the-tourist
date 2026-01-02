# the-tourist

## Project Introduction

This project is a data engineering application built to analyze railway trips using open SNCF datasets. Railway schedule data is complex and distributed across multiple tabular files, which makes it difficult to analyze relationships between stations and to identify indirect journeys or detours between cities. The goal of this project is to transform these datasets into a graph-based representation that enables efficient exploration of train connectivity and stop sequences.

The project follows a layered data architecture and uses Apache Airflow for workflow orchestration and Neo4j for graph-based analytics. It demonstrates how raw transportation data can be ingested, cleaned, enriched, and transformed into an analytics-ready graph model.

## Datasets

The project is based on the following open datasets:

- **[SNCF – Gares de voyageurs](https://data.sncf.com/explore/dataset/gares-de-voyageurs/table/?disjunctive.segment_drg&sort=nom)** :
  Passenger railway stations dataset containing station identifiers, names, and geographic information.  

- **[Réseau SNCF TGV, Intercités et TER](https://transport.data.gouv.fr/datasets/horaires-sncf)** : 
  GTFS datasets containing train schedules and stop times.  

## Project Design and Architecture

The project is divided into three main areas, each implemented as a separate Airflow pipeline.

### 1. Landing Zone – Raw Data Ingestion

**Objective:**  
Collect raw data from official SNCF sources and store it without modification to ensure traceability and reproducibility.

**Steps:**
- Download raw CSV and GTFS files (stations and stop times).
- Store the files in a landing directory.
- Log ingestion metadata such as timestamp and data source.

**Output:**  
Raw datasets stored in the landing zone.

### 2. Staging Zone – Data Cleaning and Transformation

**Objective:**  
Prepare clean, structured, and enriched datasets suitable for analytics.

**Steps:**
- Read raw data from the landing zone.
- Clean station data by removing duplicates and handling missing or invalid values.
- Clean stop times data by validating stop identifiers and ordering stops using trip IDs and stop sequences.
- Enrich stop times with station metadata (names and coordinates).
- Persist the cleaned and enriched datasets in durable storage.

**Staging Tables:**
- `stops_staging`
- `stop_times_staging`
- `trips_staging`

**Output:**  
Structured and reliable datasets stored in the staging zone.

### 3. Production Zone – Graph Modeling and Analytics

**Objective:**  
Transform staged data into an analytics-ready graph representation and enable advanced queries.

**Steps:**
- Create graph nodes for stations and trips.
- Create relationships representing ordered stop sequences within each trip.
- Load the graph into Neo4j using batch processing.
- Execute graph queries to analyze railway connectivity and detect detours.

**Graph Model:**
- Nodes: `Station`, `Trip`
- Relationships: `STOPS_AT`, `NEXT_STOP`

**Output:**  
Neo4j graph database supporting analytical queries.

## Analytical Questions Addressed

- Which train trips connect two cities through intermediate stations?
- Which stations or cities frequently appear as detours?
- How are stations connected based on train stop sequences?
- Which stations are central in the railway network?

## Team Members

1. **VU Thi Tho** – Raw data ingestion and Airflow pipeline setup  
2. **HUYNH Huu Thanh Tu** – Data cleaning, enrichment, and staging layer  
3. **Louis KUSNO** – Graph modeling, Neo4j integration, and analytics queries  

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
