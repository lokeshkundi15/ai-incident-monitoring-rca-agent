import sys
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main_api import app
from agents.nodes import ingest_incident_node, verify_grounding_node
from app.idempotency import check_and_register_incident, save_completed_incident

client = TestClient(app)

# 1. Test Authentication (Phase 3)
def test_webhook_authentication_missing_key():
    response = client.post("/api/v1/alerts/trigger", json={
        "incident_id": "TEST-INC-401",
        "service_name": "order-service",
        "alert_type": "CRITICAL"
    })
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["detail"]

def test_webhook_authentication_invalid_key():
    response = client.post(
        "/api/v1/alerts/trigger",
        headers={"X-API-Key": "invalid_wrong_key"},
        json={
            "incident_id": "TEST-INC-401",
            "service_name": "order-service",
            "alert_type": "CRITICAL"
        }
    )
    assert response.status_code == 401

# 2. Test Idempotency Behavior (Phase 4)
def test_idempotency_store_caching():
    inc_id = "TEST-INC-IDEMPOTENT-001"
    service = "order-service"
    
    # Register New Incident
    res1 = check_and_register_incident(inc_id, service)
    assert res1 is None # First time register returns None
    
    # Save Completed Analysis
    save_completed_incident(inc_id, "ROOT CAUSE: Test DB Pool Exhaustion", True)
    
    # Register Duplicate Incident
    res2 = check_and_register_incident(inc_id, service)
    assert res2 is not None
    assert res2["status"] == "DUPLICATE_CACHED"
    assert "ROOT CAUSE: Test DB Pool Exhaustion" in res2["root_cause_analysis"]

# 3. Test Grounding Safeguard Logic (Phase 1 & 2)
@pytest.mark.asyncio
async def test_verify_grounding_node_pass():
    state = {
        "incident_id": "TEST-GROUND-01",
        "raw_logs": "2026-08-04 [ERROR] sqlalchemy.exc.TimeoutError: QueuePool limit overflowed",
        "root_cause_analysis": "ROOT CAUSE: QueuePool timeout overflow detected.",
        "grounding_passed": False
    }
    updated_state = await verify_grounding_node(state)
    assert updated_state["grounding_passed"] is True

@pytest.mark.asyncio
async def test_verify_grounding_node_fail():
    state = {
        "incident_id": "TEST-GROUND-02",
        "raw_logs": "2026-08-04 [INFO] Normal application operation",
        "root_cause_analysis": "ROOT CAUSE: Imaginary hallucinated error",
        "grounding_passed": False
    }
    updated_state = await verify_grounding_node(state)
    assert updated_state["grounding_passed"] is False

# 4. Test Mocked Async Pipeline Trigger Execution
@patch("app.main_api.run_pipeline_async", new_callable=AsyncMock)
def test_authenticated_webhook_success(mock_run_pipeline):
    mock_run_pipeline.return_value = {
        "incident_id": "TEST-INC-200",
        "service_name": "payment-service",
        "grounding_passed": True,
        "root_cause_analysis": "ROOT CAUSE: Mocked Root Cause Analysis Success"
    }
    
    response = client.post(
        "/api/v1/alerts/trigger",
        headers={"X-API-Key": "rca_agent_sec_key_prod_2026"},
        json={
            "incident_id": "TEST-INC-200",
            "service_name": "payment-service",
            "alert_type": "CRITICAL"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["incident_id"] == "TEST-INC-200"
    assert response.json()["grounding_passed"] is True