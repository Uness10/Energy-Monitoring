# Project Requirements Specification

---

## 1. Functional Requirements

### A. Data Collection

The system must collect KPIs from 15 MLab nodes (workstations, Raspberry Pis, and mobile devices).

**Required KPIs per node:**
- Voltage
- CPU frequency
- CPU utilization (%)
- RAM utilization (%)
- Temperature
- Power consumption (W)
- Energy consumption (Wh)
- Node uptime

**Record format:**
- `node_id`
- `timestamp`
- `metric`
- `value`

Data transmission: Every 5–10 seconds

---

### B. Backend System

**API:**
- REST or gRPC
- Endpoint to receive KPIs
- Endpoint to query historical data
- Endpoint for aggregated data

**Authentication:**
- Node authentication (API key or token)
- Dashboard user authentication

**Data Validation:**
- Schema validation
- Timestamp validation
- Duplicate handling

**Aggregation:**
- Time-window aggregation (1min, 5min, 1h)
- Statistical functions (average, max, min)
- Daily energy per node

---

### C. Database

**Requirements:**
- Handle time-series data efficiently
- Support timestamp indexing
- Support aggregation queries

**Evaluation criteria:**
- Write throughput
- Query latency (time-range queries)
- Storage efficiency
- Aggregation performance
- Scalability

**Benchmarked DBs:** PostgreSQL, ClickHouse, InfluxDB, TimescaleDB, OpenTSDB, Druid 
---

### D. Web Dashboard

**Real-time view:**
- Current power per node
- Live CPU/RAM usage

**Historical analytics:**
- Power trends over time
- Daily energy consumption
- Temperature trends
- Node comparison

**Filtering options:**
- By node, time range, and KPI type

**Performance optimization:**
- Downsampling
- Pre-aggregated tables
- Pagination
- Time window limits

---

## 2. Non-Functional Requirements

- **Scalability:** Support increasing node count
- **Reliability:** Daemon retry logic and data buffering
- **Performance:** API response < 500ms
- **Security:** HTTPS, authentication, input sanitization

---

## 3. System Architecture

```
[ Node Daemon ] → [ Backend API ] → [ Time-Series DB ]
                                  ↓
                             [ Web Dashboard ]
```

Components must be independently deployable.

---

## 4. Deliverables

- Backend source code
- Frontend dashboard
- Node daemon
- Database benchmark report
- Architecture documentation
- Performance evaluation

---

## 5. Key Technical Challenge

Efficiently handling and visualizing large time-series data without overwhelming the database or dashboard.

