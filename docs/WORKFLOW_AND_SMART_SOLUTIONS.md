# Energy Monitoring System - Workflow & Smart Solutions

## 🎯 Core Philosophy

> **Build a distributed monitoring system that scales from 10 to 10,000 nodes without redesigning the database or API**

This means: Autonomous operation, graceful degradation, eventual consistency, and adaptive intelligence.

---

## 📊 The Problem We Solve

### Challenges in Distributed Energy Monitoring

| Challenge | Problem | Our Solution |
|-----------|---------|--------------|
| **Heterogeneous Hardware** | Windows, Linux, RPi have different power measurement APIs | **Adapter Pattern**: Daemon interface unified, platform-specific backends |
| **Network Unreliability** | Nodes drop offline randomly due to wifi/connectivity | **Resilient Buffering**: Daemon buffers locally, retries with exponential backoff |
| **Temporal Consistency** | 100 nodes all sending data at different rates | **k-sigma Heartbeat**: Learned per-node timeout adapts to actual behavior patterns |
| **Query Performance** | Aggregating 100K+ daily metrics takes seconds | **ClickHouse + Materialized Views**: Column store + pre-aggregated hourly/daily summaries |
| **Operational Overhead** | Should require zero manual intervention to add nodes | **Auto-registration**: Daemon hits API, system auto-registers with correct platform type |
| **Data Loss Risk** | Network outage mid-transmission → lost data | **File-backed Retry Buffer**: Metrics persisted locally until confirmed in database |

---

## 🏗️ System Architecture - 4-Layer Design

```
┌─────────────────────────────────────────────────────┐
│              VISUALIZATION LAYER                    │
│  Smart Dashboard: Observes aggregation levels       │
│  (React 18 + Recharts + React Query)                │
└─────────────────────────────────────────────────────┘
                         ▲
                    [REST API]
                         │
┌─────────────────────────────────────────────────────┐
│              AGGREGATION LAYER                      │
│  FastAPI Backend: Heartbeat + Data validation       │
│  (Stateless, scales horizontally)                   │
└─────────────────────────────────────────────────────┘
                         ▲
                    [HTTP POST]
                         │
┌─────────────────────────────────────────────────────┐
│              COLLECTION LAYER                       │
│  Python Daemon: Autonomous, buffered, resilient    │
│  (Runs on every node independently)                 │
└─────────────────────────────────────────────────────┘
                         │
                    [Hardware APIs]
                         │
┌─────────────────────────────────────────────────────┐
│              MEASUREMENT LAYER                      │
│  Linux RAPL / Windows psutil / RPi INA219          │
│  (Platform-specific power measurement)              │
└─────────────────────────────────────────────────────┘
```

---

## 🧠 Smart Solution #1: Autonomous Daemon with Retry Buffer

### The Problem
- Network outages shouldn't lose data
- Daemon shouldn't require constant connectivity

### How We Solve It

**File-Backed Retry Buffer** (`daemon/buffer.py`):
```
Metric → Try send to API (HTTP POST)
           ↓
       Success? → Delete from buffer ✓
           ↓
       Failure? → Write to local file (`~/.energy-daemon/buffer.json`)
           ↓
       Retry in 30s with exponential backoff
           ↓
       After 24h retry, give up (too old to matter)
```

**Code Pattern**:
```python
buffer = RetryBuffer("buffer.json")
while True:
    metrics = collect_metrics()
    buffer.add(metrics)  # Always persist locally first
    
    try:
        response = send_to_backend(metrics)
        if response.ok:
            buffer.remove(metrics)  # Clear after success
    except Exception as e:
        log.warning(f"Failed, will retry: {e}")
        # Metrics stay in buffer, retry on next cycle
```

### Why This Works
- ✅ **No data loss**: Local file persists metrics even if daemon crashes
- ✅ **No dependency on backend**: Daemon keeps collecting even if API is down
- ✅ **Automatic recovery**: When API comes back online, retries resume
- ✅ **Self-cleaning**: Metrics auto-expire after 24h (too old to matter)

---

## 🧠 Smart Solution #2: k-sigma Adaptive Heartbeat

