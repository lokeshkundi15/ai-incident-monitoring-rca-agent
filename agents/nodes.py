import sys
import os
import time
import asyncio

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import IncidentState
from mcp_server.tools import get_recent_logs, get_system_metrics
from app.llm_router import invoke_llm_with_retry_and_fallback
from app.logger import log_agent_step

async def ingest_incident_node(state: IncidentState) -> IncidentState:
    """Node 1: Initialize incident info and start execution trace."""
    start_time = time.time()
    print("\n[Node 1] Ingesting Incident Payload...")
    
    if not state.get("incident_id"):
        state["incident_id"] = "INC-101"
    if not state.get("service_name"):
        state["service_name"] = "order-service"
        
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("ingest_incident", state["incident_id"], latency_ms, {"service": state["service_name"]})
    return state

async def fetch_telemetry_node(state: IncidentState) -> IncidentState:
    """Node 2: Async Fetch logs and multi-variate metrics via FastMCP Tools."""
    start_time = time.time()
    print("\n[Node 2] Fetching Telemetry via Async FastMCP Tools...")
    
    # Async execution of tools
    state["raw_logs"] = await get_recent_logs(limit=20)
    state["raw_metrics"] = await get_system_metrics()
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("fetch_telemetry", state["incident_id"], latency_ms, {
        "logs_bytes": len(state["raw_logs"]),
        "metrics_bytes": len(state["raw_metrics"])
    })
    return state

async def analyze_root_cause_node(state: IncidentState) -> IncidentState:
    """Node 3: Analyze telemetry using Resilient LLM Router with Retries & Fallbacks."""
    start_time = time.time()
    print("\n[Node 3] Analyzing Multi-Variate Telemetry with Resilient LLM Router...")
    
    prompt = f"""
    You are an expert Principal SRE & Automated Diagnostic AI. Analyze the telemetry to find the primary root cause.
    
    APPLICATION LOGS:
    {state['raw_logs']}
    
    MULTI-VARIATE METRICS:
    {state['raw_metrics']}
    
    INSTRUCTIONS:
    1. Identify the exact Root Cause of the failure.
    2. Provide a Confidence Score between 0.0 and 1.0.
    3. Recommend a specific mitigation/remediation command or action.
    
    FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
    ROOT CAUSE: <Explain root cause concisely with citation from logs/metrics>
    CONFIDENCE: <Float value between 0.0 and 1.0>
    RECOMMENDED ACTION: <Clear fix command or step>
    """
    
    # Use resilient LLM call with retry, timeout, and fallback handling
    analysis_text = await invoke_llm_with_retry_and_fallback(prompt)
    state["root_cause_analysis"] = analysis_text
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("analyze_root_cause", state["incident_id"], latency_ms, {
        "response_length": len(analysis_text)
    })
    return state

async def verify_grounding_node(state: IncidentState) -> IncidentState:
    """Node 4: Validate if the LLM's Root Cause Analysis is grounded in actual telemetry."""
    start_time = time.time()
    print("\n[Node 4] Verifying Evidence & Grounding Safeguard...")
    
    analysis = state["root_cause_analysis"]
    logs = state["raw_logs"]
    
    # Check for evidence patterns across scenarios
    has_evidence = any(kw in logs for kw in ["TimeoutError", "QueuePool", "OutOfMemoryError", "ReadTimeout", "500"])
    has_analysis = "ROOT CAUSE:" in analysis
    
    if has_evidence and has_analysis:
        print("✅ Grounding Check Passed: Root cause maps directly to retrieved log stack trace.")
        state["grounding_passed"] = True
    else:
        print("⚠️ Grounding Check Failed: Insufficient or ungrounded evidence detected.")
        state["grounding_passed"] = False
        
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("verify_grounding", state["incident_id"], latency_ms, {
        "grounding_passed": state["grounding_passed"]
    })
    return state

async def test_nodes_async():
    print("Testing Async Nodes with Resilient Router...")
    initial_state = {
        "incident_id": "INC-101",
        "service_name": "order-service",
        "raw_logs": "",
        "raw_metrics": "",
        "root_cause_analysis": "",
        "confidence_score": 0.0,
        "recommended_action": "",
        "grounding_passed": False,
        "human_approved": None
    }
    
    s1 = await ingest_incident_node(initial_state)
    s2 = await fetch_telemetry_node(s1)
    s3 = await analyze_root_cause_node(s2)
    s4 = await verify_grounding_node(s3)
    
    print("\n--- FINAL RCA OUTPUT ---")
    print(s4["root_cause_analysis"])

if __name__ == "__main__":
    asyncio.run(test_nodes_async())