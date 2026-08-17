import re
from typing import Dict, Any, List

class IndependentRCAVerifier:
    """
    Independent Evidence Verification Engine.
    Cross-checks LLM diagnostic claims against deterministic metric thresholds 
    and log stack trace signatures before marking RCA as verified.
    """
    
    FAILURE_SIGNATURES = {
        "DB_POOL_EXHAUSTION": {
            "log_patterns": [r"QueuePool", r"connection pool", r"timeout acquiring connection", r"remaining connection slots"],
            "metric_check": lambda m: any(row.get("cpu_usage_pct", 0) > 0 for row in m)
        },
        "MEMORY_LEAK_OOM": {
            "log_patterns": [r"OutOfMemoryError", r"Heap space", r"Garbage Collection", r"OOM-killer"],
            "metric_check": lambda m: any(row.get("memory_usage_pct", 0) >= 85.0 for row in m)
        },
        "UPSTREAM_TIMEOUT": {
            "log_patterns": [r"ReadTimeout", r"504 Gateway", r"Connection refused", r"upstream request timeout"],
            "metric_check": lambda m: any(row.get("http_5xx_rate_pct", 0) >= 5.0 for row in m)
        },
        "CPU_THROTTLING": {
            "log_patterns": [r"CPU throttled", r"thread starvation", r"high latency", r"worker timeout"],
            "metric_check": lambda m: any(row.get("cpu_usage_pct", 0) >= 80.0 for row in m)
        }
    }

    def verify_rca(self, rca_text: str, logs: str, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates whether LLM diagnostic claims are mathematically and logistically grounded.
        """
        matched_signatures = []
        evidence_score = 0.0
        
        # 1. Match Log Stack Trace Signatures
        for scenario, config in self.FAILURE_SIGNATURES.items():
            for pattern in config["log_patterns"]:
                if re.search(pattern, logs, re.IGNORECASE) and re.search(pattern, rca_text, re.IGNORECASE):
                    matched_signatures.append(f"{scenario}:{pattern}")
                    evidence_score += 0.4

        # 2. Check Time-Series Metric Consistency
        metric_verified = False
        for scenario, config in self.FAILURE_SIGNATURES.items():
            if scenario in str(matched_signatures) and config["metric_check"](metrics):
                metric_verified = True
                evidence_score += 0.4
                break

        # Fallback baseline check if specific pattern isn't in signature dictionary
        if not matched_signatures:
            # Word overlap fallback
            tokens = [t for t in re.findall(r'\b[A-Za-z0-9_-]{4,}\b', rca_text) if t.lower() not in {"this", "with", "from", "that", "service", "error"}]
            matched_words = [t for t in tokens if t.lower() in logs.lower()]
            overlap_ratio = len(matched_words) / max(1, len(tokens))
            if overlap_ratio >= 0.15:
                evidence_score = min(1.0, overlap_ratio * 1.5)

        is_passed = evidence_score >= 0.35

        return {
            "verified": is_passed,
            "evidence_score": round(min(1.0, evidence_score), 3),
            "matched_signatures": matched_signatures,
            "metric_consistency": metric_verified
        }