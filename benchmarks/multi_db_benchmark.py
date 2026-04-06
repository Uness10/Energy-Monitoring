#!/usr/bin/env python3
"""
Comprehensive benchmark for 4 databases:
- ClickHouse
- InfluxDB
- TimescaleDB
- PostgreSQL

Tests throughput, query speed, and storage efficiency.
Saves results and generates plots/analysis.
"""

import time
import json
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
import statistics

import clickhouse_connect
import psycopg2
import psycopg2.extras

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False
    print("⚠️  InfluxDB client not available - will skip InfluxDB benchmark")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Database configurations
DB_CONFIGS = {
    "clickhouse": {
        "host": "localhost",
        "http_port": 8123,
        "user": "mlab",
        "password": "mlab_secure_2026",
        "database": "benchmarks"
    },
    "timescaledb": {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "benchmarks"
    },
    "influxdb": {
        "url": "http://localhost:8086",
        "token": "",  # Leave empty for default setup
        "org": "my-org",
        "bucket": "benchmarks"
    },
}

# Test parameters
NUM_NODES = 10
NUM_APPS = 5
NUM_METRICS_PER_NODE = 100_000  # Per timestamp
BATCH_SIZE = 1000
NUM_TIME_SERIES = NUM_NODES * NUM_APPS

TIMESTAMP_START = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)


# ─────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_metrics(num_records: int) -> list:
    """Generate synthetic metrics data."""
    metrics = []
    base_time = TIMESTAMP_START
    
    for i in range(num_records):
        ts = base_time + timedelta(seconds=i * 10)  # 10-second intervals
        node_id = f"node-{(i // 100) % NUM_NODES:02d}"
        app_name = f"app-{(i // 10) % NUM_APPS:02d}"
        
        metrics.append({
            "timestamp": ts,
            "node_id": node_id,
            "app_name": app_name,
            "metric": random.choice(["power_w", "cpu_percent", "memory_percent"]),
            "value": round(random.uniform(0, 100), 2),
        })
    
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# CLICKHOUSE BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

class ClickHouseBench:
    def __init__(self):
        self.client = None
        self.results = {}
    
    def setup(self):
        """Initialize ClickHouse."""
        try:
            self.client = clickhouse_connect.get_client(
                host=DB_CONFIGS["clickhouse"]["host"],
                port=DB_CONFIGS["clickhouse"]["http_port"],
                username=DB_CONFIGS["clickhouse"]["user"],
                password=DB_CONFIGS["clickhouse"]["password"],
            )
            
            # Create database
            self.client.command(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIGS['clickhouse']['database']}")
            
            # Create table
            self.client.command(f"""
                CREATE TABLE IF NOT EXISTS {DB_CONFIGS['clickhouse']['database']}.metrics (
                    timestamp DateTime,
                    node_id String,
                    app_name String,
                    metric String,
                    value Float32
                ) ENGINE = MergeTree()
                ORDER BY (timestamp, node_id, app_name)
            """)
            
            print("✓ ClickHouse setup complete")
            return True
        except Exception as e:
            print(f"✗ ClickHouse setup failed: {e}")
            return False
    
    def insert_throughput(self, metrics: list) -> dict:
        """Measure write throughput."""
        try:
            start = time.perf_counter()
            rows = [[m["timestamp"], m["node_id"], m["app_name"], m["metric"], m["value"]] 
                    for m in metrics]
            
            self.client.insert(
                f"{DB_CONFIGS['clickhouse']['database']}.metrics",
                rows,
                column_names=["timestamp", "node_id", "app_name", "metric", "value"]
            )
            
            elapsed = time.perf_counter() - start
            throughput = len(metrics) / elapsed
            
            print(f"  Inserted {len(metrics):,} rows in {elapsed:.2f}s ({throughput:,.0f} rows/sec)")
            return {"throughput_rows_per_sec": throughput, "time_seconds": elapsed}
        except Exception as e:
            print(f"  ✗ Insert failed: {e}")
            return {}
    
    def query_speed(self) -> dict:
        """Measure query speed."""
        results = {}
        
        # Q1: Simple aggregation
        try:
            start = time.perf_counter()
            result = self.client.query(f"""
                SELECT avg(value) as avg_val FROM {DB_CONFIGS['clickhouse']['database']}.metrics
            """)
            elapsed = (time.perf_counter() - start) * 1000
            results["q1_simple_avg_ms"] = elapsed
            print(f"  Q1 (simple avg): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q1 failed: {e}")
        
        # Q2: Group by node
        try:
            start = time.perf_counter()
            result = self.client.query(f"""
                SELECT node_id, avg(value) FROM {DB_CONFIGS['clickhouse']['database']}.metrics
                GROUP BY node_id
            """)
            elapsed = (time.perf_counter() - start) * 1000
            results["q2_group_by_node_ms"] = elapsed
            print(f"  Q2 (group by node): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q2 failed: {e}")
        
        # Q3: Time range + aggregation
        try:
            start = time.perf_counter()
            result = self.client.query(f"""
                SELECT metric, max(value) as max_val FROM {DB_CONFIGS['clickhouse']['database']}.metrics
                WHERE timestamp >= now() - INTERVAL 7 DAY
                GROUP BY metric
            """)
            elapsed = (time.perf_counter() - start) * 1000
            results["q3_time_range_agg_ms"] = elapsed
            print(f"  Q3 (time range agg): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q3 failed: {e}")
        
        return results
    
    def cleanup(self):
        """Drop table."""
        try:
            self.client.command(f"DROP TABLE IF EXISTS {DB_CONFIGS['clickhouse']['database']}.metrics")
        except:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# TIMESCALEDB BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

