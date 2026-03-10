# Energy Monitoring System — Complete Execution Plan (Revised)

**Date:** March 2026
**Status:** Skeleton setup complete. No services running yet.
**Professor feedback integrated:** Per-application energy, DB replication, shell benchmarking.

---

## What Changed After Professor Review

| Feedback | Impact | Action |
|----------|--------|--------|
| Energy should be **per-application**, not whole CPU | Major change to daemon collectors + DB schema + dashboard | Add process-level RAPL tracking via `perf` or `/sys/class/powercap` sub-domains. Each metric row now includes `app_name`. |
| The monitored **application name must be displayed** | Dashboard must show which app is consuming what | Add app selector, per-app charts, per-app energy breakdown table |
| **Database replication** for resilience (not just a buffer) | ClickHouse cluster setup with replication | Deploy 2-node ClickHouse with `ReplicatedMergeTree` + ZooKeeper/Keeper |
| **Shell-based benchmarking** later | Keep Python daemon now, add shell collector scripts for benchmark comparison | Create `benchmarks/shell/` with bash scripts reading same KPIs, compare overhead vs Python |
| Linux-focused, Android has Python overhead | Mobile stays in scope but lower priority | Keep Flutter/RN mobile, note Python overhead limitation in docs |

---

## What's Already Done (Step 1 — Skeleton)

```
[DONE] Directory structure (47 files)
[DONE] backend/     — FastAPI app, routes, services, auth, schemas, Dockerfile
[DONE] daemon/      — Main loop, 5 collectors, buffer, config, systemd
[DONE] dashboard/   — React 18 app, 4 pages, 5 components, hooks, services
[DONE] benchmarks/  — data_generator.py, benchmark_runner.py
[DONE] docker-compose.yml, init.sql, README.md, project-plan.md
```

**None of this is running yet.** Everything below is what's needed to go from skeleton to a fully working, testable system.

---

## Revised Architecture

```
                         ┌──────────────────────────┐
                         │      Web Dashboard       │
                         │   React 18 + Tailwind    │
                         │  Per-app energy breakdown │
                         └────────────┬─────────────┘
                                      │ GET /api/v1/*
                                      ▼
┌─────────────┐  POST    ┌──────────────────────┐      ┌─────────────────────────┐
│ Workstation  ├────────►│    Backend API        │     │  ClickHouse Cluster     │
│ Daemon       │         │    (FastAPI)          │────►│                         │
│ (Python +    │         │                      │     │  Node 1 (primary)       │
│  per-app     │         │  • Auth              │     │     ▲                   │
│  RAPL)       │         │  • Heartbeat         │     │     │ replication       │
└─────────────┘         │  • Aggregation       │     │     ▼                   │
┌─────────────┐  POST    │  • Per-app routing   │     │  Node 2 (replica)       │
│ RPi Daemon   ├────────►│                      │     │                         │
└─────────────┘         └──────────────────────┘     └─────────────────────────┘
┌─────────────┐  POST                                    ▲
│ Mobile App   ├─────────────────────────────────────────┘
└─────────────┘         (ZooKeeper / ClickHouse Keeper)
```

---

## Revised Database Schema

### Changes from original

1. **`energy_metrics` table** — Add `app_name` column to track which application the energy belongs to
2. **Engine** — Change from `MergeTree` to `ReplicatedMergeTree` for replication
3. **New materialized view** — Per-app energy aggregation

