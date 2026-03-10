#!/usr/bin/env python3
"""Benchmark ClickHouse query performance and write throughput."""

import time
import httpx
from datetime import datetime, timezone, timedelta

BACKEND_URL = "http://localhost:8000/api/v1"
TOKEN = ""  # Set after login


def login():
    global TOKEN
    resp = httpx.post(f"{BACKEND_URL}/auth/login", json={"username": "admin", "password": "admin"})
    TOKEN = resp.json()["access_token"]


def bench_query(label, params):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    times = []
    for _ in range(10):
        start = time.perf_counter()
        resp = httpx.get(f"{BACKEND_URL}/metrics", params=params, headers=headers, timeout=30)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert resp.status_code == 200, f"Got {resp.status_code}"

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(0.95 * len(times))]
    print(f"{label:40s}  avg={avg:7.1f}ms  p95={p95:7.1f}ms  points={resp.json().get('count', '?')}")


def run():
    login()
    now = datetime.now(timezone.utc)

    print("=== Query Benchmarks (10 iterations each) ===\n")

    bench_query("Raw 15min single node", {
        "node_id": "workstation-01", "metric": "power_w",
        "start": (now - timedelta(minutes=15)).isoformat(),
        "end": now.isoformat(),
    })
    bench_query("Raw 15min all nodes", {
        "metric": "power_w",
        "start": (now - timedelta(minutes=15)).isoformat(),
        "end": now.isoformat(),
    })
    bench_query("Aggregated 24h single node", {
        "node_id": "workstation-01", "metric": "power_w",
        "start": (now - timedelta(hours=24)).isoformat(),
        "end": now.isoformat(),
    })
    bench_query("Aggregated 7d all nodes", {
        "metric": "cpu_util",
        "start": (now - timedelta(days=7)).isoformat(),
        "end": now.isoformat(),
    })


if __name__ == "__main__":
    run()
