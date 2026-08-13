from typing import TypedDict, List, Dict, Optional

class IncidentState(TypedDict):
    """
    Central State schema for the RCA Agent pipeline.
    """
    incident_id: str
    service_name: str
    raw_logs: str
    raw_metrics: str
    root_cause_analysis: str
    confidence_score: float
    recommended_action: str
    grounding_passed: bool        # NEW: Grounding Guardrail Flag
    human_approved: Optional[bool]
    retry_count: int