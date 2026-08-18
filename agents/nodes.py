import sys
import os
import time
import asyncio
import re
import sqlite3
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import IncidentState
from agents.verifier import IndependentRCAVerifier
from mcp_server.tools import get_recent_logs, get_system_metrics
from app.llm_router import invoke_llm_with_retry_and_fallback
from app.logger import log_agent_step

# Shared verifier instance
verifier = IndependentRCAVerifier()
DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "simulated", "system_telemetry.db")

async def ingest_incident_node(state: IncidentState) -> IncidentState:
    start_time = time.time()
    if not state.get("incident_id"):
        state["incident_id"] = "INC-101"
    if not state.get("service_name"):
        state["service_name"] = "order-service"
        
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("ingest_incident", state["incident_id"], latency_ms, {"service": state["service_name"]})
    return state

async def fetch_telemetry_node(state: IncidentState) -> IncidentState:
    start_time = time.time()
    
    logs_output = await get_recent_logs(limit=20)
    metrics_str = await get_system_metrics()
    
    # Store logs as string
    state["raw_logs"] = "\n".join(logs_output) if isinstance(logs_output, list) else str(logs_output)
    state["raw_metrics"] = str(metrics_str)
    
    # Query structured metric rows directly from SQLite for verifier threshold rules
    structured_metrics: List[Dict[str, Any]] = []
    if os.path.exists(DB_FILE_PATH):
        try:
            conn = sqlite3.connect(DB_FILE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM metrics ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            structured_metrics = [dict(row) for row in rows]
            conn.close()
        except Exception:
            structured_metrics = []
            
    state["metrics_data"] = structured_metrics
    print(f"🔍 [Telemetry Ingest] Fetched {len(state['metrics_data'])} structured metric points for validation.")
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("fetch_telemetry", state["incident_id"], latency_ms, {
        "logs_bytes": len(str(state["raw_logs"])),
        "metrics_count": len(state["metrics_data"])
    })
    return state

async def analyze_root_cause_node(state: IncidentState) -> IncidentState:
    start_time = time.time()
    
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
    
    conf_match = re.search(r"CONFIDENCE:\s*([0-1](?:\.\d+)?)", analysis_text, re.IGNORECASE)
    state["confidence_score"] = float(conf_match.group(1)) if conf_match else 0.85

    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("analyze_root_cause", state["incident_id"], latency_ms, {
        "response_length": len(analysis_text),
        "confidence": state["confidence_score"]
    })
    return state

async def verify_grounding_node(state: IncidentState) -> IncidentState:
    """Safeguard: Runs the shared IndependentRCAVerifier ensuring logs are string."""
    start_time = time.time()
    
    rca_text = str(state.get("root_cause_analysis", ""))
    raw_logs = state.get("raw_logs", "")
    metrics_data = state.get("metrics_data", [])
    
    # Ensure logs is strictly a string for regex matching
    logs_str = "\n".join(raw_logs) if isinstance(raw_logs, list) else str(raw_logs)
    
    verification_res = verifier.verify_rca(
        rca_text=rca_text,
        logs=logs_str,
        metrics=metrics_data
    )
    
    is_verified = bool(verification_res.get("verified", False))
    state["grounding_passed"] = is_verified
    state["verification_details"] = verification_res
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("verify_grounding", state["incident_id"], latency_ms, {
        "grounding_passed": is_verified,
        "verification_score": verification_res.get("evidence_score", 0.0)
    })
    return state

async def fallback_conservative_analysis_node(state: IncidentState) -> IncidentState:
    start_time = time.time()
    state["root_cause_analysis"] = (
        "ROOT CAUSE: Automated LLM diagnosis failed independent evidence verification against telemetry signatures.\n"
        "CONFIDENCE: 0.30\n"
        "RECOMMENDED ACTION: Manual inspection required. Verify raw logs and system metrics directly."
    )
    state["confidence_score"] = 0.30
    state["grounding_passed"] = False
    
    latency_ms = (time.time() - start_time) * 1000
    log_agent_step("fallback_conservative_analysis", state["incident_id"], latency_ms, {
        "status": "fallback_applied"
    })
    return state