import sqlite3
import json
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

class HybridDatabaseManager:
    def __init__(self):
        
        self.sqlite_conn = sqlite3.connect("Phase4/dirp_evidence.db", check_same_thread=False)
        self._setup_sqlite()

        
        uri = os.getenv("NEO4J_URI", "neo4j+s://2de52e2c.databases.neo4j.io")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))

    def _setup_sqlite(self):
        """Creates the local vault for heavy vectors and bounding boxes."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_vault (
                node_id TEXT PRIMARY KEY,
                embedding JSON,
                evidence JSON
            )
        """)
        self.sqlite_conn.commit()

    def ingest_node(self, node_data: dict):
        """Routes heavy data to SQLite and relational data to Neo4j."""
        node_id = node_data["node_id"]
        data = node_data["normalized_data"]
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            INSERT INTO evidence_vault (node_id, embedding, evidence)
            VALUES (?, ?, ?)
            ON CONFLICT(node_id) DO NOTHING
        """, (
            node_id, 
            json.dumps(data.get("embedding", [])), 
            json.dumps(node_data.get("evidence", []))
        ))
        self.sqlite_conn.commit()

        query = """
        MERGE (p:Person {node_id: $node_id})
        SET p.standardized_name = $standardized_name,
            p.phonetic_key = $phonetic_key,
            p.date_start = $date_start,
            p.normalized_place = $normalized_place,
            p.owner = $owner,
            p.plantation = $plantation
        """
        params = {
            "node_id": node_id,
            "standardized_name": data.get("standardized_name"),
            "phonetic_key": data.get("phonetic_key"),
            "date_start": data.get("date_start"),
            "normalized_place": data.get("normalized_place"),
            "owner": data.get("owner"),
            "plantation": data.get("plantation")
        }
        
        with self.neo4j_driver.session() as session:
            session.run(query, **params)

    def write_hypothesis_edge(self, edge: dict):
        """Draws the ML Ranker's proposed match in Neo4j."""
        query = query = """
        MATCH (a:Person {node_id: $source_id})
        MATCH (b:Person {node_id: $target_id})
        // MERGE without the ID ensures only ONE edge is ever drawn between them
        MERGE (a)-[r:POTENTIAL_MATCH]->(b)
        SET r.edge_id = $edge_id,
            r.confidence_score = $score,
            r.explanation = $explanation,
            r.status = $status
        """
        with self.neo4j_driver.session() as session:
            session.run(query, 
                source_id=edge["source_node_id"],
                target_id=edge["target_node_id"],
                edge_id=edge["edge_id"],
                score=edge["confidence_score"],
                explanation=edge["explanation"],
                status=edge["status"].value
            )

    def close(self):
        self.sqlite_conn.close()
        self.neo4j_driver.close()