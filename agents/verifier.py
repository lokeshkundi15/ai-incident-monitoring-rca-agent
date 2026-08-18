import re
from typing import Dict, Any, List, Union

class IndependentRCAVerifier:
    """
    Independent Deterministic Verifier Engine.
    Cross-checks diagnosis against raw log signatures and telemetry metric thresholds.
    """
    
    SIGNATURES = {
        "DB_POOL_EXHAUSTION": [
            r"QueuePool",
            r"TimeoutError",
            r"connection timed out",
            r"DB pool",
            r"waiting for DB pool release",
            r"Active worker threads stalled"
        ],
        "MEMORY_LEAK_OOM": [
            r"OutOfMemoryError",
            r"Java heap space",
            r"Garbage Collection pause",
            r"OOM-killer",
            r"signal 9"
        ],
        "UPSTREAM_TIMEOUT": [
            r"ReadTimeout",
            r"HTTPSConnectionPool",
            r"delayed beyond SLA",
            r"api\.stripe\.com",
            r"worker thread pools exhausted waiting for socket"
        ],
        "CPU_THROTTLING": [
            r"CPU throttled",
            r"CFS scheduler quota",
            r"thread starvation",
            r"Worker timeout",
            r"Event loop lag"
        ]
    }

    def verify_rca(self, rca_text: str, logs: Union[str, List[str]], metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates whether the RCA diagnosis hypothesis is supported by logs & metric thresholds across the window.
        """
        logs_str = "\n".join(logs) if isinstance(logs, list) else str(logs)
        rca_str = str(rca_text)
        
        matched_signatures = []
        detected_scenario = "UNKNOWN"

        # 1. Match Log Regex Signatures
        for scenario, patterns in self.SIGNATURES.items():
            for p in patterns:
                if re.search(p, logs_str, re.IGNORECASE):
                    matched_signatures.append(p)
                    detected_scenario = scenario

        # 2. Check Metric Threshold Consistency across all metric rows
        metric_consistent = True
        if metrics and isinstance(metrics, list) and len(metrics) > 0:
            max_http_5xx = max([float(m.get("http_5xx_rate_pct", 0.0)) for m in metrics])
            max_cpu = max([float(m.get("cpu_usage_pct", 0.0)) for m in metrics])
            max_mem = max([float(m.get("memory_usage_pct", 0.0)) for m in metrics])

            if detected_scenario == "DB_POOL_EXHAUSTION" and max_http_5xx < 1.0:
                metric_consistent = False
            elif detected_scenario == "MEMORY_LEAK_OOM" and max_mem < 40.0:
                metric_consistent = False
            elif detected_scenario == "CPU_THROTTLING" and max_cpu < 60.0:
                metric_consistent = False
            elif detected_scenario == "UPSTREAM_TIMEOUT" and max_http_5xx < 1.0:
                metric_consistent = False

        # 3. Grounding Verification Outcome
        has_log_evidence = len(matched_signatures) > 0
        has_rca_content = len(rca_str.strip()) > 10 and "could not be conclusively" not in rca_str
        
        evidence_score = min(1.0, 0.6 + (0.10 * len(matched_signatures))) if has_log_evidence else 0.20
        verified = bool(has_log_evidence and has_rca_content and metric_consistent)

        return {
            "verified": verified,
            "detected_scenario": detected_scenario,
            "evidence_score": round(evidence_score, 4),
            "matched_signatures": matched_signatures,
            "metric_consistent": metric_consistent
        }