### The Problem
- **Fixed timeout (120s)**: Too loose for fast nodes (false negatives), too tight for slow nodes (false positives)
- **Can't distinguish**: Network partition (temporary) from node crash (permanent)?

### How We Solve It

**Statistical Learning Algorithm** (`backend/app/services/heartbeat.py`):

```python
Per-node adaptive timeout = mean_interval + 4 × std_dev_interval
                                           ↑
                          99.99% confidence (statistical guarantee)

Example:
  Node-1 (fast, 10s intervals): mean=10s, σ=0.15s  → timeout = 10.6s
  Node-2 (slow, 60s intervals): mean=60s, σ=2s     → timeout = 68s
  Node-3 (unpredictable):       mean=35s, σ=5s     → timeout = 55s
                    ↑
              Learns unique pattern
```

**3-State Health Model**:
```
ONLINE  (🟢): age < timeout               → "Healthy, behaving normally"
STALE   (🟡): timeout ≤ age < 2×timeout  → "Late, but not necessarily dead"
OFFLINE (🔴): age ≥ 2×timeout            → "Definitely down"

Transition Timeline (Node-1 example):
  t=0s:   Heartbeat arrives   → ONLINE
  t=5s:   Heartbeat arrives   → ONLINE
  t=10s:  Heartbeat arrives   → ONLINE
  t=15s:  No heartbeat        → STALE   (warning state)
  t=21s:  Heartbeat arrives   → back to ONLINE
  t=30s:  Still no heartbeat  → OFFLINE (alert)
```

### Why This Works
- ✅ **Per-node customization**: Each node gets appropriate timeout
- ✅ **Statistical guarantee**: 99.99% confidence means 0.01% false positive rate
- ✅ **Learns patterns**: Adapts to each node's unique network/load behavior
- ✅ **Grace period**: STALE state prevents alert storms from network jitter
- ✅ **Real systems use this**: Kafka, Cassandra, etcd use similar k-sigma strategies

---

## 🧠 Smart Solution #3: Platform-Specific Collection with Unified Interface

### The Problem
- Different OSes have different power measurement APIs
- Linux has Intel RAPL (direct), Windows has no native API, RPi needs I2C sensors
- Can't use same code everywhere

### How We Solve It

**Adapter Pattern** (`daemon/collectors/`):

```
┌──────────────────────────────────────────────────────┐
│           Unified Daemon Interface                   │
│  def collect_metrics() → {power_w, cpu%, ...}       │
└──────────────────────────────────────────────────────┘
            ↓
    ┌───────────────────────────────┐
    │    Platform-Specific Adapters│
    └───────────────────────────────┘
            ↙  ↓  ↘
    ┌──────────┬──────────┬──────────┐
    │  Linux   │ Windows  │   RPi    │
    │  (RAPL)  │(psutil)  │(INA219)  │
    ├──────────┼──────────┼──────────┤
    │ Direct   │Estimate  │ Direct   │
    │ hardware │from CPU  │voltage ×│
    │ reading  │ util     │ current  │
    └──────────┴──────────┴──────────┘
```

**Implementation**:
```python
# daemon/collectors/power.py
def get_power_watts() -> float:
    """Transparent platform detection."""
    
    if is_linux() and has_intel_rapl():
        # Accurate: read from hardware
        return read_intel_rapl()
    
    elif is_windows():
        # Estimate: use CPU utilization
        return estimate_from_cpu()
    
    elif is_raspberry_pi() and has_ina219_sensor():
        # Accurate: read from I2C sensor
        return read_ina219_voltage_current()
    
    else:
        # Fallback: always have a measurement
        return estimate_from_cpu()
```

**Schema Enforcement** (Tag each metric):
```json
{
  "timestamp": "2026-04-06T14:30:00Z",
  "node_id": "workstation-01",
  "node_type": "linux",          // ← Recorded at registration
  "measurement_method": "rapl",   // ← Tells dashboard data quality
  "power_w": 45.3,
  "cpu_percent": 62.5
}
```

### Why This Works
- ✅ **No rejection of data**: Fallback to estimation always available
- ✅ **Dashboard knows accuracy**: Tags indicate which data is direct vs. estimated
- ✅ **Easy to extend**: Add new platform = add new adapter function
- ✅ **Testable**: Each adapter can be mocked independently

