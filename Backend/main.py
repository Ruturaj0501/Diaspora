import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
import json

from Phase4.models import GraphNode, EdgeStatus
from Phase4.database import HybridDatabaseManager
from Phase4.ranker import HybridCandidateRanker


from pipeline import process_document_end_to_end


from Phase5.copilot import load_records, retrieve, build_context, generate_report, save_output

app = FastAPI(title="DIRP Hybrid Graph API", version="1.0")

db = HybridDatabaseManager()
ranker = HybridCandidateRanker(review_threshold=0.70)

# -----------------------------
# 1. DATA INGESTION
# -----------------------------
@app.post("/api/v1/graph/ingest", summary="Ingest Nodes to Hybrid Storage")
def ingest_nodes(nodes: List[GraphNode]):
    """Splits incoming data: Heavy evidence to SQLite, relationships to Neo4j."""
    for node in nodes:
        db.ingest_node(node.model_dump())
    return {"status": "success", "message": f"Ingested {len(nodes)} records into Neo4j + SQLite."}

# -----------------------------
# 2. THE AI RESOLUTION ENGINE
# -----------------------------
def get_node_embedding(node_id: str) -> list:
    """Helper: Fetches the heavy 384-dimensional vector from the SQLite vault."""
    cursor = db.sqlite_conn.cursor()
    cursor.execute("SELECT embedding FROM evidence_vault WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else []

@app.post("/api/v1/graph/resolve", summary="Run Neo4j Blocking & ML Ranking")
def run_resolution():
    """
    The Core Pipeline:
    1. Neo4j finds overlapping candidates (Blocking).
    2. SQLite provides the embeddings (ML Scoring).
    3. Neo4j stores the Hypothesis Edges.
    """
    new_edges_count = 0
    
    query = """
    MATCH (a:Person), (b:Person)
    WHERE a.node_id < b.node_id AND (
        a.phonetic_key = b.phonetic_key OR 
        a.owner = b.owner OR 
        a.plantation = b.plantation
    )
    RETURN a, b
    """
    with db.neo4j_driver.session() as session:
        result = session.run(query)
        
        for record in result:
            node_a_data = dict(record["a"])
            node_b_data = dict(record["b"])
            
            node_a_data["embedding"] = get_node_embedding(node_a_data["node_id"])
            node_b_data["embedding"] = get_node_embedding(node_b_data["node_id"])
            
            edge = ranker.evaluate_pair(node_a_data, node_b_data)
            
            if edge.status != EdgeStatus.REJECTED:
                db.write_hypothesis_edge(edge.model_dump())
                new_edges_count += 1

    return {"message": "Resolution complete.", "hypotheses_generated": new_edges_count}

# -----------------------------
# 3. THE REVIEWER UI ENDPOINTS
# -----------------------------
@app.get("/api/v1/review/queue", summary="Fetch UI Queue (Joined Data)")
def get_review_queue():
    """
    Pulls the relationships from Neo4j and joins them with the 
    bounding box evidence from SQLite so the UI can render everything.
    """
    queue = []
    
    query = """
    MATCH (a:Person)-[r:POTENTIAL_MATCH {status: 'PENDING_REVIEW'}]->(b:Person)
    RETURN a, r, b
    """
    with db.neo4j_driver.session() as session:
        result = session.run(query)
        cursor = db.sqlite_conn.cursor()
        
        for record in result:
            source_id = record["a"]["node_id"]
            target_id = record["b"]["node_id"]
            
            cursor.execute("SELECT evidence FROM evidence_vault WHERE node_id IN (?, ?)", (source_id, target_id))
            evidence_rows = cursor.fetchall()
            
            queue.append({
                "edge_data": dict(record["r"]),
                "source_entity": dict(record["a"]),
                "target_entity": dict(record["b"]),
                "evidence": [json.loads(row[0]) for row in evidence_rows if row[0]]
            })
            
    return {"pending_reviews": queue, "count": len(queue)}

class ReviewDecision(BaseModel):
    decision: str  
    reviewer_id: str

@app.post("/api/v1/review/decision/{edge_id}", summary="Submit Human Decision")
def submit_decision(edge_id: str, payload: ReviewDecision):
    """Updates the final decision directly in Neo4j."""
    if payload.decision.upper() not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Must be APPROVE or REJECT.")
        
    query = """
    MATCH ()-[r:POTENTIAL_MATCH {edge_id: $edge_id}]->()
    SET r.status = $status, r.reviewed_by = $reviewer_id
    """
    with db.neo4j_driver.session() as session:
        session.run(query, edge_id=edge_id, status=payload.decision.upper(), reviewer_id=payload.reviewer_id)
        
    return {"message": f"Edge {edge_id} updated in Neo4j."}

# -----------------------------
# 4. MASTER PIPELINE ENDPOINT
# -----------------------------
@app.post("/api/v1/pipeline/upload", summary="Upload Image & Run Full Pipeline")
async def upload_and_process_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Receives an image from the UI, saves it, and triggers the full Phase 1->4 pipeline 
    in the background so the UI doesn't freeze waiting for the LLMs to finish.
    """
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_document_end_to_end, file_path)
    
    return {
        "status": "processing",
        "message": f"File '{file.filename}' received. Pipeline running in the background.",
        "file_path": file_path
    }

# -----------------------------
# 5. THE RESEARCH COPILOT ENDPOINT
# -----------------------------
class CopilotQuery(BaseModel):
    question: str

@app.post("/api/v1/copilot/ask", summary="Ask the DIRP Research Copilot")
def ask_copilot(payload: CopilotQuery):
    """
    Takes a question from the UI, searches the extracted documents, 
    and uses local Llama 3 to generate a strictly grounded historical report.
    """
    records = load_records()
    
    if not records:
        raise HTTPException(status_code=404, detail="No extracted records found. Run the extraction pipeline first.")
        

    results = retrieve(payload.question, records)
    
    if not results:
        return {
            "question": payload.question,
            "report": "No high-confidence evidence found in the current records for this query.",
            "evidence_used": []
        }
        
    
    context, structured_evidence = build_context(results)
    
    try:
       
        narrative = generate_report(payload.question, context)
        
       
        save_output(payload.question, narrative, structured_evidence)
        
        return {
            "question": payload.question,
            "report": narrative,
            "evidence_used": structured_evidence
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Llama 3 Generation failed: {str(e)}")
