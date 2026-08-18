import os
import sqlite3
from datetime import datetime, timedelta

# Directory Setup
DATA_DIR = os.path.join(os.path.dirname(__file__), "simulated")
os.makedirs(DATA_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(DATA_DIR, "app_service.log")
DB_FILE_PATH = os.path.join(DATA_DIR, "system_telemetry.db")

def create_database_schema():
    """Create a robust metrics table for multi-scenario infrastructure tracking."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS metrics")
    cursor.execute("""
        CREATE TABLE metrics (
            timestamp TEXT PRIMARY KEY,
            service_name TEXT,
            cpu_usage_pct REAL,
            memory_usage_pct REAL,
            db_active_connections INTEGER,
            db_max_connections INTEGER,
            http_5xx_rate_pct REAL,
            avg_response_time_ms REAL
        )
    """)
    conn.commit()
    conn.close()

def generate_scenario_a():
    """Scenario A: DB Pool Exhaustion"""
    logs = [
        "2026-08-03 10:00:01 [INFO] order-service: Processing checkout request user_id=8923",
        "2026-08-03 10:01:15 [WARN] order-service: DB pool connection wait time > 500ms",
        "2026-08-03 10:02:10 [ERROR] order-service: sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflowed, connection timed out",
        "2026-08-03 10:02:12 [ERROR] order-service: HTTP 500 returned to endpoint /api/v1/checkout",
        "2026-08-03 10:03:00 [CRITICAL] order-service: Active worker threads stalled waiting for DB pool release."
    ]
    metrics = [
        ("2026-08-03 10:00:00", "order-service", 32.0, 45.0, 2, 10, 0.0, 120.0),
        ("2026-08-03 10:01:00", "order-service", 35.5, 46.0, 6, 10, 1.2, 450.0),
        ("2026-08-03 10:02:00", "order-service", 41.0, 47.5, 10, 10, 42.5, 5200.0),
        ("2026-08-03 10:03:00", "order-service", 39.0, 48.0, 10, 10, 88.0, 8500.0)
    ]
    return logs, metrics

def generate_scenario_b():
    """Scenario B: Unbounded Memory Leak & Heap OOM"""
    logs = [
        "2026-08-03 11:00:00 [INFO] analytics-service: Starting periodic payload caching batch",
        "2026-08-03 11:01:30 [WARN] analytics-service: Garbage Collection pause exceeded 1200ms",
        "2026-08-03 11:02:45 [ERROR] analytics-service: java.lang.OutOfMemoryError: Java heap space",
        "2026-08-03 11:03:00 [CRITICAL] analytics-service: Process killed by OOM-killer kernel event signal 9"
    ]
    metrics = [
        ("2026-08-03 11:00:00", "analytics-service", 25.0, 55.0, 3, 20, 0.0, 80.0),
        ("2026-08-03 11:01:00", "analytics-service", 68.0, 78.5, 3, 20, 0.0, 310.0),
        ("2026-08-03 11:02:00", "analytics-service", 95.2, 96.8, 4, 20, 15.0, 2400.0),
        ("2026-08-03 11:03:00", "analytics-service", 12.0, 5.0, 0, 20, 100.0, 0.0)
    ]
    return logs, metrics

def generate_scenario_c():
    """Scenario C: Upstream Third-Party API Latency Cascade"""
    logs = [
        "2026-08-03 12:00:00 [INFO] payment-service: Dispatching payment payload to external gateway api.stripe.com",
        "2026-08-03 12:01:20 [WARN] payment-service: Upstream HTTP response delayed beyond SLA threshold limit 10000ms",
        "2026-08-03 12:02:15 [ERROR] payment-service: requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='api.stripe.com', port=443): Read timed out",
        "2026-08-03 12:03:00 [CRITICAL] payment-service: All HTTP worker thread pools exhausted waiting for socket read"
    ]
    metrics = [
        ("2026-08-03 12:00:00", "payment-service", 15.0, 30.0, 1, 20, 0.0, 210.0),
        ("2026-08-03 12:01:00", "payment-service", 18.0, 31.0, 2, 20, 5.0, 4500.0),
        ("2026-08-03 12:02:00", "payment-service", 22.0, 32.0, 2, 20, 65.0, 12000.0),
        ("2026-08-03 12:03:00", "payment-service", 20.0, 32.5, 2, 20, 95.0, 15000.0)
    ]
    return logs, metrics

def generate_scenario_d():
    """Scenario D: CPU Throttling & CFS Quota Starvation"""
    logs = [
        "2026-08-03 14:00:00 [INFO] worker-service: Worker thread pool processing batch requests",
        "2026-08-03 14:01:00 [WARN] worker-service: CFS scheduler quota reached. CPU throttled on container",
        "2026-08-03 14:02:00 [ERROR] worker-service: Worker timeout: thread starvation detected during compute task",
        "2026-08-03 14:03:00 [CRITICAL] worker-service: Event loop lag exceeded threshold (8500ms). System unresponsive."
    ]
    metrics = [
        ("2026-08-03 14:00:00", "worker-service", 55.0, 42.0, 2, 20, 0.0, 150.0),
        ("2026-08-03 14:01:00", "worker-service", 85.0, 44.0, 3, 20, 5.0, 1200.0),
        ("2026-08-03 14:02:00", "worker-service", 98.5, 46.0, 4, 20, 35.0, 6500.0),
        ("2026-08-03 14:03:00", "worker-service", 99.8, 47.0, 4, 20, 75.0, 9200.0)
    ]
    return logs, metrics

def build_telemetry(scenario="A"):
    """Entry point to populate logs and DB metrics based on scenario selection."""
    create_database_schema()
    
    # Normalize scenario string
    sc_upper = str(scenario).upper()
    
    if "B" in sc_upper or "MEMORY" in sc_upper:
        logs, metrics = generate_scenario_b()
        print("🎭 Generating Scenario B: Memory Leak & Heap OOM...")
    elif "C" in sc_upper or "TIMEOUT" in sc_upper or "UPSTREAM" in sc_upper:
        logs, metrics = generate_scenario_c()
        print("🎭 Generating Scenario C: Upstream API Timeout Cascade...")
    elif "D" in sc_upper or "CPU" in sc_upper or "THROTTLING" in sc_upper:
        logs, metrics = generate_scenario_d()
        print("🎭 Generating Scenario D: CPU Throttling / Thread Starvation...")
    else:
        logs, metrics = generate_scenario_a()
        print("🎭 Generating Scenario A: DB Pool Exhaustion...")
        
    # Write Logs
    with open(LOG_FILE_PATH, "w") as f:
        f.write("\n".join(logs))
    print(f"✅ App Logs updated at: {LOG_FILE_PATH}")
    
    # Write DB Metrics
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", metrics)
    conn.commit()
    conn.close()
    print(f"✅ Database Telemetry Metrics updated at: {DB_FILE_PATH}")

if __name__ == "__main__":
    # Test generating Scenario A by default
    build_telemetry("A")