```sql
-- Main data table (REVISED)
CREATE TABLE energy_metrics ON CLUSTER 'energy_cluster' (
    timestamp   DateTime64(3),
    node_id     LowCardinality(String),
    app_name    LowCardinality(String) DEFAULT 'system',  -- NEW: application name
    metric      LowCardinality(String),
    value       Float64
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/energy_metrics', '{replica}')
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (node_id, app_name, metric, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- Hourly aggregation (REVISED — includes app_name)
CREATE MATERIALIZED VIEW energy_hourly_mv ON CLUSTER 'energy_cluster'
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/{shard}/energy_hourly_mv', '{replica}'
)
PARTITION BY toYYYYMMDD(hour)
ORDER BY (node_id, app_name, metric, hour)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    node_id,
    app_name,
    metric,
    avg(value)   AS avg_value,
    min(value)   AS min_value,
    max(value)   AS max_value,
    count()      AS sample_count
FROM energy_metrics
GROUP BY hour, node_id, app_name, metric;

-- Daily energy summary (REVISED)
CREATE MATERIALIZED VIEW energy_daily_mv ON CLUSTER 'energy_cluster'
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/{shard}/energy_daily_mv', '{replica}'
)
PARTITION BY toYYYYMM(day)
ORDER BY (node_id, app_name, day)
AS SELECT
    toDate(timestamp)       AS day,
    node_id,
    app_name,
    sum(if(metric='power_w', value, 0)) /
        count(if(metric='power_w', value, NULL)) AS avg_power_w,
    max(if(metric='power_w', value, 0))           AS peak_power_w,
    max(if(metric='temperature', value, 0))        AS peak_temp
FROM energy_metrics
GROUP BY day, node_id, app_name;

-- Per-app energy ranking (NEW)
CREATE MATERIALIZED VIEW energy_app_ranking_mv ON CLUSTER 'energy_cluster'
ENGINE = ReplicatedAggregatingMergeTree(
    '/clickhouse/tables/{shard}/energy_app_ranking_mv', '{replica}'
)
PARTITION BY toYYYYMMDD(hour)
ORDER BY (node_id, hour, app_name)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    node_id,
    app_name,
    sum(if(metric='power_w', value, 0))   AS total_power,
    count()                                AS sample_count
FROM energy_metrics
WHERE app_name != 'system'
GROUP BY hour, node_id, app_name;

-- Registered nodes (REVISED)
CREATE TABLE nodes ON CLUSTER 'energy_cluster' (
    node_id     String,
    node_type   LowCardinality(String),
    api_key     String,
    description String,
    registered  DateTime DEFAULT now()
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/nodes', '{replica}')
ORDER BY node_id;
```

---

## Revised Daemon — Per-Application Energy Collection

### How per-app energy works on Linux

Intel RAPL exposes energy counters per power domain:
```
/sys/class/powercap/intel-rapl:0/            ← Package (whole CPU socket)
/sys/class/powercap/intel-rapl:0:0/          ← Core
/sys/class/powercap/intel-rapl:0:1/          ← Uncore (GPU, memory controller)
/sys/class/powercap/intel-rapl:0:2/          ← DRAM
```

To get **per-application** energy, we need to:

1. **Use `perf_event` interface** — `perf stat -e power/energy-pkg/ -p <PID>` gives energy consumed by a specific process
2. **Or use `scaphandre`** — A tool that attributes RAPL energy to individual processes based on CPU time ratio
3. **Our approach** — Read RAPL total, read per-process CPU time from `/proc/<pid>/stat`, compute each app's energy share proportionally:

```
App energy = (app_cpu_time / total_cpu_time) × RAPL_total_energy
```

### New collector: `daemon/collectors/app_energy.py`

```python
# Reads running processes, computes per-app energy attribution
# Returns: [{"app_name": "firefox", "power_w": 12.3, "energy_wh": 0.5}, ...]
# Uses: /proc/<pid>/stat for CPU time, RAPL for total package energy
# Configurable: config.yaml lists which apps to track, or "top N by CPU"
```

### Updated config.yaml

```yaml
node_id: "workstation-01"
node_type: "workstation"
backend_url: "http://localhost:8000/api/v1/metrics"
api_key: "sk-xxxxxxxxxxxxxxxxxxxx"
collection_interval_seconds: 10
retry_interval_seconds: 30
buffer_max_records: 3600

# NEW: per-application energy tracking
app_tracking:
  enabled: true
  mode: "top_n"        # "top_n" = track top N CPU consumers, "whitelist" = track listed apps
  top_n: 10            # number of top processes to track
  whitelist:           # used when mode = "whitelist"
    - firefox
    - python3
    - gcc
    - java
  min_cpu_percent: 1.0 # ignore processes below this CPU usage
```

### Updated payload format

