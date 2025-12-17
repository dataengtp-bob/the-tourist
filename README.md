# the-tourist

## Getting started

**Setting up environment**
```bash
python3.9 -m venv .venv
.venv\Scripts\activate
pip install -U pandas geopandas shapely sqlalchemy psycopg2 geoalchemy2
```

**Creating database**
```bash
docker run --name travel-db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=travel_db -p 5432:5432 -d postgis/postgis
```

**Creating Neo4j database**
```bash
docker run --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -d neo4j/neo4j
```

**Loading stations into Neo4j**
```cypher
LOAD CSV WITH HEADERS FROM 'file:///stops.txt' AS row
WITH row
WHERE row.location_type = '1'

MERGE (s:Station {id: row.stop_id})
ON CREATE SET
    s.name = row.stop_name,
    // Create a 2D geospatial point
    s.location = point({latitude: toFloat(row.stop_lat), longitude: toFloat(row.stop_lon)})
RETURN count(s);
```

## Prepare for Airflow

### First step: Setting up environment

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
mkdir -p ./dags ./logs ./plugins
```

And run this **once**:
```sh
docker-compose up airflow-init
```

If the exit code is 0 then it's all good.

**Running**

```sh
docker-compose up -d
```