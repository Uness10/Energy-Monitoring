#!/usr/bin/env python3
"""Generate fake KPI data for testing and benchmarking."""

import random
import time
import httpx
from datetime import datetime, timezone, timedelta

BACKEND_URL = "http://localhost:8000/api/v1/metrics"

NODES = [f"workstation-{i:02d}" for i in range(1, 11)]
NODES += [f"rpi-{i:02d}" for i in range(1, 4)]
NODES += ["mobile-01", "mobile-02"]

API_KEY = "sk-test-key-for-benchmarking"


def generate_metrics() -> dict:
    return {
        "voltage": round(random.uniform(210, 230), 1),
        "cpu_freq": round(random.uniform(800, 4500), 0),
        "cpu_util": round(random.uniform(0, 100), 1),
        "ram_util": round(random.uniform(20, 95), 1),
        "temperature": round(random.uniform(30, 90), 1),
        "power_w": round(random.uniform(20, 300), 1),
        "energy_wh": round(random.uniform(0, 5000), 1),
        "uptime_s": round(random.uniform(0, 864000), 0),
    }


def generate_batch(node_id: str, timestamp: datetime) -> dict:
    return {
        "node_id": node_id,
        "timestamp": timestamp.isoformat(),
        "metrics": generate_metrics(),
    }


def fill_historical(hours: int = 24, interval_seconds: int = 10):
    """Generate historical data for all nodes."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)
    total = int(hours * 3600 / interval_seconds) * len(NODES)
    sent = 0

    print(f"Generating {total} records ({hours}h, {len(NODES)} nodes)...")

    with httpx.Client() as client:
        t = start
        while t <= now:
            for node_id in NODES:
                payload = generate_batch(node_id, t)
                try:
                    client.post(
                        BACKEND_URL,
                        json=payload,
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        timeout=5.0,
                    )
                    sent += 1
                except Exception as e:
                    print(f"Error: {e}")

                if sent % 1000 == 0:
                    print(f"  Sent {sent}/{total} records...")
            t += timedelta(seconds=interval_seconds)

    print(f"Done. Sent {sent} records.")


def stream_realtime(interval: float = 10.0):
    """Continuously send real-time fake data."""
    print(f"Streaming data for {len(NODES)} nodes every {interval}s...")
    with httpx.Client() as client:
        while True:
            now = datetime.now(timezone.utc)
            for node_id in NODES:
                payload = generate_batch(node_id, now)
                try:
                    client.post(
                        BACKEND_URL,
                        json=payload,
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        timeout=5.0,
                    )
                except Exception as e:
                    print(f"Error sending to {node_id}: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stream":
        stream_realtime()
    else:
        fill_historical()
