import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data", "simulated")
os.makedirs(DB_DIR, exist_ok=True)
COST_DB_PATH = os.path.join(DB_DIR, "llm_cost_tracker.db")

# Configurable Model Pricing per 1M Tokens (USD)
MODEL_PRICING = {
    "llama-3.1-8b-instant": {"input_per_1m": 0.05, "output_per_1m": 0.08},
    "meta-llama/llama-3.1-8b-instruct:free": {"input_per_1m": 0.00, "output_per_1m": 0.00},
    "default": {"input_per_1m": 0.05, "output_per_1m": 0.08}
}

def init_cost_db():
    """Initialize SQLite table for LLM token and cost tracking."""
    conn = sqlite3.connect(COST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            provider TEXT,
            model_name TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms REAL,
            estimated_cost_usd REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_llm_cost(
    incident_id: str,
    provider: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float
):
    """Calculates estimated cost and stores usage audit logs."""
    init_cost_db()
    
    pricing = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total_cost = round(input_cost + output_cost, 6)
    total_tokens = input_tokens + output_tokens
    
    conn = sqlite3.connect(COST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO token_usage_logs 
        (incident_id, provider, model_name, input_tokens, output_tokens, total_tokens, latency_ms, estimated_cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (incident_id, provider, model_name, input_tokens, output_tokens, total_tokens, latency_ms, total_cost))
    conn.commit()
    conn.close()
    
    print(f"💰 [FinOps Log] {provider} ({model_name}) | Tokens: {total_tokens} (In:{input_tokens}, Out:{output_tokens}) | Latency: {round(latency_ms, 2)}ms | Cost: ${total_cost}")

def get_cost_summary():
    """Returns aggregated usage metrics."""
    if not os.path.exists(COST_DB_PATH):
        return "No cost logs available yet."
        
    conn = sqlite3.connect(COST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_tokens), SUM(estimated_cost_usd), COUNT(*) FROM token_usage_logs")
    tokens, cost, calls = cursor.fetchone()
    conn.close()
    
    return f"Total LLM Calls: {calls} | Total Tokens Used: {tokens or 0} | Estimated Spend: ${round(cost or 0.0, 6)}"

if __name__ == "__main__":
    print("Testing Cost Tracker Module...")
    log_llm_cost("INC-999", "Groq", "llama-3.1-8b-instant", 1200, 450, 620.5)
    print(get_cost_summary())