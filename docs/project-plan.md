# Energy Monitoring System — Project Plan & Task Breakdown

## Team Roles (from spec)
| Person | Role             | Domain                                         |
|--------|------------------|-------------------------------------------------|
| **A**  | Data Engineer    | ClickHouse, Backend API, Docker, Auth, Security |
| **B**  | The Collector    | Daemon, Mobile app, Benchmarks, Performance     |
| **C**  | The Visualizer   | Dashboard, Integration testing, UI polish       |

---

## Timeline Overview (4 Weeks)

```
Week 1  ──────────────────────────────────────────────────
  A: ClickHouse schema + Backend core API (POST/GET metrics)
  B: Daemon collectors + main loop + config
  C: React project setup + Overview page + components

Week 2  ──────────────────────────────────────────────────
  A: Auth system (API key + JWT) + Heartbeat service + Nodes endpoints
  B: Retry buffer + systemd service + connect daemon → backend
  C: Realtime page + KpiChart + StatusIndicator + API service layer

Week 3  ──────────────────────────────────────────────────
  A: Aggregation endpoints + Summary endpoint + Docker Compose polish
  B: Mobile app (Flutter/RN) + Data generator for testing
  C: Historical view + smart data fetching + NodeDetail page

Week 4  ──────────────────────────────────────────────────
  A: Validation hardening + deployment + docs
  B: Benchmark runner + performance evaluation report
  C: Integration testing + UI polish + final fixes
```

---

## Detailed Task Breakdown

### WEEK 1 — Foundation (All 3 work in parallel, no cross-dependencies)

#### Person A — Data Engineer
| #  | Task                                      | Output Files                              | Days  |
|----|-------------------------------------------|-------------------------------------------|-------|
| A1 | Verify & run ClickHouse schema (init.sql) | `backend/init.sql`                        | Day 1 |
| A2 | ClickHouse service (connection, insert, raw query) | `services/clickhouse.py`          | Day 1-2 |
| A3 | POST /api/v1/metrics endpoint             | `routes/metrics.py`                       | Day 2-3 |
| A4 | GET /api/v1/metrics endpoint (raw query)  | `routes/metrics.py`                       | Day 3-4 |
| A5 | Backend Dockerfile + test with Docker Compose | `backend/Dockerfile`, `docker-compose.yml` | Day 4-5 |

#### Person B — The Collector
| #  | Task                                      | Output Files                              | Days  |
|----|-------------------------------------------|-------------------------------------------|-------|
| B1 | CPU collector (freq + utilization)        | `collectors/cpu.py`                       | Day 1 |
| B2 | Memory + Temperature + Uptime collectors  | `collectors/memory.py`, `temperature.py`, `uptime.py` | Day 1-2 |
| B3 | Power + Voltage + Energy collectors       | `collectors/power.py`                     | Day 2-3 |
| B4 | Main daemon loop + config.yaml loading    | `daemon.py`, `config.yaml`                | Day 3-4 |
| B5 | Test daemon locally (print metrics)       | —                                         | Day 4-5 |

#### Person C — The Visualizer
| #  | Task                                      | Output Files                              | Days  |
|----|-------------------------------------------|-------------------------------------------|-------|
| C1 | React project init + Tailwind + Router    | `package.json`, `App.jsx`, `index.js`, `index.css` | Day 1 |
| C2 | API service layer + auth service          | `services/api.js`, `services/auth.js`     | Day 1-2 |
| C3 | StatusIndicator + NodeCard components     | `components/StatusIndicator.jsx`, `NodeCard.jsx` | Day 2-3 |
| C4 | Overview page (node grid + summary stats) | `pages/Overview.jsx`                      | Day 3-4 |
| C5 | NodeSelector + TimeRangePicker components | `components/NodeSelector.jsx`, `TimeRangePicker.jsx` | Day 4-5 |

> **Week 1 sync point:** By end of Week 1, A has a working backend that accepts POST metrics and returns GET queries. B has a daemon that collects all 8 KPIs. C has a dashboard shell with the overview page mocked out. **No cross-dependencies yet.**

---

### WEEK 2 — Connect the Pieces (Dependencies start here)

#### Person A — Data Engineer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| A6 | API key auth middleware for daemons       | A3         | Day 1 |
| A7 | JWT auth for dashboard (login/register)   | —          | Day 1-2 |
| A8 | Heartbeat service (adaptive timeout)      | A3         | Day 2-3 |
| A9 | GET /api/v1/nodes + /nodes/{id}/status    | A8         | Day 3-4 |
| A10 | Node registration endpoint + API key generation | A6   | Day 4-5 |

#### Person B — The Collector
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| B6 | Retry buffer (file-backed deque)          | B4         | Day 1-2 |
| B7 | HTTP sending logic (POST to backend)      | **A3, A6** | Day 2-3 |
| B8 | Buffer flush logic (periodic retry)       | B6, B7     | Day 3-4 |
| B9 | systemd service file + install script     | B4         | Day 4 |
| B10 | End-to-end test: daemon → backend → ClickHouse | **A5** | Day 4-5 |

