"""
Neo4j data loading functions for the tourist DAG.
Loads stations, trips, and relationships into Neo4j graph database.
"""

from neo4j import GraphDatabase
import os
import logging

logger = logging.getLogger(__name__)

NEO4J_IMPORT_DIR = "/var/lib/neo4j/import"


def get_neo4j_driver():
    """Create a Neo4j driver using environment variables."""
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def run_cypher(query: str, **kwargs):
    """Execute a Cypher query and return the result summary."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query, **kwargs)
        summary = result.consume()
        logger.info(f"Query executed. Counters: {summary.counters}")
    driver.close()
    return summary


def clear_database():
    """Delete all nodes and relationships in the database."""
    logger.info("Clearing Neo4j database...")
    run_cypher("MATCH (n) DETACH DELETE n")
    logger.info("Database cleared.")


def create_constraints():
    """Create unique constraints on Station and Trip nodes."""
    logger.info("Creating Neo4j constraints...")

    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trip) REQUIRE t.id IS UNIQUE",
    ]

    for query in queries:
        run_cypher(query)

    logger.info("Constraints created successfully.")


def load_stations():
    """Load stations from CSV into Neo4j."""
    logger.info("Loading stations into Neo4j...")

    query = """
    LOAD CSV WITH HEADERS FROM 'file:///stations.csv' AS row
    MERGE (s:Station {id: row.stop_id})
    SET s.name = row.name,
        s.abbreviation = row.abbrev,
        s.insee_code = row.code_insee,
        s.latitude = toFloat(row.lat),
        s.longitude = toFloat(row.lon)
    RETURN count(s) as StationsImported
    """

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        count = record["StationsImported"] if record else 0
        logger.info(f"Loaded {count} stations into Neo4j.")
    driver.close()


def load_trips():
    """Load trips and stop times from CSV into Neo4j."""
    logger.info("Loading trips into Neo4j...")

    query = """
    LOAD CSV WITH HEADERS FROM 'file:///stop_times.csv' AS row
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
    """

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        count = record["RowsProcessed"] if record else 0
        logger.info(f"Processed {count} stop time rows into Neo4j.")
    driver.close()


def link_origin_destination():
    """Create STARTS_AT and ENDS_AT relationships for trips."""
    logger.info("Linking trip origins and destinations...")

    query = """
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
    """

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        count = record["TripsLinked"] if record else 0
        logger.info(f"Linked {count} trips to their origin/destination stations.")
    driver.close()


def create_next_stop_chain():
    """Create NEXT_STOP relationships between consecutive stops."""
    logger.info("Creating NEXT_STOP chain...")

    query = """
    // Match consecutive stops in each trip
    MATCH (t:Trip)-[r1:STOPS_AT]->(s1:Station)
    MATCH (t)-[r2:STOPS_AT]->(s2:Station)
    WHERE r2.stop_sequence = r1.stop_sequence + 1

    // Create NEXT_STOP edge between consecutive stations
    MERGE (s1)-[ns:NEXT_STOP {trip_id: t.id}]->(s2)

    // Copy the times from the STOPS_AT relationships
    SET ns.departure_time = r1.departure_time,
        ns.arrival_time = r2.arrival_time,
        ns.date = t.date
    
    RETURN count(ns) as RelationshipsCreated
    """

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        count = record["RelationshipsCreated"] if record else 0
        logger.info(f"Created {count} NEXT_STOP relationships.")
    driver.close()