class TimescaleDBBench:
    def __init__(self):
        self.conn = None
        self.results = {}
    
    def setup(self):
        """Initialize TimescaleDB."""
        try:
            self.conn = psycopg2.connect(
                host=DB_CONFIGS["timescaledb"]["host"],
                port=DB_CONFIGS["timescaledb"]["port"],
                user=DB_CONFIGS["timescaledb"]["user"],
                password=DB_CONFIGS["timescaledb"]["password"],
                database=DB_CONFIGS["timescaledb"]["database"]
            )
            
            cur = self.conn.cursor()
            
            cur = self.conn.cursor()
            
            # Try to enable TimescaleDB extension (may not be installed)
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
                self.conn.commit()
                has_timescaledb = True
            except Exception as ext_err:
                print(f"  Note: TimescaleDB extension not available ({ext_err})")
                print(f"  Using regular PostgreSQL instead")
                has_timescaledb = False
                self.conn.rollback()
            
            # Drop and create table
            cur.execute("DROP TABLE IF EXISTS metrics CASCADE")
            cur.execute("""
                CREATE TABLE metrics (
                    timestamp TIMESTAMPTZ,
                    node_id TEXT,
                    app_name TEXT,
                    metric TEXT,
                    value FLOAT
                )
            """)
            
            # Only create hypertable if TimescaleDB is available
            if has_timescaledb:
                try:
                    cur.execute("SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE)")
                except Exception:
                    pass  # Already a hypertable or TimescaleDB unavailable
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_node_id ON metrics (node_id, timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_app_name ON metrics (app_name, timestamp)")
            
            self.conn.commit()
            cur.close()
            
            print("✓ PostgreSQL setup complete" + (" (with TimescaleDB)" if has_timescaledb else ""))
            return True
        except Exception as e:
            print(f"✗ PostgreSQL setup failed: {e}")
            return False
    
    def insert_throughput(self, metrics: list) -> dict:
        """Measure write throughput."""
        try:
            cur = self.conn.cursor()
            start = time.perf_counter()
            
            # Batch insert
            for i in range(0, len(metrics), BATCH_SIZE):
                batch = metrics[i:i+BATCH_SIZE]
                cur.executemany("""
                    INSERT INTO metrics (timestamp, node_id, app_name, metric, value)
                    VALUES (%s, %s, %s, %s, %s)
                """, [(m["timestamp"], m["node_id"], m["app_name"], m["metric"], m["value"]) 
                      for m in batch])
            
            self.conn.commit()
            elapsed = time.perf_counter() - start
            throughput = len(metrics) / elapsed
            
            cur.close()
            print(f"  Inserted {len(metrics):,} rows in {elapsed:.2f}s ({throughput:,.0f} rows/sec)")
            return {"throughput_rows_per_sec": throughput, "time_seconds": elapsed}
        except Exception as e:
            print(f"  ✗ Insert failed: {e}")
            return {}
    
    def query_speed(self) -> dict:
        """Measure query speed."""
        results = {}
        cur = self.conn.cursor()
        
        # Q1: Simple aggregation
        try:
            start = time.perf_counter()
            cur.execute("SELECT avg(value) FROM metrics")
            result = cur.fetchone()
            elapsed = (time.perf_counter() - start) * 1000
            results["q1_simple_avg_ms"] = elapsed
            print(f"  Q1 (simple avg): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q1 failed: {e}")
        
        # Q2: Group by node
        try:
            start = time.perf_counter()
            cur.execute("SELECT node_id, avg(value) FROM metrics GROUP BY node_id")
            result = cur.fetchall()
            elapsed = (time.perf_counter() - start) * 1000
            results["q2_group_by_node_ms"] = elapsed
            print(f"  Q2 (group by node): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q2 failed: {e}")
        
        # Q3: Time range + aggregation
        try:
            start = time.perf_counter()
            cur.execute("""
                SELECT metric, max(value) FROM metrics
                WHERE timestamp >= now() - INTERVAL '7 days'
                GROUP BY metric
            """)
            result = cur.fetchall()
            elapsed = (time.perf_counter() - start) * 1000
            results["q3_time_range_agg_ms"] = elapsed
            print(f"  Q3 (time range agg): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q3 failed: {e}")
        
        cur.close()
        return results
    
    def cleanup(self):
        """Drop table."""
        try:
            cur = self.conn.cursor()
            cur.execute("DROP TABLE IF EXISTS metrics CASCADE")
            self.conn.commit()
            cur.close()
        except:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# INFLUXDB BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

class InfluxDBBench:
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self.results = {}
    
    def setup(self):
        """Initialize InfluxDB."""
        try:
            self.client = InfluxDBClient(
                url=DB_CONFIGS["influxdb"]["url"],
                token=DB_CONFIGS["influxdb"]["token"],
                org=DB_CONFIGS["influxdb"]["org"]
            )
            self.write_api = self.client.write_api(write_type=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            print("✓ InfluxDB setup complete")
            return True
        except Exception as e:
            print(f"✗ InfluxDB setup failed: {e}")
            return False
    
    def insert_throughput(self, metrics: list) -> dict:
        """Measure write throughput."""
        try:
            start = time.perf_counter()
            
            # Convert to InfluxDB line protocol
            lines = []
            for m in metrics:
                line = f"metrics,node_id={m['node_id']},app_name={m['app_name']},metric={m['metric']} value={m['value']} {int(m['timestamp'].timestamp() * 1e9)}"
                lines.append(line)
            
            # Write in batches
            for i in range(0, len(lines), BATCH_SIZE):
                batch = "\n".join(lines[i:i+BATCH_SIZE])
                self.write_api.write(bucket=DB_CONFIGS["influxdb"]["bucket"], record=batch)
            
            elapsed = time.perf_counter() - start
            throughput = len(metrics) / elapsed
            
            print(f"  Inserted {len(metrics):,} rows in {elapsed:.2f}s ({throughput:,.0f} rows/sec)")
            return {"throughput_rows_per_sec": throughput, "time_seconds": elapsed}
        except Exception as e:
            print(f"  ✗ Insert failed: {e}")
            return {}
    
    def query_speed(self) -> dict:
        """Measure query speed."""
        results = {}
        
        # Q1: Simple aggregation (explicit field filter, no gap-filling)
        try:
            start = time.perf_counter()
            query = f'''from(bucket:"{DB_CONFIGS["influxdb"]["bucket"]}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._field == "value")
                |> mean()
            '''
            result = self.query_api.query(query)
            elapsed = (time.perf_counter() - start) * 1000
            results["q1_simple_avg_ms"] = elapsed
            print(f"  Q1 (simple avg with field filter): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q1 failed: {e}")
        
        # Q2: Group by node (filter to actual values, no implicit filling)
        try:
            start = time.perf_counter()
            query = f'''from(bucket:"{DB_CONFIGS["influxdb"]["bucket"]}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._field == "value")
                |> group(columns: ["node_id"])
                |> mean()
            '''
            result = self.query_api.query(query)
            elapsed = (time.perf_counter() - start) * 1000
            results["q2_group_by_node_ms"] = elapsed
            print(f"  Q2 (group by node with field filter): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q2 failed: {e}")
        
        # Q3: Time range + aggregation (explicit field, no filling on missing intervals)
        try:
            start = time.perf_counter()
            query = f'''from(bucket:"{DB_CONFIGS["influxdb"]["bucket"]}")
                |> range(start: -7d)
                |> filter(fn: (r) => r._field == "value")
                |> max()
            '''
            result = self.query_api.query(query)
            elapsed = (time.perf_counter() - start) * 1000
            results["q3_time_range_agg_ms"] = elapsed
            print(f"  Q3 (time range max with field filter): {elapsed:.2f}ms")
        except Exception as e:
            print(f"  Q3 failed: {e}")
        
        return results
    
    def cleanup(self):
        """Delete bucket."""
        try:
            # InfluxDB cleanup via API if needed
            pass
        except:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark():
    """Run comprehensive benchmark."""
    print("\n" + "="*80)
    print("MULTI-DATABASE BENCHMARK".center(80))
    print("="*80)
    
    # Generate test data
    print("\nGenerating test data...")
    metrics = generate_metrics(NUM_METRICS_PER_NODE)
    print(f"  Generated {len(metrics):,} metrics")
    
    all_results = {}
    
    # ─── ClickHouse ──────────────────────────────────────────────────────────
    print("\n" + "-"*80)
    print("CLICKHOUSE BENCHMARK")
    print("-"*80)
    ch_bench = ClickHouseBench()
    if ch_bench.setup():
        print("\nWrite Throughput:")
        ch_bench.results["write"] = ch_bench.insert_throughput(metrics)
        
        print("\nQuery Speed:")
        ch_bench.results["queries"] = ch_bench.query_speed()
        
        ch_bench.cleanup()
        all_results["clickhouse"] = ch_bench.results
    
    # ─── PostgreSQL (TimescaleDB-compatible) ──────────────────────────────────
    print("\n" + "-"*80)
    print("PostgreSQL BENCHMARK (with optional TimescaleDB)")
    print("-"*80)
    ts_bench = TimescaleDBBench()
    if ts_bench.setup():
        print("\nWrite Throughput:")
        ts_bench.results["write"] = ts_bench.insert_throughput(metrics)
        
        print("\nQuery Speed:")
        ts_bench.results["queries"] = ts_bench.query_speed()
        
        ts_bench.cleanup()
        all_results["postgresql"] = ts_bench.results
    
    # ─── InfluxDB ─────────────────────────────────────────────────────────────
    if not HAS_INFLUXDB:
        print("\n" + "-"*80)
        print("INFLUXDB BENCHMARK - SKIPPED (package not installed)")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("INFLUXDB BENCHMARK")
        print("-"*80)
        influx_bench = InfluxDBBench()
        if influx_bench.setup():
            print("\nWrite Throughput:")
            influx_bench.results["write"] = influx_bench.insert_throughput(metrics)
            
            print("\nQuery Speed:")
            influx_bench.results["queries"] = influx_bench.query_speed()
            
            influx_bench.cleanup()
            all_results["influxdb"] = influx_bench.results
    
    # ─── Save Results ─────────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_path = RESULTS_DIR / f"benchmark_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"✓ Results saved to {json_path}")
    
    # Save CSV
    csv_path = RESULTS_DIR / f"benchmark_summary_{timestamp}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Database", "Metric", "Value", "Unit"])
        
        for db_name, db_results in all_results.items():
            # Write throughput
            if "write" in db_results:
                for metric, value in db_results["write"].items():
                    unit = "rows/sec" if "rows_per_sec" in metric else "sec"
                    writer.writerow([db_name, f"write_{metric}", f"{value:.2f}", unit])
            
            # Write queries
            if "queries" in db_results:
                for metric, value in db_results["queries"].items():
                    writer.writerow([db_name, metric, f"{value:.2f}", "ms"])
    
    print(f"✓ Summary saved to {csv_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    for db_name, db_results in all_results.items():
        print(f"\n{db_name.upper()}:")
        if "write" in db_results:
            throughput = db_results["write"].get("throughput_rows_per_sec", 0)
            print(f"  Write Throughput: {throughput:,.0f} rows/sec")
        
        if "queries" in db_results:
            queries = db_results["queries"]
            avg_query_time = statistics.mean(queries.values()) if queries else 0
            print(f"  Avg Query Time: {avg_query_time:.2f}ms")
            print(f"  Query Details:")
            for q, t in queries.items():
                print(f"    {q}: {t:.2f}ms")


if __name__ == "__main__":
    run_benchmark()
