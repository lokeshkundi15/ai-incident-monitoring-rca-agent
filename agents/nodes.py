import sys
import os
import time
import asyncio
import re

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
    ROOT CAUSE: <Explain root cause concisely using exact error technical phrases from logs/metrics>
    CONFIDENCE: <Float value between 0.0 and 1.0>
    RECOMMENDED ACTION: <Clear fix command or step>
    """
    
    analysis_text = await invoke_llm_with_retry_and_fallback(
        prompt=prompt,
        incident_id=state["incident_id"]
    )
    state["root_cause_analysis"] = analysis_text
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("analyze_root_cause", state["incident_id"], latency_ms, {
        "response_length": len(analysis_text)
    })
    return state

async def verify_grounding_node(state: IncidentState) -> IncidentState:
    """Safeguard: Verifies if the RCA output is strictly grounded in raw telemetry."""
    start_time = time.time()
    print("\n[Node 4] Verifying Evidence & Grounding Safeguard...")
    
    rca_text = state.get("root_cause_analysis", "")
    raw_logs = state.get("raw_logs", "")
    
    # Extract keywords/technical terms from RCA
    keywords = [word.strip(".,;:\"'()[]{}").lower() for word in rca_text.split() if len(word) > 4]
    
    # Check evidence overlap
    matches = [kw for kw in set(keywords) if kw in raw_logs.lower()]
    
    # Grounding criteria: If hallucinated without matching evidence, fail it
    if len(matches) > 0:
        print(f"✅ Grounding Check Passed: {len(matches)} matching technical terms found in log evidence.")
        state["grounding_passed"] = True
    else:
        print("❌ Grounding Check Failed: RCA does not match telemetry evidence (Hallucination detected).")
        state["grounding_passed"] = False
        
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("verify_grounding", state["incident_id"], latency_ms, {
        "grounding_passed": state["grounding_passed"]
    })
    return state

async def fallback_conservative_analysis_node(state: IncidentState) -> IncidentState:
    """Fallback Node: Triggered via Conditional Edge when Grounding Safeguard fails."""
    start_time = time.time()
    print("\n[Fallback Node] Executing Safe Conservative Triage (Grounding Failed)...")
    
    state["root_cause_analysis"] = (
        "ROOT CAUSE: Automated LLM diagnosis could not be conclusively verified against raw logs.\n"
        "CONFIDENCE: 0.3\n"
        "RECOMMENDED ACTION: Manual inspection required. Verify raw logs and system metrics directly."
    )
    state["confidence_score"] = 0.3
    state["grounding_passed"] = False
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("fallback_conservative_analysis", state["incident_id"], latency_ms, {
        "status": "fallback_applied"
    })
    return state