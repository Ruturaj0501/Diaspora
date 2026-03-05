import sqlite3
import json
from datetime import datetime
from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ==========================================
# 1. DATABASE AUDIT LOGGING (SQLITE)
# ==========================================
# We connect to the same SQLite vault used in Phase 4, or create a new one.
AUDIT_DB_PATH = "dirp_hybrid_vault.db"

def init_audit_db():
    """Ensures the audit table exists on startup."""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()


init_audit_db()

def log_audit_event(user_id: str, action: str, target_resource: str, metadata: dict = None):
    """Writes an immutable audit record directly into the SQLite database."""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    meta_json = json.dumps(metadata) if metadata else "{}"
    
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, user_id, action, resource, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, user_id, action, target_resource, meta_json))
    
    conn.commit()
    conn.close()
    
    
    print(f"[AUDIT] {timestamp} | User: {user_id} | Action: {action} | Target: {target_resource}")


# ==========================================
# 2. MODEL & VERSION REGISTRY
# ==========================================
class ModelRegistry:
    """
    Tracks exactly which AI models are currently approved for production.
    If a model degrades, you update this registry and the whole system shifts.
    """
    CURRENT_PRODUCTION_MODELS = {
        "ocr_engine": "mistral-ocr-latest",
        "extraction_engine": "mistral-small-latest",
        "embedding_model": "huggingface/all-MiniLM-L6-v2",
        "copilot_llm": "llama3:latest"
    }

    @classmethod
    def get_provenance(cls) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "models_used": cls.CURRENT_PRODUCTION_MODELS
        }


# ==========================================
# 3. ROLE-BASED ACCESS CONTROL (RBAC)
# ==========================================
security_scheme = HTTPBearer()


MOCK_USERS = {
    "token_admin_999": {"user_id": "admin_01", "role": "ADMIN"},
    "token_research_123": {"user_id": "historian_sarah", "role": "RESEARCHER"},
    "token_descendant_456": {"user_id": "descendant_marcus", "role": "DESCENDANT"}
}

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    """Validates the incoming API token and identifies the user."""
    token = credentials.credentials
    user = MOCK_USERS.get(token)
    
    if not user:
        log_audit_event("UNKNOWN_USER", "FAILED_LOGIN_ATTEMPT", "API")
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token.")
    
    return user

def require_role(allowed_roles: list[str]):
    """Dependency injector to lock down specific FastAPI endpoints."""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            log_audit_event(user["user_id"], "UNAUTHORIZED_ACCESS_ATTEMPT", f"Required Roles: {allowed_roles}")
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action.")
        return user
    return role_checker


# ==========================================
# 4. DATA RETENTION & CONSENT ENFORCEMENT
# ==========================================
def check_consent_status(node_id: str):
    """
    Before returning an identity record, check if a descendant has revoked consent.
    """
   
    revoked_nodes = ["doc_entity_1710000_1"] 
    if node_id in revoked_nodes:
        log_audit_event("SYSTEM", "CONSENT_ENFORCED_BLOCK", f"Node: {node_id}")
        raise HTTPException(
            status_code=451, 
            detail="Unavailable For Legal Reasons: Descendant has revoked consent for this record."
        )
    return True