```json
{
  "node_id": "workstation-01",
  "timestamp": "2026-03-09T14:30:00.000Z",
  "metrics": {
    "voltage": 220.5,
    "cpu_freq": 3200.0,
    "cpu_util": 45.2,
    "ram_util": 62.8,
    "temperature": 58.3,
    "power_w": 85.4,
    "energy_wh": 1024.7,
    "uptime_s": 86400
  },
  "app_metrics": [
    {
      "app_name": "firefox",
      "pid": 12345,
      "cpu_percent": 15.2,
      "power_w": 18.3,
      "energy_wh": 42.1
    },
    {
      "app_name": "python3",
      "pid": 67890,
      "cpu_percent": 8.7,
      "power_w": 10.5,
      "energy_wh": 24.3
    }
  ]
}
```

The backend unpacks `metrics` into rows with `app_name='system'` and `app_metrics` into rows with the actual app name.

---

## Revised Docker Compose — ClickHouse Replication

```yaml
# 2-node ClickHouse cluster with Keeper for replication
services:
  clickhouse-keeper:
    image: clickhouse/clickhouse-server:latest
    volumes:
      - ./backend/keeper-config.xml:/etc/clickhouse-server/config.d/keeper.xml
    ports:
      - "9181:9181"

  clickhouse-01:
    image: clickhouse/clickhouse-server:latest
    depends_on:
      - clickhouse-keeper
    volumes:
      - ch01_data:/var/lib/clickhouse
      - ./backend/cluster-config.xml:/etc/clickhouse-server/config.d/cluster.xml
      - ./backend/macros-01.xml:/etc/clickhouse-server/config.d/macros.xml
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "8123:8123"
      - "9000:9000"

  clickhouse-02:
    image: clickhouse/clickhouse-server:latest
    depends_on:
      - clickhouse-keeper
    volumes:
      - ch02_data:/var/lib/clickhouse
      - ./backend/cluster-config.xml:/etc/clickhouse-server/config.d/cluster.xml
      - ./backend/macros-02.xml:/etc/clickhouse-server/config.d/macros.xml
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "8124:8123"
      - "9001:9000"
```

If `clickhouse-01` goes down, the backend can failover to `clickhouse-02` which has a full replica of the data.

---

## Complete Execution Plan — From Now to Working System

### Phase 1: Infrastructure (Person A) — Days 1-3

| # | Task | Details | Files |
|---|------|---------|-------|
| 1.1 | Update `init.sql` with revised schema | Add `app_name` column, switch to `ReplicatedMergeTree`, add `energy_app_ranking_mv` | `backend/init.sql` |
| 1.2 | Create ClickHouse cluster config files | `keeper-config.xml`, `cluster-config.xml`, `macros-01.xml`, `macros-02.xml` | `backend/*.xml` |
| 1.3 | Update `docker-compose.yml` | Add keeper + 2 ClickHouse nodes, update backend to connect to cluster | `docker-compose.yml` |
| 1.4 | Run `docker compose up` and verify | Confirm tables created on both nodes, replication works | — |
| 1.5 | Update `services/clickhouse.py` for failover | Try `clickhouse-01`, if down try `clickhouse-02` | `services/clickhouse.py` |

### Phase 2: Backend Core (Person A) — Days 3-6

| # | Task | Details | Files |
|---|------|---------|-------|
| 2.1 | Update `schemas.py` for `app_metrics` | Add `AppMetrics` model, update `MetricsPayload` to include `app_metrics` list | `models/schemas.py` |
| 2.2 | Update POST `/api/v1/metrics` | Unpack both `metrics` (app_name='system') and `app_metrics` (per-app rows) into ClickHouse | `routes/metrics.py` |
| 2.3 | Update GET `/api/v1/metrics` | Add `app_name` filter parameter | `routes/metrics.py` |
| 2.4 | Add GET `/api/v1/apps` endpoint | List all tracked applications per node with energy totals | `routes/apps.py` (new) |
| 2.5 | Add GET `/api/v1/apps/{app_name}/energy` | Per-app energy over time (uses `energy_app_ranking_mv`) | `routes/apps.py` |
| 2.6 | Test all endpoints with `curl` / Swagger | Verify POST with app_metrics, GET with app_name filter, apps endpoints | — |

