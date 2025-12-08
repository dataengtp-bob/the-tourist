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