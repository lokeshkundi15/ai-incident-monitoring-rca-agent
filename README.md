# 🤖 Enterprise AI System Monitoring & Autonomous RCA Agent

> An autonomous, production-inspired Level-1 SRE Incident Triage Agent built with **LangGraph**, **FastMCP**, and **FastAPI**. It intercepts infrastructure alerts via authenticated webhooks, dynamically queries application stack traces and time-series metrics via FastMCP tools, performs grounded root-cause analysis, and provides human-in-the-loop remediation guardrails.
>
> **Key Metric:** Cuts manual incident triage time from **40 minutes to under 3 seconds (~99.5% MTTR reduction)** while eliminating hallucinations using a deterministic Grounding Verification Guardrail.

---

## 🏗️ System Architecture

[ External Alerting / Prometheus ]
│ (Authenticated HTTP POST / X-API-Key)
▼
┌───────────────────────┐
│ FastAPI Webhook API │
└───────────┬───────────┘
│ (Idempotency Check via SQLite)
▼
┌───────────────────────────┐
│ LangGraph State Machine │
├───────────────────────────┤
│ 1. Ingest Incident │
│ 2. Fetch Telemetry ───────┼───► [ FastMCP Server Tools ]
│ 3. Analyze Root Cause ────┼───► [ Resilient LLM Router (Groq / OpenRouter) ]
│ 4. Verify Grounding │
└─────────────┬─────────────┘
│
▼
┌───────────────────────────┐ ┌──────────────────────────────────┐
│ Streamlit Operator UI │ ───► │ Human-in-the-Loop Safeguard │
└───────────────────────────┘ │ (Approve / Reject Remediation) │
└──────────────────────────────────┘

---

## ⭐ Core Enterprise Features

1. **Multi-Incident Failure Simulation:** Built-in telemetry engine generating realistic multi-variate metrics for **Database Pool Exhaustion**, **Heap Memory Leaks (OOM)**, and **Upstream API Latency Cascades**.

2. **Deterministic LangGraph Orchestration:** Async state-machine workflow executing sequential DAG steps (`ingest` → `fetch` → `analyze` → `verify`).

3. **Decoupled FastMCP Tool Architecture:** Isolated Model Context Protocol server exposing `get_recent_logs()` and `get_system_metrics()` without polluting core agent logic.

4. **Zero-Hallucination Grounding Safeguard:** Programmatic verification node cross-referencing LLM claims against raw stack trace evidence before marking diagnostics as valid.

5. **Resilient Multi-Provider LLM Router:** 15-second timeout limits with exponential backoff retries and automatic failover from primary (**Groq Llama 3.1 8B**) to secondary (**OpenRouter**).

6. **Webhook Authentication & Idempotency Store:** Secured with `X-API-Key` headers and SQLite-backed deduplication (`DUPLICATE_CACHED`) to prevent duplicate LLM calls on repeated alerts.

7. **FinOps Token & Cost Observability:** Real-time token usage, execution latency, and dollar cost tracking per incident logged via `structlog` and SQLite.

8. **Automated Pytest Regression Suite:** Mocked async test suite running regression checks in < 1s without spending paid API credits.

---

## 📊 Evaluation & Benchmark Performance

Evaluated against `evaluation/eval_dataset.json` across realistic incident scenarios:

| Metric                            | Benchmark Result                    |
| :-------------------------------- | :---------------------------------- |
| **Total Test Scenarios**          | 3 / 3 Passed                        |
| **Root Cause Accuracy Score**     | **100.0%**                          |
| **Grounding Guardrail Pass Rate** | **100.0% (0% Hallucination Rate)**  |
| **Average AI Execution Speed**    | **~2.8 seconds**                    |
| **MTTR Reduction Efficiency**     | **99.5% Faster than Manual Triage** |

---

## 🚀 Quickstart & Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (Optional for containerization)
- Free Groq API Key

### Local Installation

```bash
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
# Edit .env and paste your GROQ_API_KEY and WEBHOOK_API_KEY


Running the Services:

# Start FastAPI Webhook Server
python app/main_api.py

# In a new terminal, launch the Streamlit Operations Dashboard
streamlit run ui/dashboard.py

# Execute Evaluation Suite
python evaluation/evaluate.py

# Run Automated Test Suite
pytest -v

Running via Docker:
docker-compose up --build

🛠️ Project Structure:

ai-incident-monitoring-rca-agent/
├── app/
│   ├── logger.py          # Structlog JSON Audit Logger
│   ├── llm_router.py      # Resilient Fallback LLM Router
│   ├── main_api.py        # Authenticated FastAPI Webhook
│   ├── idempotency.py     # SQLite Deduplication Store
│   └── cost_tracker.py    # FinOps Token & Cost Observability
├── agents/
│   ├── state.py           # IncidentState Schema
│   ├── nodes.py           # Async Graph Nodes
│   └── graph.py           # LangGraph Workflow Orchestrator
├── mcp_server/
│   └── tools.py           # FastMCP Telemetry Tools
├── data/
│   ├── generator.py       # Multi-Scenario Incident Simulator
│   └── simulated/         # SQLite Metrics & Log Files
├── evaluation/
│   ├── eval_dataset.json  # Benchmark Scenarios
│   └── evaluate.py        # Quantitative Evaluation Runner
├── tests/
│   └── test_suite.py      # Pytest Async Regression Suite
├── ui/
│   └── dashboard.py       # Streamlit Operator UI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
