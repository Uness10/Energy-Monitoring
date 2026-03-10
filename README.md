<div align="center">

# Energy Monitoring System

**A distributed real-time energy monitoring framework for heterogeneous compute nodes**

Built for the MLab research environment — tracking power, performance, and health across workstations, Raspberry Pis, and mobile devices.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-OLAP-FFCC00?logo=clickhouse&logoColor=black)](https://clickhouse.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API Reference](#api-reference) · [Dashboard](#dashboard) · [Contributing](#contributing)

</div>

---

## Why This Exists

Research labs consume significant energy, but most teams have **zero visibility** into where the watts go. Which workstation is burning 300W idle? Is that Raspberry Pi cluster efficient? How does GPU training affect power draw over time?

This system answers those questions by collecting **8 key performance indicators** from every node in the lab, every 5-10 seconds, and presenting them through a real-time dashboard with historical analytics.

## Features

- **8 KPIs per node** — Voltage, CPU frequency, CPU utilization, RAM utilization, temperature, power consumption, energy consumption, and uptime
- **Adaptive heartbeat detection** — Each node gets a dynamic timeout based on its actual behavior pattern (not a fixed threshold), using statistical analysis of inter-arrival times
- **Sub-second query performance** — ClickHouse column-oriented storage with materialized views for pre-aggregated hourly and daily summaries
- **Smart data fetching** — Dashboard automatically selects the right aggregation level (raw/1min/5min/1h) based on the requested time range, never exceeding ~2,000 data points per chart
- **Resilient data collection** — File-backed retry buffer in the daemon ensures no data loss during network outages
- **Multi-platform support** — Workstations (RAPL), Raspberry Pi (INA219/thermal), and mobile devices (Flutter/React Native)

## Architecture

```
                    ┌─────────────────┐
                    │   Web Dashboard │  React 18 + Tailwind + Recharts
                    │   (port 3000)   │  Smart data fetching + React Query
                    └────────┬────────┘
                             │ GET /api/v1/*
                             ▼
┌──────────┐  POST   ┌─────────────────┐        ┌──────────────────┐
│Workstation├────────►│  Backend API    │───────►│    ClickHouse    │
│  Daemon   │        │  (FastAPI)      │        │  (OLAP Database) │
└──────────┘        │  (port 8000)    │        │  (port 8123)     │
┌──────────┐  POST   │                 │        │                  │
│Raspberry ├────────►│  • Auth (JWT +  │        │  • energy_metrics│
│ Pi Daemon │        │    API Keys)   │        │  • hourly MV     │
└──────────┘        │  • Heartbeat   │        │  • daily MV      │
┌──────────┐  POST   │  • Aggregation │        │  • nodes         │
│Mobile App├────────►│  • Validation  │        │                  │
└──────────┘        └─────────────────┘        └──────────────────┘
```

## KPIs Collected

| KPI | Unit | Collection Method |
|-----|------|-------------------|
| Voltage | V | RAPL / INA219 / nominal |
| CPU Frequency | MHz | `psutil.cpu_freq()` |
| CPU Utilization | % | `psutil.cpu_percent()` |
| RAM Utilization | % | `psutil.virtual_memory()` |
| Temperature | °C | `sensors_temperatures()` / `/sys/class/thermal/` |
| Power Consumption | W | RAPL / INA219 / estimation |
| Energy Consumption | Wh | Cumulative from power readings |
| Node Uptime | seconds | `psutil.boot_time()` |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for daemon)
- Node.js 18+ (for dashboard development)

### 1. Clone and Launch

```bash
git clone https://github.com/Uness10/Energy-Monitoring.git
cd Energy-Monitoring

# Start all services (ClickHouse + Backend + Dashboard)
docker compose up -d
```

This starts:
- **ClickHouse** on `localhost:8123` (HTTP) and `localhost:9000` (native)
- **Backend API** on `localhost:8000` (with Swagger docs at `/docs`)
- **Dashboard** on `localhost:3000`

