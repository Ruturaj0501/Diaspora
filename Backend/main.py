import os
import shutil
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from Phase4.models import GraphNode, EdgeStatus
from Phase4.database import HybridDatabaseManager
from Phase4.ranker import HybridCandidateRanker

from pipeline import process_document_end_to_end
from Phase5.copilot import load_records, retrieve, build_context, generate_report, save_output

from Phase6.governance import require_role, log_audit_event, ModelRegistry, check_consent_status

app = FastAPI(title="DIRP Hybrid Graph API (Secured)", version="1.0")

# ==========================================
# 0. CORS & DEPLOYMENT CONFIGURATION
# ==========================================

origins = [
    "http://localhost:3000",
    "https://diaspora-one.vercel.app", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

@app.get("/")
def health_check():
    """
    Render looks for this exact endpoint to verify the server is alive.
    """
    return {
        "status": "online", 
        "message": "Diaspora API is running.",
        "active_models": ModelRegistry.get_provenance()
    }

# ==========================================
# DATABASE & RANKER INITIALIZATION
# ==========================================
db = HybridDatabaseManager()
ranker = HybridCandidateRanker(review_threshold=0.70)

# -----------------------------
# 1. DATA INGESTION (ADMIN ONLY)
# -----------------------------
@app.post("/api/v1/graph/ingest", summary="Ingest Nodes to Hybrid Storage")
def ingest_nodes(
    nodes: List[GraphNode],
    user: dict = Depends(require_role(["ADMIN"])) # Strict RBAC
):
    # Audit Log the action
    log_audit_event(user["user_id"], "INGEST_NODES", "HybridDatabase", {"count": len(nodes)})
    
    for node in nodes:
        db.ingest_node(node.model_dump())
        
    return {"status": "success", "message": f"Ingested {len(nodes)} records."}

# -----------------------------
# 2. THE AI RESOLUTION ENGINE (ADMIN ONLY)
# -----------------------------
def get_node_embedding(node_id: str) -> list:
    cursor = db.sqlite_conn.cursor()
    cursor.execute("SELECT embedding FROM evidence_vault WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()
    return json.loads(row[0]) if row and row[0] else []

@app.post("/api/v1/graph/resolve", summary="Run Neo4j Blocking & ML Ranking")
def run_resolution(user: dict = Depends(require_role(["ADMIN"]))):
    log_audit_event(user["user_id"], "RUN_RESOLUTION", "Neo4j/SQLite")
    
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
# 3. THE REVIEWER UI ENDPOINTS (RESEARCHER & ADMIN)
# -----------------------------
@app.get("/api/v1/review/queue", summary="Fetch UI Queue (Joined Data)")
def get_review_queue(user: dict = Depends(require_role(["ADMIN", "RESEARCHER"]))):
    log_audit_event(user["user_id"], "FETCH_REVIEW_QUEUE", "Neo4j")
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
            
            # PHASE 6: Consent check before displaying node data
            check_consent_status(source_id)
            check_consent_status(target_id)
            
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

@app.post("/api/v1/review/decision/{edge_id}", summary="Submit Human Decision")
def submit_decision(
    edge_id: str, 
    payload: ReviewDecision,
    user: dict = Depends(require_role(["ADMIN", "RESEARCHER"]))
):
    if payload.decision.upper() not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Must be APPROVE or REJECT.")
        
    log_audit_event(user["user_id"], f"SUBMIT_DECISION_{payload.decision.upper()}", f"Edge:{edge_id}")
        
    query = """
    MATCH ()-[r:POTENTIAL_MATCH {edge_id: $edge_id}]->()
    SET r.status = $status, r.reviewed_by = $reviewer_id
    """
    with db.neo4j_driver.session() as session:
        session.run(query, edge_id=edge_id, status=payload.decision.upper(), reviewer_id=user["user_id"])
        
    return {"message": f"Edge {edge_id} updated in Neo4j."}

# -----------------------------
# 4. MASTER PIPELINE ENDPOINT
# -----------------------------
@app.post("/api/v1/pipeline/upload", summary="Upload Image & Run Full Pipeline")
async def upload_and_process_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    user: dict = Depends(require_role(["ADMIN", "RESEARCHER"]))
):
    log_audit_event(user["user_id"], "UPLOAD_DOCUMENT", f"File:{file.filename}")
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_document_end_to_end, file_path)
    
    return {
        "status": "processing",
        "message": f"File '{file.filename}' received. Pipeline running.",
        "ai_provenance": ModelRegistry.get_provenance()
    }

# -----------------------------
# 5. THE RESEARCH COPILOT ENDPOINT
# -----------------------------
class CopilotQuery(BaseModel):
    question: str

@app.post("/api/v1/copilot/ask", summary="Ask the DIRP Research Copilot")
def ask_copilot(
    payload: CopilotQuery,
    user: dict = Depends(require_role(["ADMIN", "RESEARCHER"]))
):
    log_audit_event(user["user_id"], "COPILOT_QUERY", "Llama3", {"question": payload.question})
    
    records = load_records()
    if not records:
        raise HTTPException(status_code=404, detail="No extracted records found.")
        
    results = retrieve(payload.question, records)
    if not results:
        return {"report": "No evidence found.", "evidence_used": []}
        
    context, structured_evidence = build_context(results)
    
    try:
        narrative = generate_report(payload.question, context)
        save_output(payload.question, narrative, structured_evidence)
        
        return {
            "question": payload.question,
            "report": narrative,
            "evidence_used": structured_evidence,
            "ai_provenance": ModelRegistry.get_provenance() 
        }
    except Exception as e:
        log_audit_event(user["user_id"], "COPILOT_ERROR", "Llama3", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

