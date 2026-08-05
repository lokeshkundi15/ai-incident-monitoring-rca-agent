import sys
import os
import sqlite3
import asyncio
import json
import pandas as pd
import streamlit as st

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import build_telemetry
from agents.graph import run_pipeline_async

# Page Configuration
st.set_page_config(
    page_title="AI System Monitoring & RCA Agent",
    page_icon="🤖",
    layout="wide"
)

# Set Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE_PATH = os.path.join(BASE_DIR, "data", "simulated", "system_telemetry.db")
LOG_FILE_PATH = os.path.join(BASE_DIR, "data", "simulated", "app_service.log")
TRACE_FILE_PATH = os.path.join(BASE_DIR, "logs", "agent_execution.json")

st.title("🤖 Enterprise AI System Monitoring & RCA Agent")
st.caption("Production Level-1 Incident Triage Dashboard | LangGraph + FastMCP + Multi-Variate Telemetry")
st.divider()

# Sidebar Controls
st.sidebar.header("🕹️ Incident Simulation Control")
selected_scenario = st.sidebar.selectbox(
    "Select Target Failure Scenario",
    ["Scenario A: DB Pool Exhaustion", "Scenario B: Memory Leak (Heap OOM)", "Scenario C: Upstream API Read Timeout"]
)

if st.sidebar.button("⚙️ Switch & Regenerate Telemetry", use_container_width=True):
    scenario_code = "A"
    if "Scenario B" in selected_scenario:
        scenario_code = "B"
    elif "Scenario C" in selected_scenario:
        scenario_code = "C"
        
    build_telemetry(scenario_code)
    st.sidebar.success(f"Generated {selected_scenario} Telemetry!")

st.sidebar.divider()
run_pipeline_btn = st.sidebar.button("🚀 Trigger AI RCA Execution", type="primary", use_container_width=True)

# Dashboard Columns for Metrics & Logs
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Multi-Variate Telemetry Metrics")
    if os.path.exists(DB_FILE_PATH):
        conn = sqlite3.connect(DB_FILE_PATH)
        df_metrics = pd.read_sql_query("SELECT * FROM metrics", conn)
        conn.close()
        
        # Plot Charts
        st.line_chart(df_metrics, x="timestamp", y=["cpu_usage_pct", "memory_usage_pct", "http_5xx_rate_pct"])
        st.dataframe(df_metrics, use_container_width=True)
    else:
        st.warning("No metrics database found. Click Regenerate Telemetry in sidebar.")

with col2:
    st.subheader("📄 Live Application Stack Trace Logs")
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            log_data = f.read()
        st.code(log_data, language="log")
    else:
        st.warning("No log files found. Click Regenerate Telemetry in sidebar.")

st.divider()

# Pipeline Execution Section
if run_pipeline_btn:
    st.subheader("⚡ LangGraph Orchestration & AI Root Cause Report")
    
    with st.spinner("Executing Async LangGraph Pipeline via FastMCP Tools..."):
        # Run async graph inside Streamlit
        output = asyncio.run(run_pipeline_async(
            incident_id="INC-" + selected_scenario[9],
            service_name="order-service"
        ))
    
    # Status Indicators
    m1, m2, m3 = st.columns(3)
    m1.metric("Incident Status", "TRIAGED")
    m2.metric("Grounding Check", "PASSED ✅" if output["grounding_passed"] else "FAILED ⚠️")
    m3.metric("Target Service", output["service_name"])

    st.success("✅ Root Cause Analysis Generated Successfully!")
    st.markdown(output["root_cause_analysis"])

    # Human-in-the-Loop Safeguard
    st.divider()
    st.subheader("🛡️ Human-in-the-Loop Remediation Safeguard")
    st.warning("⚠️ Action Required: Review recommended mitigation action before executing on infrastructure.")
    
    col_acc, col_rej = st.columns(2)
    with col_acc:
        if st.button("✅ APPROVE & EXECUTE REMEDIATION", use_container_width=True, type="primary"):
            st.balloons()
            st.success("SUCCESS: Action executed safely by System Operator.")
    with col_rej:
        if st.button("❌ REJECT / ESCALATE TO SENIOR SRE", use_container_width=True):
            st.error("ACTION ABORTED: Incident escalated to On-Call Engineer.")

# Observability Audit Panel
if os.path.exists(TRACE_FILE_PATH):
    st.divider()
    with st.expander("🔍 Observability & Execution Latency Traces (structlog)"):
        traces = []
        with open(TRACE_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    traces.append(json.loads(line.strip()))
        
        if traces:
            df_traces = pd.DataFrame(traces)
            st.dataframe(df_traces.tail(10), use_container_width=True)