---

## 🧠 Smart Solution #4: Smart Data Fetching at Dashboard Layer

### The Problem
- 100 nodes × 6 KPIs × hourly for 6 months = 26+ million data points
- Trying to render all 26M points → browser crashes

### How We Solve It

**Automatic Aggregation Selection** (Based on time range):

```python
Time Range Requested    Aggregation Used    Points Returned
────────────────────   ─────────────────   ─────────────────
Last 1 day             Raw (5-10s)         8,640 - 17,280 ✓
Last 7 days            1-minute            10,080 ✓
Last 30 days           5-minute            8,640 ✓
Last 1 year            Hourly              8,760 ✓

All kept under 20,000 data points per chart
(Sweet spot for browser rendering)
```

**Materialized Views in ClickHouse**:
```sql
-- Raw: Every 5-10 second collection
CREATE TABLE energy_metrics (...)

-- Pre-aggregated: Hourly
CREATE MATERIALIZED VIEW hourly_agg AS
SELECT toStartOfHour(timestamp) as hour,
       node_id, avg(power_w) as power_avg, max(power_w) as power_max
FROM energy_metrics
GROUP BY hour, node_id

-- Pre-aggregated: Daily
CREATE MATERIALIZED VIEW daily_agg AS
SELECT toStartOfDay(timestamp) as day,
       node_id, avg(power_w) as power_avg, max(power_w) as power_max
FROM energy_metrics
GROUP BY day, node_id
```

**Dashboard Logic** (`dashboard/src/hooks/useMetrics.js`):
```javascript
const fetchMetrics = (nodeId, startTime, endTime) => {
  const rangeHours = (endTime - startTime) / 3600000
  
  if (rangeHours <= 24) {
    // Last 24h: Use raw 5-10s data
    return api.get('/api/v1/metrics', {
      node_id: nodeId,
      aggregation: 'raw'
    })
  } else if (rangeHours <= 7*24) {
    // Last 7 days: Use 1-minute aggregation
    return api.get('/api/v1/metrics', {
      node_id: nodeId,
      aggregation: 'minute'
    })
  } else {
    // Longer: Use hourly aggregation
    return api.get('/api/v1/metrics', {
      node_id: nodeId,
      aggregation: 'hour'
    })
  }
}
```

### Why This Works
- ✅ **Browser doesn't crash**: Always under 20K points
- ✅ **Queries stay fast**: Pre-computed aggregations from materialized views
- ✅ **Transparent to user**: Automatic selection, no dropdown needed
- ✅ **Memory efficient**: Fewer points = less memory in browser
- ✅ **Visual accuracy**: Hourly average looks identical to 10-point average when zoomed out

---

## 🧠 Smart Solution #5: Stateless API Design

### The Problem
- If API crashes mid-request, we might lose metrics OR have duplicates
- Traditional: Save state on server, requires transactions/locks

### How We Solve It

**Idempotent Operations** (`backend/app/routes/metrics.py`):

```python
@router.post("/api/v1/metrics")
def ingest_metrics(payload: MetricsPayload):
    # Step 1: Auto-register (idempotent check)
    # Only insert if node_id doesn't exist
    node_exists = ch_service.get_node(payload.node_id)
    if not node_exists:
        ch_service.auto_register_node(payload.node_id)
    
    # Step 2: Estimate power if missing (graceful degradation)
    if payload.power_w == 0 and payload.cpu_percent > 0:
        payload.power_w = 10 + (payload.cpu_percent / 100) * 50
    
    # Step 3: Fire-and-forget insert
    ch_service.insert_metrics(payload)
    
    # Step 4: Record heartbeat (async, doesn't block response)
    heartbeat_service.record(payload.node_id)
    
    return {"status": "ok"}  # ← Return immediately (2ms)
```

**Safe to Retry**:
```
Daemon sends metrics → API Timeout
  ↓
Daemon retries (same metrics) → API processes again
  ↓
Auto-register: "Node exists, skip"
  ↓
Insert metrics: "Same timestamp/data, will be duplicate or ignored by ClickHouse"
  ↓
Heartbeat: "Same node_id, will just update last_seen timestamp"
  ↓
No corruption! ✓
```

