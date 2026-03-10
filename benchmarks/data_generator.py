#!/usr/bin/env python3
"""
Generate fake KPI data for testing and benchmarking.
Produces both system-level metrics AND per-application energy data.
"""

import random
import time
import httpx
from datetime import datetime, timezone, timedelta

BACKEND_URL = "http://localhost:8000/api/v1/metrics"

NODES = [f"workstation-{i:02d}" for i in range(1, 11)]
NODES += [f"rpi-{i:02d}" for i in range(1, 4)]
NODES += ["mobile-01", "mobile-02"]

# Typical lab applications
APPS = ["firefox", "python3", "gcc", "matlab", "code", "jupyter",
        "chrome", "java", "docker", "git"]

# Per-node API keys (auto-populated from ClickHouse at registration time)
NODE_KEYS = {
    "mobile-01":      "sk-36d059de079be093343096e3f9cf8d430f4fb95d",
    "mobile-02":      "sk-084d5ce43a6fecf6e59973e74907536a05e7dbd8",
    "rpi-01":         "sk-9990ba263c54e3bc7664791390b3fdf914b9ad09",
    "rpi-02":         "sk-258b4de55e9345cab37f67f8dfd8742b732e2ec5",
    "rpi-03":         "sk-eefb663d5856ed50fe79ffd55975d7cc4c2b40cb",
    "workstation-01": "sk-6041dc92685a16bf229494b8e0c8601542f868ac",
    "workstation-02": "sk-b968e3b9630edde5435a5b2252f6a05aeb1dca12",
    "workstation-03": "sk-98dbd8cee0adac0779e9e2338ce8cc75e30bbd2d",
    "workstation-04": "sk-de56826037cfded321af17212a63caf06ad85873",
    "workstation-05": "sk-3d8fec23383e6618f2f4a340ffed7cf141879792",
    "workstation-06": "sk-60d3f5f73791ba84bf68e594acbbecf427f89dea",
    "workstation-07": "sk-30225b130b8fc34daf18a57c66289edb482cf47c",
    "workstation-08": "sk-0c7b522d9397ee8819933a4add31c33728f13841",
    "workstation-09": "sk-e9ab5a0763a12bb8427e04ea7910f1f53f3b7f71",
    "workstation-10": "sk-8c08ec52f75599df90bd70f9705ad76e0feff197",
}


def generate_system_metrics() -> dict:
    cpu = random.uniform(5, 90)
    power = 30 + (120 * cpu / 100) + random.uniform(-5, 5)
    return {
        "voltage":     round(random.uniform(218, 222), 1),
        "cpu_freq":    round(random.uniform(800, 4500), 0),
        "cpu_util":    round(cpu, 1),
        "ram_util":    round(random.uniform(20, 85), 1),
        "temperature": round(random.uniform(35, 85), 1),
        "power_w":     round(power, 1),
        "energy_wh":   round(random.uniform(0, 5000), 1),
        "uptime_s":    round(random.uniform(0, 864000), 0),
    }


def generate_app_metrics(system_power: float) -> list:
    """Generate per-app energy data proportional to system power."""
    num_apps = random.randint(2, 5)
    apps = random.sample(APPS, num_apps)
    shares = [random.random() for _ in apps]
    total = sum(shares)
    # Apps consume ~60-80% of system power total
    app_power_budget = system_power * random.uniform(0.6, 0.8)
    result = []
    for app, share in zip(apps, shares):
        power = (share / total) * app_power_budget
        cpu_pct = random.uniform(1, 40)
        result.append({
            "app_name":   app,
            "pid":        random.randint(1000, 65000),
            "cpu_percent": round(cpu_pct, 1),
            "power_w":    round(power, 2),
            "energy_wh":  round(power * random.uniform(0.001, 0.1), 4),
        })
    return result


def build_payload(node_id: str, timestamp: datetime) -> dict:
    system = generate_system_metrics()
    apps   = generate_app_metrics(system["power_w"])
    return {
        "node_id":    node_id,
        "timestamp":  timestamp.isoformat(),
        "metrics":    system,
        "app_metrics": apps,
    }


def fill_historical(hours: int = 24, interval_seconds: int = 10):
    """Fill ClickHouse with historical data for all nodes."""
    now   = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)
    steps = int(hours * 3600 / interval_seconds)
    total = steps * len(NODES)
    sent  = 0

    print(f"Generating {total:,} records ({hours}h, {len(NODES)} nodes, {interval_seconds}s interval)...")

    with httpx.Client(timeout=10) as client:
        t = start
        while t <= now:
            for node_id in NODES:
                payload = build_payload(node_id, t)
                try:
                    resp = client.post(
                        BACKEND_URL,
                        json=payload,
                        headers={"Authorization": f"Bearer {NODE_KEYS[node_id]}"},
                    )
                    sent += 1
                    if resp.status_code != 200:
                        print(f"  Warning: {node_id} → {resp.status_code}: {resp.text[:80]}")
                except Exception as e:
                    print(f"  Error: {e}")

                if sent % 500 == 0:
                    print(f"  {sent:>6,} / {total:,} ({sent/total*100:.1f}%)")

            t += timedelta(seconds=interval_seconds)

    print(f"Done. Sent {sent:,} records.")


def stream_realtime(interval: float = 10.0):
    """Continuously stream fake real-time data."""
    print(f"Streaming data for {len(NODES)} nodes every {interval}s  (Ctrl+C to stop)...")
    with httpx.Client(timeout=10) as client:
        while True:
            now = datetime.now(timezone.utc)
            for node_id in NODES:
                payload = build_payload(node_id, now)
                try:
                    client.post(
                        BACKEND_URL,
                        json=payload,
                        headers={"Authorization": f"Bearer {NODE_KEYS[node_id]}"},
                    )
                except Exception as e:
                    print(f"Error sending to {node_id}: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fill"
    if cmd == "stream":
        stream_realtime()
    elif cmd == "fill":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        fill_historical(hours=hours)
    else:
        print("Usage: python data_generator.py [fill [hours] | stream]")
