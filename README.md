---
title: AI Incident Monitoring & RCA Agent
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.32.0
app_file: ui/dashboard.py
pinned: false
---

# 🤖 Enterprise AI System Monitoring & Autonomous RCA Agent

[![Live Demo](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Live%20Demo-blue)](https://huggingface.co/spaces/lokeshkundi15/ai-incident-monitoring-rca-agent)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/lokeshkundi15/ai-incident-monitoring-rca-agent)

> An autonomous, production-inspired Level-1 SRE Incident Triage Agent built with **LangGraph**, **FastMCP**, and **FastAPI**. It intercepts infrastructure alerts via authenticated webhooks, dynamically queries application stack traces and time-series metrics via FastMCP tools, performs grounded root-cause analysis, and provides human-in-the-loop remediation guardrails.
>
> **Illustrative Efficiency Baseline:** Automates traditional manual SRE triage steps (~30–40 minutes of manual log searching) into an automated, grounded RCA workflow executing in under **~3 seconds**.

---

## 🏗️ System Architecture & Stateful Workflow

```text
               [ External Alerting / Prometheus ]
                               │ (Authenticated HTTP POST / X-API-Key)
                               ▼
                    ┌─────────────────────┐
                    │ FastAPI Webhook API │
                    └──────────┬──────────┘
                               │ (Idempotency Check via SQLite)
                               ▼
               ┌───────────────────────────────┐
               │    LangGraph State Machine    │
               ├───────────────────────────────┤
               │ 1. Ingest Incident            │
               │ 2. Fetch Telemetry ───────────┼──► [ FastMCP Server Tools ]
               │ 3. Analyze Root Cause ────────┼──► [ Resilient LLM Router (Groq / OpenRouter) ]
               │ 4. Verify Grounding           │
               └───────────────┬───────────────┘
                               │
               ┌───────────────┴───────────────┐
               │ Conditional Branching Edge    │
               └───────┬───────────────┬───────┘
        (Passed)       │               │ (Failed / Unverified)
                       ▼               ▼
                   [ END ]   [ Conservative Fallback Node ]
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │   Streamlit Operator UI   │ ──► Human-in-the-Loop Safeguard
                         └───────────────────────────┘     (Approve / Reject Remediation)


⭐ Core Enterprise Features:

1.Multi-Incident Failure Simulation: Built-in telemetry engine generating realistic multi-variate metrics for Database Pool Exhaustion, Heap Memory Leaks (OOM), and Upstream API Latency Cascades.

2.Stateful LangGraph Orchestration with Branching: Async state-machine workflow executing sequential steps with add_conditional_edges routing ungrounded claims to a Conservative Fallback Node.

3.Decoupled FastMCP Tool Architecture: Isolated Model Context Protocol server exposing get_recent_logs() and get_system_metrics() as modular tools without polluting core agent logic.

4.Dynamic Grounding Safeguard: Programmatic verification node extracting technical claims via regex and cross-referencing them against raw stack trace evidence before marking diagnostics as verified.

5.Resilient Multi-Provider LLM Router: 15-second timeout limits with exponential backoff retries ($1.5s, 3.0s$) and automatic failover from primary (Groq Llama 3.1 8B) to secondary (OpenRouter).

6.Webhook Security & Idempotency Store: Secured with X-API-Key header authentication and SQLite-backed deduplication (DUPLICATE_CACHED) returning cached responses in $< 5\text{ms}$ to eliminate redundant LLM costs.

7.FinOps Token & Cost Observability: Real-time prompt/completion token usage, execution latency, and asymmetric USD cost tracking per incident logged via structlog and SQLite.

8.Automated Pytest Regression Suite: Mocked async test suite utilizing AsyncMock to run complete integration and regression checks in $< 500\text{ms}$ at zero API cost.

## 📊 Quantitative Evaluation Benchmark

Evaluated against `evaluation/eval_dataset.json` across deterministic incident scenarios:

| Metric | Benchmark Result | Evaluation Description |
| :--- | :--- | :--- |
| **Total Test Scenarios** | **3 / 3 Passed** | Scenarios A (DB Pool), B (OOM), C (Upstream Timeout) |
| **Grounding Pass Rate** | **100.0%** | Extracted technical terms matched against raw log evidence |
| **Mean AI Execution Latency** | **~2.8 seconds** | Total pipeline execution time including LLM inference |
| **Deduplication Speed** | **< 5 ms** | Instant cached RCA return on duplicate incident IDs |
| **Triage Baseline Efficiency** | **Automated (~2.8s)** | Drastically reduces manual SRE APM inspection overhead (~30m baseline) |

🚀 Quickstart & Setup
    Prerequisites
        Python 3.11+
        Docker & Docker Compose
        Free Groq API Key

Local Installation

# 1. Clone Repository
git clone [https://github.com/lokeshkundi15/ai-incident-monitoring-rca-agent.git](https://github.com/lokeshkundi15/ai-incident-monitoring-rca-agent.git)
cd ai-incident-monitoring-rca-agent

# 2. Create Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Environment Variables Setup
cp .env.example .env
# Edit .env and specify your GROQ_API_KEY and WEBHOOK_API_KEY

Running the Services

# Start Authenticated FastAPI Webhook Server
python app/main_api.py

# In a new terminal, launch the Streamlit Operations Dashboard
streamlit run ui/dashboard.py

# Execute Quantitative Evaluation Benchmark Suite
python evaluation/evaluate.py

# Run Automated Integration Tests (Zero API Cost)
pytest -v

Running via Docker & Docker Compose

# Build and run dual-process container (FastAPI Port 8000 & Streamlit Port 8501/7860)
docker-compose up --build

🛠️ Project Structure

ai-incident-monitoring-rca-agent/
├── app/
│   ├── logger.py          # Structlog JSON Audit Logger
│   ├── llm_router.py      # Resilient Fallback LLM Router
│   ├── main_api.py        # Authenticated FastAPI Webhook
│   ├── idempotency.py     # SQLite Deduplication Store
│   └── cost_tracker.py    # FinOps Token & Cost Observability
├── agents/
│   ├── state.py           # IncidentState Schema (TypedDict)
│   ├── nodes.py           # Async Graph Nodes & Fallback Handler
│   └── graph.py           # LangGraph Workflow Orchestrator (Conditional Edges)
├── mcp_server/
│   └── tools.py           # FastMCP Telemetry Tools
├── data/
│   ├── generator.py       # Multi-Scenario Incident Simulator
│   └── simulated/         # SQLite Metrics & Log Files
├── evaluation/
│   ├── eval_dataset.json  # Benchmark Scenarios
│   └── evaluate.py        # Quantitative Evaluation Runner
├── tests/
│   └── test_suite.py      # Pytest Async Mocked Regression Suite
├── ui/
│   └── dashboard.py       # Streamlit Operator HITL UI
├── Dockerfile             # Multi-stage Docker Container Definition
├── entrypoint.sh          # Dual Process Execution Script
├── docker-compose.yml     # Orchestration File
└── requirements.txt       # Production Dependencies


Evaluation Methodology:

### 🔬 How Evaluation Works (Evaluation Methodology)

1. **Deterministic Scenario Simulation (`data/generator.py`):**
   - The test suite executes against standard telemetry scenarios representing real-world infrastructure failures:
     - **Scenario A:** Database Connection Pool Exhaustion (`QueuePool` limit reached).
     - **Scenario B:** Heap Out Of Memory (`java.lang.OutOfMemoryError`).
     - **Scenario C:** Upstream API Timeout (`ReadTimeout` on payment gateway).

2. **Automated Benchmark Execution (`evaluation/evaluate.py`):**
   - Runs each scenario asynchronously through the full LangGraph pipeline.
   - Measures exact execution time (in milliseconds) from webhook ingestion to final state.

3. **Dynamic Claim Grounding Verification (`verify_grounding_node`):**
   - Extracts key technical terms (>4 chars) from the LLM's diagnostic report using Regex.
   - Cross-references these terms against raw log stack traces.
   - If the term match ratio exceeds the safety threshold ($>= 20\%$), grounding passes (`100% Pass Rate`).

4. **Zero-Cost Cache Benchmarking (`app/idempotency.py`):**
   - Sends duplicate alert payloads to test the Idempotency Store.
   - Verifies that duplicate incident IDs immediately return cached RCA in $< 5\text{ms}$ without consuming LLM tokens.

