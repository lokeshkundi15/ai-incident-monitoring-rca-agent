import sys
import os
import json
import time
import asyncio

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import build_telemetry
from agents.graph import run_pipeline_async

async def run_evaluation_suite():
    print("="*65)
    print("🧪 RUNNING PRODUCTION RCA AGENT EVALUATION SUITE")
    print("="*65)
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EVAL_SET_PATH = os.path.join(BASE_DIR, "evaluation", "eval_dataset.json")
    
    if not os.path.exists(EVAL_SET_PATH):
        print("❌ Error: eval_dataset.json benchmark file missing.")
        return
        
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)
        
    total_incidents = len(benchmarks)
    correct_root_causes = 0
    grounding_passes = 0
    total_ai_time = 0.0
    total_manual_time = 0.0
    
    for item in benchmarks:
        print(f"\n[Test Case]: {item['incident_id']} - {item['scenario_name']}")
        
        # 1. Regenerate telemetry matching target test scenario
        build_telemetry(item['scenario_code'])
        
        # 2. Execute Async LangGraph RCA Agent
        start_time = time.time()
        output = await run_pipeline_async(
            incident_id=item["incident_id"],
            service_name=item["target_service"]
        )
        elapsed_time = round(time.time() - start_time, 2)
        
        analysis_text = output.get("root_cause_analysis", "")
        grounding_ok = output.get("grounding_passed", False)
        
        # 3. Keyword Grounding Evidence Match Analysis
        matched_keywords = [
            kw for kw in item["expected_evidence_keywords"] 
            if kw.lower() in analysis_text.lower()
        ]
        evidence_score = (len(matched_keywords) / len(item["expected_evidence_keywords"])) * 100
        
        print(f"⏱️ Execution Latency      : {elapsed_time}s (Manual Target: {item['simulated_manual_time_sec']}s)")
        print(f"🔍 Evidence Match Score    : {round(evidence_score, 1)}% ({len(matched_keywords)}/{len(item['expected_evidence_keywords'])} keywords matched)")
        print(f"🛡️ Grounding Safeguard     : {'PASSED ✅' if grounding_ok else 'FAILED ⚠️'}")
        
        is_accurate = grounding_ok and (evidence_score >= 50.0)
        if is_accurate:
            correct_root_causes += 1
            print("Verdict: ✅ ACCURATE & GROUNDED DIAGNOSIS")
        else:
            print("Verdict: ⚠️ POOR DIAGNOSIS OR UNGROUNDED EVIDENCE")
            
        if grounding_ok:
            grounding_passes += 1
            
        total_ai_time += elapsed_time
        total_manual_time += item["simulated_manual_time_sec"]

    # 4. Final Aggregated Scorecard
    rca_accuracy = round((correct_root_causes / total_incidents) * 100, 2)
    grounding_rate = round((grounding_passes / total_incidents) * 100, 2)
    time_saved_pct = round(((total_manual_time - total_ai_time) / total_manual_time) * 100, 2)
    
    print("\n" + "="*65)
    print("📊 EVALUATION BENCHMARK METRICS SCORECARD")
    print("="*65)
    print(f"Total Incident Test Scenarios : {total_incidents}")
    print(f"Correct Root Cause Diagnoses   : {correct_root_causes}")
    print(f"Root Cause Accuracy Score      : {rca_accuracy}%")
    print(f"Grounding Guardrail Pass Rate  : {grounding_rate}%")
    print(f"Total AI Execution Time        : {round(total_ai_time, 2)} seconds")
    print(f"Total Manual Triage Time       : {total_manual_time} seconds")
    print(f"⚡ MTTR Reduction Efficiency   : {time_saved_pct}% Faster")
    print("="*65)

if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())