### 2. Create a Dashboard User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin", "role": "admin"}'
```

### 3. Register a Node

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')

# Register a node (returns an API key)
curl -X POST http://localhost:8000/api/v1/nodes/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "workstation-01", "node_type": "workstation", "description": "Lab PC #1"}'
```

### 4. Start the Daemon

```bash
cd daemon

# Edit config with your node's API key
vim config.yaml

# Install dependencies and run
pip install -r requirements.txt
python daemon.py
```

### 5. Generate Test Data (Optional)

```bash
cd benchmarks
pip install httpx

# Fill 24 hours of fake data for 15 nodes
python data_generator.py

# Or stream real-time fake data
python data_generator.py stream
```

## API Reference

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| `POST` | `/api/v1/metrics` | Receive KPI batch from node | API Key |
| `GET` | `/api/v1/metrics` | Query raw metrics (with filters) | JWT |
| `GET` | `/api/v1/metrics/aggregated` | Get pre-aggregated data | JWT |
| `GET` | `/api/v1/nodes` | List all nodes + live status | JWT |
| `GET` | `/api/v1/nodes/{id}/status` | Single node detail | JWT |
| `GET` | `/api/v1/summary` | System-wide summary | JWT |
| `POST` | `/api/v1/auth/login` | Dashboard user login | None |
| `POST` | `/api/v1/auth/register` | Register dashboard user | Admin |

### Example: Send Metrics from a Daemon

```json
POST /api/v1/metrics
Authorization: Bearer <node-api-key>

{
  "node_id": "workstation-01",
  "timestamp": "2026-03-02T10:30:00.000Z",
  "metrics": {
    "voltage": 220.5,
    "cpu_freq": 3200.0,
    "cpu_util": 45.2,
    "ram_util": 62.8,
    "temperature": 58.3,
    "power_w": 85.4,
    "energy_wh": 1024.7,
    "uptime_s": 86400
  }
}
```

Full interactive API docs available at `http://localhost:8000/docs` when the backend is running.

## Dashboard

The web dashboard provides four views:

| Page | Description |
|------|-------------|
| **Overview** | Grid of all 15 nodes showing live status (green/yellow/red), current power draw, CPU%, and system-wide totals |
| **Realtime** | Live-updating line charts (5-10s refresh) for power and CPU/RAM over the last 15 minutes |
| **Historical** | Time-range selectable analytics with automatic downsampling — power trends, temperature, daily energy bars |
| **Node Detail** | Deep dive into a single node with all 8 KPIs, full history, and uptime timeline |

### Smart Data Fetching

The dashboard never fetches more data than needed:

| Time Range | Aggregation | Max Points |
|------------|-------------|------------|
| Last 15 min | Raw (5-10s) | ~180 |
| Last 1 hour | 1-minute avg | 60 |
| Last 24 hours | 5-minute avg | 288 |
| Last 7 days | 1-hour avg | 168 |
| Last 30 days | 1-hour avg | 720 |

## Adaptive Heartbeat

Instead of fixed timeouts, each node gets a **dynamic timeout** learned from its own behavior:

```
T_timeout = μ + 4σ
```

Where **μ** is the mean inter-arrival time and **σ** is the standard deviation, computed over a sliding window of the last 100 transmissions. This means:

- A node sending every **5s** gets a ~7s timeout (detects failures fast)
- A node sending every **10s** with jitter gets a ~14s timeout (no false alarms)
- New nodes use a **30s fallback** until 5 samples are collected

| Status | Condition | Color |
|--------|-----------|-------|
| ONLINE | age < timeout | Green |
| STALE | timeout < age < 2 × timeout | Yellow |
| OFFLINE | age > 2 × timeout | Red |
| UNKNOWN | No data ever received | Gray |

## Project Structure

