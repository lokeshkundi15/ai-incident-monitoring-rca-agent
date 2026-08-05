import sys
import os
import asyncio

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from agents.state import IncidentState
from agents.nodes import (
    ingest_incident_node,
    fetch_telemetry_node,
    analyze_root_cause_node,
    verify_grounding_node
)

def build_async_workflow():
    """Constructs the Async LangGraph orchestration graph."""
    builder = StateGraph(IncidentState)

    # Add Nodes
    builder.add_node("ingest_incident", ingest_incident_node)
    builder.add_node("fetch_telemetry", fetch_telemetry_node)
    builder.add_node("analyze_root_cause", analyze_root_cause_node)
    builder.add_node("verify_grounding", verify_grounding_node)

    # Add Sequential Edges
    builder.add_edge(START, "ingest_incident")
    builder.add_edge("ingest_incident", "fetch_telemetry")
    builder.add_edge("fetch_telemetry", "analyze_root_cause")
    builder.add_edge("analyze_root_cause", "verify_grounding")
    builder.add_edge("verify_grounding", END)

    return builder.compile()

async def run_pipeline_async(incident_id: str = "INC-101", service_name: str = "order-service"):
    rca_agent = build_async_workflow()
    initial_input = {
        "incident_id": incident_id,
        "service_name": service_name,
        "raw_logs": "",
        "raw_metrics": "",
        "root_cause_analysis": "",
        "confidence_score": 0.0,
        "recommended_action": "",
        "grounding_passed": False,
        "human_approved": None
    }
    
    # Async Graph Execution
    final_output = await rca_agent.ainvoke(initial_input)
    return final_output

if __name__ == "__main__":
    print("🚀 Running Async LangGraph Executable Pipeline...")
    output = asyncio.run(run_pipeline_async())
    print("\n" + "="*50)
    print("   COMPLETE ASYNC LANGGRAPH EXECUTION RESULT")
    print("="*50)
    print(f"Incident ID      : {output['incident_id']}")
    print(f"Service          : {output['service_name']}")
    print(f"Grounding Passed : {output['grounding_passed']}")
    print("\n[AI RCA REPORT]")
    print(output["root_cause_analysis"])
    print("="*50)