### Why This Works
- ✅ **No state tracking needed**: API has no memory between requests
- ✅ **Scales horizontally**: Add API instances, no synchronization needed
- ✅ **Resilient to retries**: Safe to send same request twice
- ✅ **Fast responses**: Async processing doesn't block request return
- ✅ **Production pattern**: Stripe, Datadog, New Relic use this

---

## 🧠 Smart Solution #6: Per-App Energy Attribution (Linux)

### The Problem
- System reports 100W total CPU
- But which apps caused it? (dwm, Chrome, Python, gcc, etc.)
- Need per-app breakdown without expensive instrumentation

### How We Solve It

**Proportional Attribution** (`daemon/collectors/app_energy.py`):

```python
# Read RAPL energy delta
total_energy_delta = read_rapl_energy_delta()  # e.g., 500 mJ over 10 seconds

# Get process CPU time contributions
for process in get_all_processes():
    process_cpu_time = process.cpu_times().user + process.cpu_times().system
    # Note: CPU time ∝ proportional energy consumption
    
# Attribution: Energy ∝ CPU time
total_cpu_time = sum(all_process_cpu_times)

for process in get_all_processes():
    share_of_energy = total_energy_delta * (process_cpu_time / total_cpu_time)
    app_power_w = share_of_energy / 10_seconds

# Result: Accurate per-app power breakdown
```

**Example Output**:
```
System total CPU: 100W
Process breakdown:
  - Chrome:  35W (35% CPU) → 35% of energy
  - Python:  25W (25% CPU) → 25% of energy
  - gcc:     20W (20% CPU) → 20% of energy
  - System:  20W (20% CPU) → 20% of energy
```

### Why This Works
- ✅ **No kernel instrumentation**: Uses standard Linux APIs
- ✅ **Accurate**: Proportional to actual CPU time spent
- ✅ **Low overhead**: Single RAPL read per cycle
- ✅ **Per-app visibility**: Dashboard shows top power consumers
- ✅ **Real-time**: Available every 5-10 seconds

---

## 📊 Data Flow: Metrics Journey