```
Energy-Monitoring/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entry point + CORS + routes
│   │   ├── config.py           # Settings (env-based)
│   │   ├── models/schemas.py   # Pydantic validation models
│   │   ├── routes/             # API endpoints
│   │   │   ├── metrics.py      # POST/GET /api/v1/metrics
│   │   │   ├── nodes.py        # GET /api/v1/nodes
│   │   │   └── auth.py         # POST /api/v1/auth/*
│   │   ├── services/           # Business logic
│   │   │   ├── clickhouse.py   # DB connection + queries
│   │   │   ├── heartbeat.py    # Adaptive timeout tracker
│   │   │   └── aggregation.py  # Smart aggregation levels
│   │   └── auth/               # Security
│   │       ├── jwt_handler.py  # JWT create/verify
│   │       └── api_key.py      # Node API key validation
│   ├── init.sql                # ClickHouse schema
│   ├── requirements.txt
│   └── Dockerfile
├── daemon/                     # Node data collector
│   ├── daemon.py               # Main loop
│   ├── collectors/             # KPI collection modules
│   │   ├── cpu.py              # CPU freq + utilization
│   │   ├── memory.py           # RAM utilization
│   │   ├── temperature.py      # CPU/system temperature
│   │   ├── power.py            # Power + energy + voltage
│   │   └── uptime.py           # System uptime
│   ├── buffer.py               # File-backed retry buffer
│   ├── config.yaml             # Node configuration
│   ├── requirements.txt
│   └── energy-daemon.service   # systemd unit file
├── dashboard/                  # React web dashboard
│   ├── src/
│   │   ├── App.jsx             # Router + navigation
│   │   ├── pages/              # Overview, Realtime, Historical, NodeDetail
│   │   ├── components/         # NodeCard, KpiChart, StatusIndicator, etc.
│   │   ├── services/           # API client + auth
│   │   └── hooks/              # useNodeStatus, useMetrics
│   ├── package.json
│   └── Dockerfile
├── benchmarks/                 # Testing & performance
│   ├── data_generator.py       # Fake data for 15 nodes
│   └── benchmark_runner.py     # Query latency benchmarks
├── docs/                       # Documentation
│   └── project-plan.md         # Team task breakdown & timeline
└── docker-compose.yml          # Full stack deployment
```

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Database | ClickHouse | 6x faster writes than PostgreSQL, all queries <302ms ([benchmark](docs/benchmark-report.md)) |
| Backend | Python + FastAPI | Async, auto-generated docs, Pydantic validation |
| Dashboard | React 18 + Recharts + Tailwind | Component-based, performant charts, utility-first CSS |
| Data fetching | React Query v5 | Caching, background refetch, stale-while-revalidate |
| Daemon | Python + psutil | Cross-platform KPI collection |
| Auth | JWT + API Keys | JWT for dashboard users, API keys for daemon nodes |
| Deployment | Docker Compose | Single command to launch the full stack |

## Database Design

ClickHouse was chosen based on the [SciTS benchmark](docs/benchmark-report.md) for time-series workloads:

- **`energy_metrics`** — Main table, one row per metric per timestamp. Partitioned by day, sorted by `(node_id, metric, timestamp)`. 1-year TTL.
- **`energy_hourly_mv`** — Materialized view with hourly avg/min/max per node per metric. Auto-populated on insert.
- **`energy_daily_mv`** — Materialized view with daily power and temperature summaries.
- **`nodes`** — Registry of all nodes with API keys and metadata.

`LowCardinality(String)` provides dictionary compression for the 120 unique node/metric combinations (15 nodes x 8 KPIs).

## Contributing

This project is maintained by a team of three:

| Role | Responsibility |
|------|---------------|
| **Data Engineer** | ClickHouse, Backend API, Auth, Docker deployment |
| **The Collector** | Node daemon, Mobile app, Performance benchmarks |
| **The Visualizer** | Web dashboard, Integration testing, UI polish |

See [docs/project-plan.md](docs/project-plan.md) for the full task breakdown and timeline.

## License

MIT