### Phase 3: Auth + Heartbeat (Person A) — Days 6-8

| # | Task | Details | Files |
|---|------|---------|-------|
| 3.1 | Wire up API key auth middleware | Verify daemon API keys against `nodes` table on every POST | `auth/api_key.py` |
| 3.2 | Wire up JWT auth for dashboard | Login returns JWT, all GET endpoints require valid JWT | `auth/jwt_handler.py` |
| 3.3 | Integrate heartbeat into POST endpoint | Every successful POST calls `heartbeat_tracker.record()` | `routes/metrics.py` |
| 3.4 | Wire up node status into GET `/api/v1/nodes` | Return ONLINE/STALE/OFFLINE per node with adaptive timeout | `routes/nodes.py` |
| 3.5 | Wire up GET `/api/v1/summary` | System-wide stats: online/stale/offline counts, total power | `main.py` |

### Phase 4: Daemon — Per-App Energy (Person B) — Days 1-6

| # | Task | Details | Files |
|---|------|---------|-------|
| 4.1 | Create `app_energy.py` collector | Read `/proc/<pid>/stat` for CPU time, attribute RAPL energy proportionally | `collectors/app_energy.py` (new) |
| 4.2 | Process discovery + filtering | Enumerate running processes, filter by `top_n` or whitelist from config, ignore < min_cpu_percent | `collectors/app_energy.py` |
| 4.3 | Handle process name resolution | Map PID → friendly app name (strip path, merge child processes like `chrome` subprocesses) | `collectors/app_energy.py` |
| 4.4 | Update `daemon.py` main loop | Collect system metrics + per-app metrics, build combined payload with `app_metrics` array | `daemon.py` |
| 4.5 | Update `config.yaml` | Add `app_tracking` section with `mode`, `top_n`, `whitelist`, `min_cpu_percent` | `config.yaml` |
| 4.6 | Test daemon locally | Run daemon, verify it prints per-app energy data, verify JSON payload format is correct | — |
| 4.7 | Connect daemon to running backend | Register node, get API key, update config, run daemon, verify data appears in ClickHouse | — |

### Phase 5: Daemon — Buffer + Reliability (Person B) — Days 6-8

| # | Task | Details | Files |
|---|------|---------|-------|
| 5.1 | Test file-backed retry buffer | Kill backend, verify daemon buffers to disk, restart backend, verify flush | `buffer.py` |
| 5.2 | Test systemd service | Install service, verify auto-restart, verify survives reboot | `energy-daemon.service` |
| 5.3 | Edge case testing | Network timeout, backend overload, ClickHouse down (replication failover), malformed responses | — |

### Phase 6: Dashboard — Core Pages (Person C) — Days 1-8

| # | Task | Details | Files |
|---|------|---------|-------|
| 6.1 | `npm install` + verify React app starts | Install all deps, verify Tailwind works, verify routing works | — |
| 6.2 | Wire up API service to real backend | Update `api.js` base URL, test login flow, verify token management | `services/api.js` |
| 6.3 | Overview page with live data | Fetch real nodes, show NodeCards with status dots, show summary stats | `pages/Overview.jsx` |
| 6.4 | Realtime Monitor with live charts | Fetch raw metrics (last 15 min), auto-refresh every 5s, line charts for power + CPU | `pages/RealtimeMonitor.jsx` |
| 6.5 | Historical View with smart fetching | Time range picker, auto-select aggregation level, power + temperature charts | `pages/HistoricalView.jsx` |
| 6.6 | Node Detail page | All 8 KPIs for one node, time range selector, status indicator | `pages/NodeDetail.jsx` |

### Phase 7: Dashboard — Per-App Energy Views (Person C) — Days 8-11