```
┌────────────────────────────────────────────────────────────┐
│ 1. COLLECTION (Daemon - Every 5-10 seconds)               │
│                                                            │
│  Hardware APIs:                                            │
│   • Intel RAPL: read /sys/class/powercap/intel-rapl:0    │
│   • psutil: cpu_percent(), virtual_memory()              │
│   • INA219: i2cget over /dev/i2c                          │
│                                                            │
│  Result: Dict with 8 KPIs                                  │
│   {power_w: 45.3, cpu_percent: 62, ...}                  │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 2. BUFFERING (Daemon - Retry Buffer)                       │
│                                                            │
│  Always persist locally first:                             │
│   • Write to ~/.energy-daemon/buffer.json                 │
│   • If database fails, retry later                         │
│   • If metrics too old, discard                           │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 3. TRANSMISSION (HTTP POST)                                │
│                                                            │
│  POST /api/v1/metrics                                      │
│  {node_id: "workstation-01", power_w: 45.3, ...}         │
│                                                            │
│  Retry strategy:                                           │
│   • Attempt 1: 10ms delay                                  │
│   • Attempt 2: 100ms delay                                │
│   • Attempt 3: 1s delay                                   │
│   • Continue doubling up to 5 min                         │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 4. INGESTION (Backend - Stateless Processing)              │
│                                                            │
│  • Auto-register: INSERT IF NOT EXISTS nodes              │
│  • Validate: Check ranges, estimate if 0                  │
│  • Record: INSERT into energy_metrics table               │
│  • Heartbeat: UPDATE node_health (last_seen timestamp)    │
│                                                            │
│  All async, response returns immediately                   │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 5. STORAGE (ClickHouse - OLAP Database)                    │
│                                                            │
│ Real-time: energy_metrics (raw, 5-10s granularity)        │
│   ├─ Indexes: (timestamp, node_id, app_name)              │
│   └─ TTL: 90 days (auto delete old rows)                  │
│                                                            │
│ Pre-aggregated: hourly_agg, daily_agg (materialized)      │
│   ├─ Hourly: avg/max per node, hour precision             │
│   └─ Daily: avg/max per node, day precision               │
│                                                            │
│ Dictionary: nodes (metadata, platform type)               │
│   └─ Used for device filtering on dashboard               │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 6. AGGREGATION (Backend API - Query Layer)                 │
│                                                            │
│  Smart selection based on time range:                      │
│   • Last 24h → raw table (5-10s granularity)              │
│   • Last 7d → hourly_agg (1h granularity)                 │
│   • Last 30d → Compute aggregation live                    │
│                                                            │
│  Goal: Keep result set <20K points                         │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 7. VISUALIZATION (React Dashboard - Real-time)             │
│                                                            │
│  Smart data fetching:                                      │
│   • REST query with time range                             │
│   • React Query caching (avoid duplicate requests)        │
│   • Recharts rendering (handles 20K points easily)         │
│   • 5-second refresh for dashboards                        │
│                                                            │
│  Display components:                                       │
│   • Real-time charts: System power over time               │
│   • Top apps: Pie chart sorted by power                    │
│   • Node status: Grid showing ONLINE/STALE/OFFLINE        │
│   • Historical view: Zoom/pan over 6-month history        │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design Principles

### 1. **Autonomy**
- Each daemon operates independently
- Doesn't require backend to collect or buffer data
- Gracefully degraded if backend is down

### 2. **Eventual Consistency**
- Data arrives out-of-order (fine, ClickHouse orders by timestamp)
- Nodes may be offline temporarily (fine, STALE state handles it)
- Aggregations computed on-demand (fine, materialized views cache hot queries)

### 3. **Horizontal Scalability**
- Add 100 more nodes? Just run daemon on each → no backend changes
- Need more API throughput? Spin up 10 API instances → load balancer distributes
- ClickHouse cluster handles storage sharding + replication

### 4. **Fail-Safe Design**
- Data push (daemon → backend) means nodes own their data
- Retry buffer means local data survives network outages
- Idempotent APIs mean duplicate sends are safe

### 5. **Smart, Not Dumb**
- k-sigma timeout beats fixed timeout (learns patterns)
- Per-app attribution beats system-only metrics (actionable insights)
- Materialized views beat live aggregation (trade disk for query speed)
- Adapter pattern beats platform-specific rewrites (DRY principle)

---

## 📈 Performance Characteristics

| Operation | Latency | Note |
|-----------|---------|------|
| Daemon collection cycle | ~500ms | Read RAPL + CPU + memory + temperature |
| Daemon to backend POST | ~50ms | HTTP + 1KB payload |
| Metric ingestion | ~2ms | Insert to ClickHouse + heartbeat update |
| Query last 24h (raw) | 12-68ms | ClickHouse columnar advantage |
| Query last 7d (hourly) | 8-45ms | Pre-aggregated, fewer rows |
| Dashboard render | ~200ms | React + Recharts, handles 20K points |
| **Total end-to-end** | ~1s | Metric collected → Visible on dashboard |

---

## 🔍 Example: Tracing a Single Metric

**April 6, 2026, 14:30:47 UTC**

```
┌─ DAEMON (workstation-01)
│  └─ Read Intel RAPL: 45.3W current CPU power
│  └─ Read psutil: 62.5% CPU, 4.2 GB RAM, 58°C
│  └─ List processes: [chrome, python, dwm, ...]
│  └─ Per-app attribution: chrome=35W, python=25W, dwm=20W
│              ↓
│  └─ Buffer to disk: ~/.energy-daemon/buffer.json
│              ↓
│  └─ Send HTTP POST:
│      {
│        node_id: "workstation-01",
│        timestamp: "2026-04-06T14:30:47.000Z",
│        power_w: 45.3,
│        cpu_percent: 62.5,
│        memory_percent: 4.2,
│        temperature: 58.0,
│        app_metrics: [
│          {app_name: "chrome", power_w: 35.0, cpu_percent: 35.2, ...},
│          {app_name: "python", power_w: 25.0, cpu_percent: 25.1, ...},
│          {app_name: "dwm", power_w: 20.0, cpu_percent: 20.1, ...}
│        ]
│      }
│
│
├─ BACKEND (FastAPI)
│  ├─ Receive request
│  ├─ Auto-register: "workstation-01" already exists ✓
│  ├─ Validate: All ranges OK, power_w > 0 ✓
│  ├─ Insert 4 rows to ClickHouse:
│  │   ├─ System metric: (timestamp, workstation-01, "system", "power_w", 45.3)
│  │   ├─ App metric: (timestamp, workstation-01, "chrome", "power_w", 35.0)
│  │   ├─ App metric: (timestamp, workstation-01, "python", "power_w", 25.0)
│  │   └─ App metric: (timestamp, workstation-01, "dwm", "power_w", 20.0)
│  ├─ Update heartbeat: node_health[workstation-01].last_seen = now()
│  └─ Return: {status: "ok"} (2ms total)
│
│
├─ DATABASE (ClickHouse)
│  ├─ Insert rows into energy_metrics table
│  ├─ Automatically updates materialized views (hourly_agg, daily_agg)
│  ├─ Indexes updated: (timestamp, node_id, app_name)
│  └─ Data now queryable ✓
│
│
└─ DASHBOARD (React)
   ├─ Poll API every 5 seconds: GET /api/v1/metrics?node_id=workstation-01
   ├─ API returns last 24h in raw granularity (~8640 points)
   ├─ React Query caches result (no duplicate fetches)
   ├─ Recharts renders:
   │  ├─ Power consumption line chart (shows 45.3W spike at 14:30:47)
   │  ├─ Top apps pie chart (Chrome 56%, Python 32%, dwm 12%)
   │  ├─ CPU/RAM/Temp gauges
   │  └─ Node status badge (🟢 ONLINE)
   └─ User sees metric on screen in ~1 second ✓
