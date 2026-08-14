import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main_api import app
from app.idempotency import check_and_register_incident, save_completed_incident, init_idempotency_db
from agents.nodes import verify_grounding_node

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_idempotency_db()

def test_webhook_authentication_missing_key():
    response = client.post("/api/v1/alerts/trigger", json={
        "incident_id": "TEST-01",
        "service_name": "order-service",
        "alert_type": "HIGH"
    })
    assert response.status_code == 401
    assert "Invalid or missing X-API-Key" in response.json()["detail"]

def test_webhook_authentication_invalid_key():
    response = client.post(
        "/api/v1/alerts/trigger",
        headers={"X-API-Key": "invalid_wrong_key"},
        json={
            "incident_id": "TEST-01",
            "service_name": "order-service",
            "alert_type": "HIGH"
        }
    )
    assert response.status_code == 401
    assert "Invalid or missing X-API-Key" in response.json()["detail"]

def test_idempotency_store_caching():
    inc_id = f"TEST-IDEM-{uuid.uuid4().hex[:8]}"
    service = "order-service"
    
    # 1. First registration must return None (new incident)
    res1 = check_and_register_incident(inc_id, service)
    assert res1 is None

    # 2. Save completed status
    save_completed_incident(inc_id, "ROOT CAUSE: Test DB Pool Exhaustion", True)

    # 3. Querying again with same ID must return cached status
    res2 = check_and_register_incident(inc_id, service)
    assert res2 is not None
    assert res2["status"] == "DUPLICATE_CACHED"
    assert res2["incident_id"] == inc_id

@pytest.mark.asyncio
async def test_verify_grounding_node_pass():
    state = {
        "incident_id": "TEST-GROUND-01",
        "raw_logs": "2026-08-04 [ERROR] HikariPool-1 - Connection is not available, request timed out after 30005ms.",
        "root_cause_analysis": "ROOT CAUSE: Database connection pool HikariPool exhausted.",
        "grounding_passed": False
    }
    updated_state = await verify_grounding_node(state)
    assert updated_state["grounding_passed"] is True

@pytest.mark.asyncio
async def test_verify_grounding_node_fail():
    state = {
        "incident_id": "TEST-GROUND-02",
        "raw_logs": "2026-08-04 [INFO] Normal application operation",
        "root_cause_analysis": "ROOT CAUSE: Imaginary hallucinated error with nonexistent words",
        "grounding_passed": False
    }
    updated_state = await verify_grounding_node(state)
    assert updated_state["grounding_passed"] is False

@patch("app.main_api.run_pipeline_async", new_callable=AsyncMock)
def test_authenticated_webhook_success(mock_run_pipeline):
    fresh_inc_id = f"TEST-WEBHOOK-{uuid.uuid4().hex[:8]}"
    mock_run_pipeline.return_value = {
        "incident_id": fresh_inc_id,
        "service_name": "payment-service",
        "grounding_passed": True,
        "root_cause_analysis": "ROOT CAUSE: Mocked Root Cause Analysis Success"
    }
    
    response = client.post(
        "/api/v1/alerts/trigger",
        headers={"X-API-Key": "rca_agent_sec_key_prod_2026"},
        json={
            "incident_id": fresh_inc_id,
            "service_name": "payment-service",
            "alert_type": "CRITICAL"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["incident_id"] == fresh_inc_id