| # | Task | Details | Files |
|---|------|---------|-------|
| 7.1 | Add `AppSelector` component | Dropdown listing all tracked applications for a node | `components/AppSelector.jsx` (new) |
| 7.2 | Add `AppEnergyBreakdown` component | Stacked bar chart or pie chart showing energy per app | `components/AppEnergyBreakdown.jsx` (new) |
| 7.3 | Add `AppEnergyTable` component | Table: app name, avg power, total energy, CPU%, ranked by consumption | `components/AppEnergyTable.jsx` (new) |
| 7.4 | Update NodeDetail page | Add per-app energy section below system KPIs | `pages/NodeDetail.jsx` |
| 7.5 | Add per-app filtering to Historical View | Select specific app to see its energy trend over time | `pages/HistoricalView.jsx` |
| 7.6 | Login page UI | Username/password form, token storage, redirect on auth failure | `pages/Login.jsx` (new) |

### Phase 8: Shell Benchmarking (Person B) — Days 8-11

| # | Task | Details | Files |
|---|------|---------|-------|
| 8.1 | Create shell collector scripts | Bash scripts reading same 8 KPIs: `cat /proc/stat`, `cat /proc/meminfo`, RAPL files, `/sys/class/thermal/` | `benchmarks/shell/collect.sh` |
| 8.2 | Create shell per-app energy script | Bash script reading `/proc/<pid>/stat` + RAPL, computing per-app attribution | `benchmarks/shell/app_energy.sh` |
| 8.3 | Create benchmark harness | Run Python collector N times + shell collector N times, measure: execution time, CPU overhead, memory overhead | `benchmarks/shell/compare.sh` |
| 8.4 | Run benchmarks on workstation + RPi | Compare Python vs shell overhead on both platforms, record results | `benchmarks/results/python_vs_shell.md` |
| 8.5 | Data generator: seed 24h of data | Run `data_generator.py` to fill 24h historical data for all 15 nodes (with per-app data) | — |
| 8.6 | Query benchmarks | Run `benchmark_runner.py`, measure latency for raw/aggregated/per-app queries | `benchmarks/results/query_benchmarks.md` |

### Phase 9: Integration + Polish — Days 11-14

| # | Task | Details | Owner |
|---|------|---------|-------|
| 9.1 | Full E2E test: daemon → backend → ClickHouse → dashboard | Start all services, run daemon, verify data appears on dashboard | All |
| 9.2 | Replication failover test | Kill clickhouse-01, verify backend failovers to clickhouse-02, verify no data loss | A |
| 9.3 | Buffer resilience test | Kill backend for 5 min while daemon runs, restart, verify buffered data flushes | B |
| 9.4 | Dashboard error states | Loading spinners, empty states, offline indicators, connection error messages | C |
| 9.5 | Input validation hardening | All spec rules: no future timestamps, cpu/ram 0-100, node must exist, duplicate rejection | A |
| 9.6 | Dashboard Dockerfile + nginx | Build production React bundle, serve via nginx, test in Docker | C |
| 9.7 | Final Docker Compose deployment | `docker compose up` starts everything, healthchecks pass, dashboard accessible | A |
| 9.8 | Performance evaluation report | Write up: write throughput, query latency, Python vs shell overhead, replication impact | B |
| 9.9 | API documentation | Ensure Swagger/OpenAPI docs are complete and accurate at `/docs` | A |
| 9.10 | Demo preparation | Screenshots, test data loaded, talking points for each feature | C |

---

## Timeline View (14 Working Days)

```
         Day 1   2   3   4   5   6   7   8   9  10  11  12  13  14
         ─────────────────────────────────────────────────────────────
Person A │██ Phase 1: Infra ██│██ Phase 2: Backend ██│Ph3│ Phase 9  │
         │ CH cluster, schema │ API endpoints, apps  │HA │ Validate │
         │ replication, docker│ per-app support      │JWT│ Deploy   │
         ─────────────────────────────────────────────────────────────
Person B │████ Phase 4: Daemon █████████│Ph5 │███ Phase 8: Shell ███│
         │ per-app energy collector     │Buff│ benchmarks, compare  │
         │ RAPL, /proc, process disc.   │Test│ perf report          │
         ─────────────────────────────────────────────────────────────
Person C │████ Phase 6: Dashboard Core ████████│██ Phase 7: App UI █│
         │ Overview, Realtime, Historical,     │ per-app energy      │
         │ NodeDetail, live data wiring        │ breakdown, polish   │
         ─────────────────────────────────────────────────────────────
```

---

## Dependency Map

