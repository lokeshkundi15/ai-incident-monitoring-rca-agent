import os
import sqlite3
from typing import Optional, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data", "simulated")
os.makedirs(DB_DIR, exist_ok=True)
IDEMPOTENCY_DB_PATH = os.path.join(DB_DIR, "idempotency_store.db")

def init_idempotency_db():
    """Initialize SQLite table for tracking incident execution states."""
    conn = sqlite3.connect(IDEMPOTENCY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_states (
            incident_id TEXT PRIMARY KEY,
            service_name TEXT,
            status TEXT,
            root_cause_analysis TEXT,
            grounding_passed INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def check_and_register_incident(incident_id: str, service_name: str) -> Optional[Dict[str, Any]]:
    """
    Checks if incident already exists.
    - If COMPLETED, returns cached result to prevent duplicate LLM execution.
    - If NEW, registers as 'PROCESSING' and returns None.
    """
    init_idempotency_db()
    conn = sqlite3.connect(IDEMPOTENCY_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, root_cause_analysis, grounding_passed FROM incident_states WHERE incident_id = ?", (incident_id,))
    row = cursor.fetchone()
    
    if row:
        status, analysis, grounding = row
        conn.close()
        if status == "COMPLETED":
            return {
                "status": "DUPLICATE_CACHED",
                "incident_id": incident_id,
                "grounding_passed": bool(grounding),
                "root_cause_analysis": analysis
            }
        elif status == "PROCESSING":
            return {
                "status": "ALREADY_PROCESSING",
                "incident_id": incident_id,
                "root_cause_analysis": "Incident is currently being triaged by another worker."
            }
            
    # Register new incident
    cursor.execute("""
        INSERT OR REPLACE INTO incident_states (incident_id, service_name, status, root_cause_analysis, grounding_passed)
        VALUES (?, ?, 'PROCESSING', NULL, 0)
    """, (incident_id, service_name))
    conn.commit()
    conn.close()
    return None

def save_completed_incident(incident_id: str, analysis: str, grounding_passed: bool):
    """Updates incident status to COMPLETED and stores final RCA analysis."""
    conn = sqlite3.connect(IDEMPOTENCY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE incident_states 
        SET status = 'COMPLETED', root_cause_analysis = ?, grounding_passed = ?
        WHERE incident_id = ?
    """, (analysis, 1 if grounding_passed else 0, incident_id))
    conn.commit()
    conn.close()