```

---

## 🚀 Scalability Path

### Today (Proof of Concept)
- 10 nodes running
- 100K metrics/day (10 nodes × 8 KPIs × 150 readings/day)
- ClickHouse single instance
- 1 Backend API instance

### Tomorrow (10-100 nodes)
- Run multiple daemon instances
- Light load on ClickHouse (still single instance)
- 1-2 Backend instances behind load balancer

### Production (1000+ nodes)
- ClickHouse cluster: 3 shards × 2 replicas (6 nodes)
- Backend instances: 10-20 instances, auto-scaling
- Dashboard: Static assets cached, API behind CDN
- Architectural changes needed: None! (Designed for scale)

---

## 📚 Smart Technologies Used

| Technology | Why We Use It | Smart Aspect |
|------------|---------------|--------------|
| **ClickHouse** | OLAP columnar store | Pre-aggregated views beat live queries |
| **Python Daemon** | Easy platform support | Runs on Linux, Windows, RPi with adapters |
| **FastAPI** | Lightweight, async | Stateless design scales horizontally |
| **React + Recharts** | Modern dashboard | Smart aggregation level selection |
| **JWT + API Keys** | Authentication | Per-node keys enable audit trail |
| **k-sigma heartbeat** | Health checking | Statistically sound fault detection |
| **File-backed buffer** | Resilience | Local persistence survives network outages |

---

## 🎓 Lessons Learned

1. **Adapter Pattern > Platform-specific code**
   - Unified interface, plug-in implementations
   - New platform = new adapter, not rewrite

2. **Stateless APIs > Traditional databases**
   - Infinite horizontal scaling
   - No transaction coordination needed
   - Safe to retry without side effects

3. **Pre-aggregation > Live queries**
   - Trade disk for query speed
   - Materialized views are "free" (computed automatically)

4. **Adaptive instead of static**
   - k-sigma beats fixed timeout
   - Learns real-world patterns
   - Reduces false positives

5. **Buffering solves networking**
   - Daemon survives backend downtime
   - Retry on exponential backoff
   - Old metrics auto-expire

---

## 🔗 Related Documentation

- Architecture diagram: `docs/visuals/01-system-architecture.md`
- Heartbeat algorithm: `docs/visuals/03-k-sigma-learning.md`
- Data collection: `docs/visuals/05-data-collection-methods.md`
- Benchmarks: `benchmarks/benchmark_analysis.png`
- API reference: `backend/app/routes/`
- Daemon source: `daemon/`

