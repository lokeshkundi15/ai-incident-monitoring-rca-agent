from typing import List, Dict, Any

class EvaluationMetricsCalculator:
    """Computes RCA Accuracy, Category Matching, and Expected Calibration Error (ECE)."""

    @staticmethod
    def evaluate_rca_accuracy(predicted_rca: str, ground_truth_category: str) -> bool:
        """Strict evaluation: Asserts that key diagnostic terms exist in the prediction."""
        category_keywords = {
            "DB_POOL_EXHAUSTION": ["connection pool", "hikaricp", "pool exhaustion", "active connections", "connection timeout"],
            "CPU_THROTTLING": ["cpu throttling", "cpu limit", "cfs quota", "high cpu", "throttled"],
            "MEMORY_LEAK": ["out of memory", "oom", "heap", "memory leak", "gc overhead"],
            "CASCADING_TIMEOUT": ["downstream timeout", "payment-service", "circuit breaker", "deadline exceeded", "cascading"]
        }
        
        keywords = category_keywords.get(ground_truth_category, [])
        pred_lower = predicted_rca.lower()
        return any(kw in pred_lower for kw in keywords)

    @staticmethod
    def compute_calibration_error(predictions: List[Dict[str, Any]], bins: int = 5) -> float:
        """
        Calculates Expected Calibration Error (ECE) comparing 
        predicted confidence vs true accuracy across confidence bins.
        """
        if not predictions:
            return 0.0

        total_samples = len(predictions)
        ece = 0.0

        for i in range(bins):
            bin_lower = i / bins
            bin_upper = (i + 1) / bins
            
            bin_items = [
                p for p in predictions 
                if bin_lower <= p.get("confidence", 0.0) < bin_upper or (i == bins - 1 and p.get("confidence", 0.0) == 1.0)
            ]
            
            if not bin_items:
                continue

            bin_accuracy = sum(1 for p in bin_items if p.get("is_correct", False)) / len(bin_items)
            bin_confidence = sum(p.get("confidence", 0.0) for p in bin_items) / len(bin_items)
            
            weight = len(bin_items) / total_samples
            ece += weight * abs(bin_accuracy - bin_confidence)

        return round(ece, 4)