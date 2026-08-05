import os
import sys
import logging
import structlog

# Create logs directory if not exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

TRACE_FILE_PATH = os.path.join(LOG_DIR, "agent_execution.json")

# Configure Structlog for JSON & Console Output
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=open(TRACE_FILE_PATH, "a", encoding="utf-8")
    ),
    cache_logger_on_first_use=True,
)

audit_logger = structlog.get_logger()

def log_agent_step(node_name: str, incident_id: str, latency_ms: float, payload: dict):
    """Log structured execution traces for observability."""
    audit_logger.info(
        "graph_node_execution",
        node_name=node_name,
        incident_id=incident_id,
        latency_ms=round(latency_ms, 2),
        payload_summary=payload
    )

if __name__ == "__main__":
    print("Testing Structured Logger...")
    log_agent_step("test_node", "INC-999", 120.45, {"status": "success"})
    print(f"✅ Execution trace recorded at: {TRACE_FILE_PATH}")