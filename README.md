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
- `stations.csv`
- `stop_times.csv`

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

For a collection of useful queries to explore the data, see [cypher_queries.md](cypher_queries.md).

## Analytical Questions Addressed

- **Route Variations**: What are the distinct route variations between major cities (e.g., Paris to Marseille) based on intermediate stops?
- **Station Roles**: How can we distinguish between major transit hubs (high connectivity) and frequent commuter stops (high volume)?
- **Network Traffic**: What are the strongest direct connections and busiest segments in the rail network?
- **Topological Centrality**: Which stations serve as the structural "center" of the network, based on connections rather than just trip volume?

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