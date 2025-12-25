# the-tourist

## Getting started

**Setting up environment**

```bash
python3.9 -m venv .venv
.venv\Scripts\activate
pip install -U pandas geopandas shapely sqlalchemy psycopg2 geoalchemy2
```

**Loading stops into Neo4j**

```cypher
// 1. Load the CSV
LOAD CSV WITH HEADERS FROM 'file:///stops.txt' AS row

// 2. Filter and Extract ID
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
// Split the string "StopArea:OCE71043075" by "OCE" -> ["StopArea:", "71043075"]
// We select index [1] to get the number part
WITH row, split(row.stop_id, 'OCE')[1] AS clean_id

// 3. Create the Node using the clean number
MERGE (s:Stop {id: clean_id})

// 4. Set properties
SET s.name = row.stop_name,
    s.latitude = toFloat(row.stop_lat),
    s.longitude = toFloat(row.stop_lon)

RETURN s
```

**Loading trips into Neo4j**

```cypher
// 1. Load the CSV
LOAD CSV WITH HEADERS FROM 'file:///trips.txt' AS row

// 2. Parse string
WITH row, split(row.trip_id, ':') AS parts

WITH row,
     parts[-5] AS origin_id,
     parts[-4] AS dest_id
    //  parts[-1] AS date_str,
    //  parts[-2] AS time_str,

// 3. Create the Trip Node
MERGE (t:Trip {id: row.route_id})
SET t.headsign = row.trip_headsign
    // t.date = date_str,
    // t.time = time_str

// 4. Link Origin
WITH t, origin_id, dest_id
MATCH (start:Stop {id: origin_id})
MERGE (t)-[:STARTS_AT]->(start)

// 5. Link Destination
// *** FIX IS HERE: We must pass 'start' forward to use it later ***
WITH t, dest_id, start
MATCH (end:Stop {id: dest_id})
MERGE (t)-[:ENDS_AT]->(end)

RETURN t.id, start.name, end.name
```