#### Person C — The Visualizer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| C6 | useNodeStatus hook (polling nodes)        | **A9**     | Day 2-3 |
| C7 | useMetrics hook (fetch with caching)      | **A4**     | Day 2-3 |
| C8 | Realtime Monitor page (live line charts)  | C7         | Day 3-4 |
| C9 | KpiChart component (Recharts integration) | —          | Day 1-2 |
| C10 | Login page + token management            | **A7**     | Day 4-5 |

> **Week 2 sync point:** B needs A's POST endpoint + API key auth before sending real data (B7 depends on A3+A6). C needs A's nodes/metrics endpoints before hooking up real data (C6 depends on A9, C7 depends on A4). **A is the critical path — A must finish A3+A6 by mid-week so B and C can integrate.**

---

### WEEK 3 — Advanced Features (More parallel work)

#### Person A — Data Engineer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| A11 | Aggregation logic (smart level selection) | A4        | Day 1-2 |
| A12 | GET /api/v1/metrics/aggregated endpoint   | A11        | Day 2-3 |
| A13 | GET /api/v1/summary endpoint              | A8, A9     | Day 3 |
| A14 | Docker Compose final polish (env vars, healthchecks, volumes) | A5 | Day 3-4 |
| A15 | Input validation hardening (all rules from spec) | A3 | Day 4-5 |

#### Person B — The Collector
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| B11 | Mobile app project setup (Flutter/RN)    | —          | Day 1 |
| B12 | Mobile KPI collection (battery, network)  | B11        | Day 1-3 |
| B13 | Mobile data sending to backend            | B11, **A6** | Day 3-4 |
| B14 | Data generator script (fake 15 nodes)     | **A3**     | Day 4 |
| B15 | Seed test data (24h historical fill)      | B14        | Day 4-5 |

#### Person C — The Visualizer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| C11 | Historical View page + time range picker  | **A12**    | Day 1-3 |
| C12 | Smart data fetching (aggregation by range)| C11, **A11** | Day 2-3 |
| C13 | NodeDetail page (all 8 KPIs for one node) | C7, C9     | Day 3-4 |
| C14 | Dashboard Dockerfile + nginx config       | —          | Day 4 |
| C15 | Responsive layout + mobile-friendly       | C4, C8     | Day 4-5 |

> **Week 3 sync point:** A delivers the aggregation endpoint early so C can build smart data fetching. B generates test data so C has something to visualize. **B15 → C can see real charts.**

---

### WEEK 4 — Polish, Test, Deploy

#### Person A — Data Engineer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| A16 | Duplicate detection on metrics ingest     | A3         | Day 1 |
| A17 | Rate limiting / error responses           | —          | Day 1-2 |
| A18 | Full Docker deployment test (compose up)  | A14        | Day 2-3 |
| A19 | API documentation (OpenAPI / docs page)   | All A*     | Day 3-4 |
| A20 | Architecture doc + deployment guide       | All A*     | Day 4-5 |

#### Person B — The Collector
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| B16 | Benchmark runner script                   | B14, **A3** | Day 1-2 |
| B17 | Run benchmarks (write throughput, query latency) | B16 | Day 2-3 |
| B18 | Performance evaluation report             | B17        | Day 3-4 |
| B19 | Mobile app viewer (display own metrics)   | B12, B13   | Day 3-4 |
| B20 | Daemon edge cases (network loss, reboot)  | B8         | Day 4-5 |

#### Person C — The Visualizer
| #  | Task                                      | Depends On | Days  |
|----|-------------------------------------------|------------|-------|
| C16 | Integration testing (full flow E2E)       | **A18**    | Day 2-3 |
| C17 | Error states (loading, empty, offline)    | C8, C11    | Day 1-2 |
| C18 | UI polish (colors, spacing, animations)   | All C*     | Day 3-4 |
| C19 | Cross-browser testing + fixes             | C18        | Day 4 |
| C20 | Final demo prep + screenshots             | All        | Day 5 |

---

## Dependency Graph (Critical Path)

```
A1 → A2 → A3 ──→ A4 ──→ A11 → A12
              │               ↓
              ├→ A6 ──→ B7    C11 → C12
              │    ↓
              │   A10
              │
              └→ A8 → A9 ──→ C6
                        ↓
                       A13

B1 → B4 → B6 → B7 → B8 → B10
                 ↑
                A3+A6

C1 → C9 → C8
C2 → C7 → C8, C13
C3 → C4
```

**Critical path:** A1 → A2 → A3 → A6 → B7 → B10 (daemon can't send real data until A has auth ready)

---

## Weekly Sync Meetings
- **Monday**: 15-min standup — what's planned this week, any blockers
- **Wednesday**: Mid-week check — are cross-dependencies unblocked?
- **Friday**: Demo — each person shows what they built this week

## Key Milestones
| Date       | Milestone                                    |
|------------|----------------------------------------------|
| End Week 1 | Backend accepts data, daemon collects, dashboard renders |
| End Week 2 | Full pipeline working: daemon → backend → dashboard |
| End Week 3 | All pages, mobile app, historical analytics working |
| End Week 4 | Deployed, tested, benchmarked, documented     |
