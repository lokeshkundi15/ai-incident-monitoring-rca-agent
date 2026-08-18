from typing import TypedDict, List, Dict, Any, Optional

class IncidentState(TypedDict, total=False):
    incident_id: str
    service_name: str
    raw_logs: str
    raw_metrics: str
    metrics_data: List[Dict[str, Any]]        # Structured telemetry rows for metric checks
    root_cause_analysis: str
    confidence_score: float
    grounding_passed: bool
    verification_details: Dict[str, Any]      # Independent verifier output dict
    remediation_action: str
    remediation_approved: bool
    remediation_status: str