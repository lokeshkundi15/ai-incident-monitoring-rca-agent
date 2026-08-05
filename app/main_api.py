import sys
import os
from fastapi import FastAPI, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import run_pipeline_async
from app.idempotency import check_and_register_incident, save_completed_incident

# API Key Security Setup
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_key = os.getenv("WEBHOOK_API_KEY", "rca_agent_sec_key_prod_2026")
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-API-Key header."
        )
    return api_key

app = FastAPI(
    title="AI Incident Monitoring & RCA Agent API",
    description="Production Webhook Listener with API Key Auth & Idempotency Store",
    version="4.0.0"
)

class AlertPayload(BaseModel):
    incident_id: str
    service_name: str
    alert_type: str
    severity: Optional[str] = "CRITICAL"

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "RCA-Agent-API", "version": "4.0.0"}

@app.post("/api/v1/alerts/trigger")
async def trigger_incident_webhook(
    payload: AlertPayload,
    authenticated: str = Depends(verify_api_key)
):
    """
    Authenticated & Idempotent Webhook endpoint. 
    Prevents duplicate LLM analysis if incident was already processed.
    """
    try:
        # 1. Idempotency Check
        cached_result = check_and_register_incident(payload.incident_id, payload.service_name)
        if cached_result:
            print(f"⚡ Duplicate Alert Detected for {payload.incident_id}. Returning cached RCA without calling LLM.")
            return cached_result

        print(f"🔒 Processing New Alert: Incident {payload.incident_id} on {payload.service_name}")
        
        # 2. Execute Async LangGraph RCA Agent
        result = await run_pipeline_async(
            incident_id=payload.incident_id,
            service_name=payload.service_name
        )
        
        # 3. Save to Idempotency Store
        save_completed_incident(
            incident_id=result["incident_id"],
            analysis=result["root_cause_analysis"],
            grounding_passed=result["grounding_passed"]
        )

        return {
            "status": "SUCCESS",
            "incident_id": result["incident_id"],
            "grounding_passed": result["grounding_passed"],
            "root_cause_analysis": result["root_cause_analysis"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RCA Agent Execution Failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)