```
Phase 1 (A: Infra)
  ├──→ Phase 2 (A: Backend)  ──→ Phase 3 (A: Auth/HB)
  │         │                          │
  │         ▼                          ▼
  │    Phase 4 (B: Daemon) ──→ Phase 5 (B: Buffer tests)
  │         │                          │
  │         ▼                          ▼
  │    Phase 6 (C: Dashboard) ──→ Phase 7 (C: App UI)
  │                                    │
  └──→ Phase 8 (B: Shell bench) ───────┤
                                       ▼
                                 Phase 9 (All: Integration)
```

**Critical path:** Phase 1 → Phase 2 → Phase 4.7 (daemon connects to backend)

- B can start Phase 4 (daemon collectors) in parallel with A's Phase 1, but **4.7** (connecting to backend) requires Phase 2 done
- C can start Phase 6 (dashboard UI) in parallel, but **6.3+** (live data) requires Phase 2 done
- Phase 8 (shell benchmarks) is independent and can run anytime after Phase 4

---

## Files That Need to Be Created or Modified

### New files to create
| File | Owner | Phase |
|------|-------|-------|
| `daemon/collectors/app_energy.py` | B | 4 |
| `backend/app/routes/apps.py` | A | 2 |
| `backend/keeper-config.xml` | A | 1 |
| `backend/cluster-config.xml` | A | 1 |
| `backend/macros-01.xml` | A | 1 |
| `backend/macros-02.xml` | A | 1 |
| `dashboard/src/components/AppSelector.jsx` | C | 7 |
| `dashboard/src/components/AppEnergyBreakdown.jsx` | C | 7 |
| `dashboard/src/components/AppEnergyTable.jsx` | C | 7 |
| `dashboard/src/pages/Login.jsx` | C | 7 |
| `benchmarks/shell/collect.sh` | B | 8 |
| `benchmarks/shell/app_energy.sh` | B | 8 |
| `benchmarks/shell/compare.sh` | B | 8 |

### Existing files to modify
| File | Change | Owner | Phase |
|------|--------|-------|-------|
| `backend/init.sql` | Add `app_name` column, switch to `ReplicatedMergeTree` | A | 1 |
| `docker-compose.yml` | Add keeper + 2 CH nodes | A | 1 |
| `backend/app/models/schemas.py` | Add `AppMetrics` model, update `MetricsPayload` | A | 2 |
| `backend/app/routes/metrics.py` | Handle `app_metrics` in POST, add `app_name` filter to GET | A | 2 |
| `backend/app/services/clickhouse.py` | Failover logic, per-app queries, insert app_metrics rows | A | 1+2 |
| `daemon/daemon.py` | Integrate per-app collection into main loop | B | 4 |
| `daemon/config.yaml` | Add `app_tracking` section | B | 4 |
| `dashboard/src/pages/NodeDetail.jsx` | Add per-app energy section | C | 7 |
| `dashboard/src/pages/HistoricalView.jsx` | Add app filter | C | 7 |
| `dashboard/src/services/api.js` | Add apps endpoints | C | 7 |
| `benchmarks/data_generator.py` | Generate per-app fake data | B | 8 |

---

## Deliverables Checklist

By the end of this plan, we should have:

- [ ] ClickHouse cluster with 2 replicated nodes (failover tested)
- [ ] Backend API with all endpoints working (metrics, nodes, apps, auth, summary)
- [ ] Per-application energy tracking (RAPL-based, top N or whitelist)
- [ ] Application names displayed in dashboard
- [ ] Daemon collecting and sending 8 system KPIs + per-app energy
- [ ] File-backed retry buffer tested under network failure
- [ ] Dashboard with 4 pages + per-app energy breakdown
- [ ] Smart data fetching (auto-aggregation by time range)
- [ ] Adaptive heartbeat (ONLINE/STALE/OFFLINE/UNKNOWN)
- [ ] JWT auth for dashboard, API key auth for daemons
- [ ] Shell benchmark scripts for Python vs shell overhead comparison
- [ ] Performance evaluation report (write/query latency, overhead)
- [ ] Full Docker Compose deployment (`docker compose up` and everything works)
- [ ] Swagger API docs at `/docs`
