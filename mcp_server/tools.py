import os
import sqlite3
import asyncio
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Production-Telemetry-MCP-Server")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE_PATH = os.path.join(BASE_DIR, "data", "simulated", "app_service.log")
DB_FILE_PATH = os.path.join(BASE_DIR, "data", "simulated", "system_telemetry.db")

@mcp.tool()
async def get_recent_logs(limit: int = 20) -> str:
    """Fetch the most recent application log lines asynchronously."""
    if not os.path.exists(LOG_FILE_PATH):
        return "ERROR: Log telemetry source file missing."
    
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    recent_lines = lines[-limit:] if len(lines) >= limit else lines
    return "".join(recent_lines) if recent_lines else "NO_LOGS_AVAILABLE"

@mcp.tool()
async def get_system_metrics() -> str:
    """Query multi-variate infrastructure time-series metrics from SQLite database."""
    if not os.path.exists(DB_FILE_PATH):
        return "ERROR: Telemetry metrics database file missing."
    
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, service_name, cpu_usage_pct, memory_usage_pct, 
               db_active_connections, db_max_connections, http_5xx_rate_pct, avg_response_time_ms 
        FROM metrics ORDER BY timestamp ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "NO_METRICS_FOUND"
        
    output = "Timestamp | Service | CPU% | RAM% | DB_Conn | Max_DB | HTTP_5xx% | Response_ms\n"
    output += "-" * 85 + "\n"
    for r in rows:
        output += f"{r[0]} | {r[1]} | {r[2]}% | {r[3]}% | {r[4]} | {r[5]} | {r[6]}% | {r[7]}ms\n"
        
    return output

async def test_mcp_server():
    print("Testing Async FastMCP Tools Local Execution...")
    logs = await get_recent_logs()
    metrics = await get_system_metrics()
    
    print("\n--- [MCP TOOL OUTPUT: LOGS] ---")
    print(logs)
    print("\n--- [MCP TOOL OUTPUT: METRICS] ---")
    print(metrics)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())