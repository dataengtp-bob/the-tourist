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

First, get your **id**:
```sh
id -u
```

Now edit the **.env** file and swap out 501 for your own.

Run the following command to creat the volumes needed in order to send data to airflow:

```sh
mkdir -p ./dags ./logs ./plugins
```

create JWT secret, using this [website](https://jwtsecrets.com/)
or look [here](https://www.willhaley.com/blog/generate-jwt-with-bash/).

And run this **once**:
```sh
docker-compose up airflow-init
```

If the exit code is 0 then it's all good.

**Running**

```sh
docker-compose up -d
```