# Multi-Database Benchmark Suite

Comprehensive benchmark comparing 4 databases for time-series energy monitoring:
- **ClickHouse** - Column-oriented OLAP database
- **TimescaleDB** - PostgreSQL extension for time-series
- **InfluxDB** - Time-series specialized database
- **PostgreSQL** - Traditional relational database

## Features

✅ **Write Throughput Testing** - Measures rows inserted per second
✅ **Query Performance** - Tests 3 realistic query patterns
✅ **Automatic Results Collection** - JSON, CSV, and text reports
✅ **Visualization** - Generates comparison charts
✅ **Analysis** - Provides scoring and recommendations

## Setup

### 1. Install Dependencies

```bash
cd benchmarks
pip install -r requirements_benchmark.txt
```

### 2. Configure Databases

Edit `multi_db_benchmark.py` to set your database credentials:

```python
DB_CONFIGS = {
    "clickhouse": {
        "host": "localhost",
        "port": 9000,
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
        "token": "mytoken",
        "org": "myorg",
        "bucket": "benchmarks"
    },
}
```

### 3. Setup Databases

Ensure all databases are running:

**ClickHouse (already running in docker-compose):**
```bash
docker-compose up -d clickhouse-01 clickhouse-02
```

**TimescaleDB:**
```bash
# Install PostgreSQL + TimescaleDB
# macOS: brew install postgresql timescaledb
# Linux: apt install postgresql postgresql-client timescaledb-postgresql-12
# Windows: https://timescaledb.com/install#windows

# Create database
psql -U postgres -c "CREATE DATABASE benchmarks;"
```

**InfluxDB:**
```bash
# Install InfluxDB
# macOS: brew install influxdb
# Linux: curl https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /usr/share/keyrings/influxdb-archive-keyring.gpg > /dev/null
# Windows: https://portal.influxdata.com/downloads/

# Start InfluxDB and create bucket via UI at http://localhost:8086
```

## Running Benchmarks

### Run Full Benchmark

```bash
python multi_db_benchmark.py
```

This will:
1. Generate 100,000 synthetic metrics
2. Test write throughput for each database
3. Run query benchmarks (3 different query patterns)
4. Save detailed results to `results/` folder
5. Print summary to console

**Expected output:**
```
================================================================================
MULTI-DATABASE BENCHMARK
================================================================================

Generating test data...
  Generated 100,000 metrics

────────────────────────────────────────────────────────────────────────────────
CLICKHOUSE BENCHMARK
────────────────────────────────────────────────────────────────────────────────

Write Throughput:
  Inserted 100,000 rows in 1.23s (81,300 rows/sec)

Query Speed:
  Q1 (simple avg): 0.45ms
  Q2 (group by node): 2.34ms
  Q3 (time range agg): 5.67ms

...
```

### Generate Analysis & Plots

After running the benchmark, generate visualizations and analysis:

```bash
python analyze_benchmark.py
```

This creates:
- `write_throughput.png` - Bar chart comparing write speeds
- `query_performance.png` - Bar chart comparing average query times
- `query_breakdown.png` - Detailed query performance by type
- `overall_score.png` - Composite performance score
- `benchmark_report.txt` - Detailed text report

## Test Queries

The benchmark tests 3 representative queries:

### Q1: Simple Aggregation (Analytics)
```sql
SELECT avg(value) FROM metrics
```
✓ Tests: Basic aggregation, full table scan

### Q2: Group By Node (Real-time Monitor)
```sql
SELECT node_id, avg(value) FROM metrics GROUP BY node_id
```
✓ Tests: Grouping, aggregation efficiency

### Q3: Time Range Aggregation (Historical Analysis)
```sql
SELECT metric, max(value) FROM metrics 
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY metric
```
✓ Tests: Time filtering, range queries, complex aggregation

## Benchmark Parameters

Edit in `multi_db_benchmark.py`:

```python
NUM_NODES = 10                    # Number of nodes
NUM_APPS = 5                      # Apps per node
NUM_METRICS_PER_NODE = 100_000   # Records to insert (100K)
BATCH_SIZE = 1000                # Batch insert size
NUM_TIME_SERIES = 50             # Total series (nodes × apps)
```

## Results Interpretation

### Write Throughput
- **Higher is better** (rows per second)
- ClickHouse and InfluxDB typically excel here

### Query Performance  
- **Lower is better** (milliseconds)
- TimescaleDB excels at complex queries due to PostgreSQL's optimizer

### Overall Score
- Composite metric (0-100)
- Balances throughput and query performance
- Choose highest score for your workload

## Example Results

```
BENCHMARK SUMMARY
================================================================================

CLICKHOUSE:
  Write Throughput: 125,000 rows/sec
  Avg Query Time: 1.23ms
  Q1: 0.45ms, Q2: 1.12ms, Q3: 2.34ms

TIMESCALEDB:
  Write Throughput: 45,000 rows/sec
  Avg Query Time: 2.45ms
  Q1: 0.89ms, Q2: 2.14ms, Q3: 4.23ms

INFLUXDB:
  Write Throughput: 95,000 rows/sec
  Avg Query Time: 3.67ms
  Q1: 1.23ms, Q2: 3.45ms, Q3: 6.78ms

POSTGRESQL:
  Write Throughput: 28,000 rows/sec
  Avg Query Time: 4.12ms
  Q1: 1.56ms, Q2: 4.01ms, Q3: 7.23ms
```

## Recommendations

| Scenario | Best Choice | Why |
|----------|------------|-----|
| **High write volume** | ClickHouse | Optimized for columnar storage and aggregation |
| **Complex queries** | TimescaleDB | PostgreSQL query optimizer handles complexity |
| **Time-series optimized** | InfluxDB | Purpose-built for metrics, good compression |
| **ACID guaranteed** | PostgreSQL | Traditional relational guarantees |


## Files

- `multi_db_benchmark.py` - Main benchmark runner
- `analyze_benchmark.py` - Analysis and visualization 
- `requirements_benchmark.txt` - Python dependencies
- `results/` - Output directory (created automatically)
  - `benchmark_results_YYYYMMDD_HHMMSS.json` - Detailed results
  - `benchmark_summary_YYYYMMDD_HHMMSS.csv` - Summary CSV
  - `*.png` - Comparison charts
  - `benchmark_report.txt` - Analysis report

## Troubleshooting

### "Cannot connect to database"
- Verify database is running: `ping localhost`
- Check port: ClickHouse (9000), TimescaleDB (5432), InfluxDB (8086)
- Verify credentials in `DB_CONFIGS`

### "ImportError: No module named 'clickhouse_connect'"
```bash
pip install -r requirements_benchmark.txt
```

### "Out of memory"
Reduce `NUM_METRICS_PER_NODE` to 10,000 or 50,000

### Slow InfluxDB writes
InfluxDB might be single-threaded - verify sufficient disk I/O

## Notes

- Benchmarks use clean test databases (tables dropped after each run)
- Results vary based on hardware, system load, and database configuration
- For production decisions, benchmark with your actual data distribution
- TimescaleDB and PostgreSQL may need tuning (`work_mem`, `maintenance_work_mem`)
