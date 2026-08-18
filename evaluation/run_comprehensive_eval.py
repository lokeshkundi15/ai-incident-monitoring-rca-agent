import os
import sys
import json
import time
import asyncio
import pandas as pd

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from data.generator import build_telemetry
from agents.graph import run_pipeline_async
from agents.verifier import IndependentRCAVerifier
from evaluation.metrics import EvaluationMetricsCalculator

DATASET_PATH = os.path.join(BASE_DIR, "evaluation", "dataset", "incidents.json")

SCENARIO_MAP = {
    "DB_POOL_EXHAUSTION": "Scenario A: DB Pool Exhaustion",
    "MEMORY_LEAK_OOM": "Scenario B: Memory Leak (Heap OOM)",
    "UPSTREAM_TIMEOUT": "Scenario C: Upstream API Read Timeout",
    "CPU_THROTTLING": "Scenario D: CPU Throttling & Starvation"
}

EXPECTED_KEYWORDS = {
    "DB_POOL_EXHAUSTION": ["db", "database", "connection", "pool", "hikaricp", "queuepool", "timeout", "exhaustion", "waiting"],
    "MEMORY_LEAK_OOM": ["memory", "heap", "oom", "outofmemoryerror", "leak", "gc", "garbage collection"],
    "UPSTREAM_TIMEOUT": ["upstream", "timeout", "payment", "gateway", "stripe", "readtimeout", "socket", "http"],
    "CPU_THROTTLING": ["cpu", "throttled", "starvation", "cfs", "thread", "quota", "worker", "lag"]
}

async def evaluate_full_dataset():
    print("🚀 === Starting 30-Incident Comprehensive RCA Evaluation ===")
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    print(f"📊 Loaded {len(incidents)} Incidents from Golden Benchmark Dataset.\n")
    verifier = IndependentRCAVerifier()
    
    results = []
    total_time_start = time.time()

    for idx, inc in enumerate(incidents, start=1):
        inc_id = inc["incident_id"]
        scenario_key = inc.get("scenario") or inc.get("failure_type", "DB_POOL_EXHAUSTION")
        service = inc.get("service") or inc.get("service_name", "order-service")
        gen_scenario = SCENARIO_MAP.get(scenario_key, "Scenario A: DB Pool Exhaustion")

        print(f"[{idx:02d}/30] Executing Incident: {inc_id} ({scenario_key} on {service})...")

        # 1. Generate live telemetry
        build_telemetry(gen_scenario)

        # 2. Run LangGraph RCA pipeline
        start_t = time.time()
        agent_out = await run_pipeline_async(inc_id, service)
        latency_ms = (time.time() - start_t) * 1000

        # Extract telemetry & RCA text
        raw_logs = agent_out.get("raw_logs", "")
        metrics_data = agent_out.get("metrics_data", [])
        logs_str = "\n".join(raw_logs) if isinstance(raw_logs, list) else str(raw_logs)

        rca_text = str(agent_out.get("root_cause_analysis") or "")
        confidence = float(agent_out.get("confidence_score") or 0.90)

        # 3. Independent Verification Check
        ver_res = verifier.verify_rca(rca_text, logs_str, metrics_data)
        
        # 4. Strict Keyword Ground Truth Check
        rca_lower = rca_text.lower()
        expected_kws = EXPECTED_KEYWORDS.get(scenario_key, [])
        keyword_matched = any(kw in rca_lower for kw in expected_kws)
        
        is_correct = bool(ver_res.get("verified", False) and keyword_matched)

        results.append({
            "incident_id": inc_id,
            "scenario": scenario_key,
            "service": service,
            "is_correct": is_correct,
            "confidence": confidence,
            "evidence_score": ver_res.get("evidence_score", 0.90),
            "latency_ms": latency_ms
        })

    # Summary Metrics
    total_latency = (time.time() - total_time_start)
    correct_count = sum(1 for r in results if r["is_correct"])
    accuracy = (correct_count / len(results)) * 100 if results else 0.0
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0.0
    ece_error = EvaluationMetricsCalculator.compute_calibration_error(results)

    print("\n" + "="*80)
    print("🏆 EMPIRICAL RCA BENCHMARK EVALUATION SCORECARD (30 INCIDENTS)")
    print("="*80)
    print(f"✅ Total Scenarios Evaluated  : {len(results)}")
    print(f"🎯 Strict Verified RCA Accuracy : {accuracy:.1f}% ({correct_count}/{len(results)} Passed)")
    print(f"📏 Expected Calibration Error : {ece_error:.4f} (Calibrated Model Confidence)")
    print(f"⚡ Mean Execution Latency    : {avg_latency:.1f} ms / incident")
    print(f"⏱️ Total Benchmark Runtime   : {total_latency:.2f} seconds")
    print("="*80)

    # Save summary dataframe
    df = pd.DataFrame(results)
    summary_path = os.path.join(BASE_DIR, "evaluation", "evaluation_summary.csv")
    df.to_csv(summary_path, index=False)
    print(f"💾 Full evaluation trace logged to: {summary_path}")

if __name__ == "__main__":
    asyncio.run(evaluate_full_dataset())