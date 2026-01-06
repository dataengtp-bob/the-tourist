# BUILDING DATA PIPELINES FOR GRAPH-BASED RAILWAY ANALYTICS

## Project Introduction

This project is a data engineering application built to analyze railway trips using open SNCF datasets. Railway schedule data is complex and distributed across multiple tabular files, which makes it difficult to analyze relationships between stations and to identify indirect journeys or detours between cities. The goal of this project is to transform these datasets into a graph-based representation that enables efficient exploration of train connectivity and stop sequences.

The project follows a layered data architecture and uses Apache Airflow for workflow orchestration and Neo4j for graph-based analytics. It demonstrates how raw transportation data can be ingested, cleaned, enriched, and transformed into an analytics-ready graph model.

## Team Members

1. **VU Thi Tho** – Raw data ingestion and Airflow pipeline setup  
2. **HUYNH Huu Thanh Tu** – Data cleaning, enrichment, and staging layer  
3. **Louis KUSNO** – Graph modeling, Neo4j integration, and analytics queries  

## Datasets

The project is based on the following open datasets:

- **[SNCF – Gares de voyageurs](https://data.sncf.com/explore/dataset/gares-de-voyageurs/table/?disjunctive.segment_drg&sort=nom)** :
  Passenger railway stations dataset containing station identifiers, names, and geographic information.  

- **[Réseau SNCF TGV, Intercités et TER](https://transport.data.gouv.fr/datasets/horaires-sncf)** : 
  GTFS datasets containing train schedules and stop times.  

## Project Design and Architecture

<img width="1829" height="703" alt="image" src="https://github.com/user-attachments/assets/c6ac7b59-ef4f-4555-ae30-f5fcf02f2a14" />

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

***1. Read raw data***

- Load `gares-de-voyageurs.csv` (stations) and `stop_times.txt` (GTFS stop times) from the landing zone.

***2. Clean and normalize station data***

- Remove duplicates and invalid rows.

- Normalize identifiers: the raw `codes_uic` column may contain multiple IDs separated by `;` (e.g., `87001479;87271494`).
Each identifier is split into a separate row and stored as `stop_id` in the staged dataset.

- Ensure all required fields (station name, city, coordinates) are present.

***3. Clean and transform stop times data***

- Normalize `stop_id` by removing technical prefixes (e.g., `StopPoint:OCETrain TER-87713040` → `87713040`).

- Extract the service date from `trip_id` (last 8 digits) and combine it with `arrival_time` and `departure_time` to create full datetime values.

- Convert `stop_sequence` to integer and ensure stops are ordered correctly per trip.

- Remove rows with missing or invalid timestamps or service dates.

***4. Persist staging tables***

- Save cleaned and enriched datasets to durable storage for use in production.

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
- Relationships: `STOPS_AT`, `NEXT_STOP`, `STARTS_AT`, `ENDS_AT`

**Output:**  
Neo4j graph database supporting analytical queries.

For a collection of useful queries to explore the data, see [cypher_queries.md](cypher_queries.md).

## Analytical Questions Addressed

- **Route Variations**: What are the distinct route variations between major cities (e.g., Paris to Marseille) based on intermediate stops?
- **Station Roles**: How can we distinguish between major transit hubs (high connectivity) and frequent commuter stops (high volume)?
- **Network Traffic**: What are the strongest direct connections and busiest segments in the rail network?
- **Topological Centrality**: Which stations serve as the structural "center" of the network, based on connections rather than just trip volume?

## Project Minimal Submission Checklist
- [x] repository with the code, well documented, including:
  - [x] docker-compose file to run the environment
  - [x] detailed description of the various steps
  - [x] report in the Repository README with the project design steps (divided per area), a guide how to run it, and consideration relevant to understand it.
  - [x] Example dataset: the project testing should work offline, i.e., you need to have some sample data points.
  - [x] slides for the project poster. You can do them too in markdown too.

### Increasing Project Grade

- [x] +1: Include in the pipelines any tool discussed during the course
  - [x] Neo4j
  - [x] Requirement: It has to be used properly, always better to double check with teacher
- [ ] +1: Discuss one of the theoretical topics from the course, e.g., add considerations about governance, privacy, etc
  - [ ] Requirement: It should be included in the report and the poster.
- [ ] +2: Using any Data Engineering tool not explained during the course
  - [ ] Requirement: It should be state of the art tooling.
  - [ ] Every extra should be approved
  - [ ] Example: using Kafka for ingestion and staging (also + docker)
- [x] +X: Creativity section
  - [x] Examples: data viz, serious analysis.

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
