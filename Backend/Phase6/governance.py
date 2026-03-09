import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. DATABASE CONNECTION & AUDIT LOGGING
# ==========================================
NEON_URL = os.getenv("NEON_DATABASE_URL")

if not NEON_URL:
    raise ValueError("Missing NEON_DATABASE_URL in .env file.")

def get_db_connection():
    """Creates a secure connection to the Neon Serverless Postgres DB."""
    return psycopg2.connect(NEON_URL)

def log_audit_event(user_id: str, action: str, target_resource: str, metadata: dict = None):
    """Writes an immutable audit record directly into the Neon Cloud Database."""
    timestamp = datetime.now().isoformat()
    meta_json = json.dumps(metadata) if metadata else "{}"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_logs (timestamp, user_id, action, resource, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (timestamp, user_id, action, target_resource, meta_json))
        print(f"[CLOUD AUDIT] {timestamp} | User: {user_id} | Action: {action}")
    except Exception as e:
        print(f"[ERROR] Failed to write cloud audit log to Neon: {e}")

# ==========================================
# 2. MODEL & VERSION REGISTRY
# ==========================================
class ModelRegistry:
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
# 3. ROLE-BASED ACCESS CONTROL (NEON DB DB)
# ==========================================
security_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    """Validates the incoming API token directly against the Neon Database."""
    token = credentials.credentials
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
               
                cursor.execute("""
                    SELECT user_id, role FROM api_users WHERE token = %s AND is_active = TRUE
                """, (token,))
                user = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] Database authentication failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during authentication.")
    
    
    if not user:
        log_audit_event("UNKNOWN_USER", "FAILED_LOGIN_ATTEMPT", "API")
        raise HTTPException(status_code=401, detail="Invalid, missing, or revoked authentication token.")
    
    return user

def require_role(allowed_roles: list[str]):
    """FastAPI Dependency to lock down endpoints by database role."""
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            log_audit_event(user["user_id"], "UNAUTHORIZED_ACCESS_ATTEMPT", f"Required: {allowed_roles}")
            raise HTTPException(status_code=403, detail="Permission denied.")
        return user
    return role_checker

# ==========================================
# 4. CLOUD DATA RETENTION & CONSENT
# ==========================================
def check_consent_status(node_id: str):
    """Checks the Neon database to see if a descendant revoked access to this record."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT status FROM consent_registry WHERE node_id = %s
                """, (node_id,))
                result = cursor.fetchone()
                
        if result and result.get("status") == "REVOKED":
            log_audit_event("SYSTEM", "CONSENT_ENFORCED_BLOCK", f"Node: {node_id}")
            raise HTTPException(
                status_code=451, 
                detail="Unavailable For Legal Reasons: Descendant has revoked consent."
            )
            
    except HTTPException:
        raise 
    except Exception:
        pass 
        
    return True
