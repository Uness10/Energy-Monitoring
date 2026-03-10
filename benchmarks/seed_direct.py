#!/usr/bin/env python3
"""
Fast data seeder — inserts directly into ClickHouse, bypassing the HTTP API.
32,400 rows that would take ~5 min via API are inserted in ~2 seconds.
"""

import random
from datetime import datetime, timezone, timedelta
import clickhouse_connect

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "mlab"
CLICKHOUSE_PASSWORD = "mlab_secure_2026"
CLICKHOUSE_DB = "energy_monitoring"

NODES = [f"workstation-{i:02d}" for i in range(1, 11)]
NODES += [f"rpi-{i:02d}" for i in range(1, 4)]
NODES += ["mobile-01", "mobile-02"]

APPS = ["firefox", "python3", "gcc", "matlab", "code",
        "jupyter", "chrome", "java", "docker", "git"]

SYSTEM_METRICS = ["voltage", "cpu_freq", "cpu_util", "ram_util",
                  "temperature", "power_w", "energy_wh", "uptime_s"]


def rand_metric(name):
    return {
        "voltage":     random.uniform(218, 222),
        "cpu_freq":    random.uniform(800, 4500),
        "cpu_util":    random.uniform(5, 90),
        "ram_util":    random.uniform(20, 85),
        "temperature": random.uniform(35, 85),
        "power_w":     random.uniform(25, 280),
        "energy_wh":   random.uniform(0, 5000),
        "uptime_s":    random.uniform(0, 864000),
    }[name]


def generate_rows(hours: int, interval_seconds: int):
    now   = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now - timedelta(hours=hours)
    rows  = []

    t = start
    while t <= now:
        for node_id in NODES:
            cpu = random.uniform(5, 90)
            power = 30 + (120 * cpu / 100) + random.uniform(-5, 5)

            # System-level rows (app_name = 'system')
            metric_vals = {
                "voltage":     round(random.uniform(218, 222), 1),
                "cpu_freq":    round(random.uniform(800, 4500), 0),
                "cpu_util":    round(cpu, 1),
                "ram_util":    round(random.uniform(20, 85), 1),
                "temperature": round(random.uniform(35, 85), 1),
                "power_w":     round(power, 1),
                "energy_wh":   round(random.uniform(0, 5000), 1),
                "uptime_s":    round(random.uniform(0, 864000), 0),
            }
            for metric, value in metric_vals.items():
                rows.append([t, node_id, "system", metric, value])

            # Per-app rows
            num_apps = random.randint(2, 4)
            app_names = random.sample(APPS, num_apps)
            shares = [random.random() for _ in app_names]
            total_share = sum(shares)
            app_power_budget = power * random.uniform(0.6, 0.8)

            for app_name, share in zip(app_names, shares):
                app_power = (share / total_share) * app_power_budget
                rows.append([t, node_id, app_name, "power_w",    round(app_power, 2)])
                rows.append([t, node_id, app_name, "cpu_percent", round(random.uniform(1, 40), 1)])
                rows.append([t, node_id, app_name, "energy_wh",  round(app_power * 0.05, 4)])

        t += timedelta(seconds=interval_seconds)

    return rows


def main(hours=24, interval_seconds=60):
    print(f"Connecting to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}...")
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )

    print(f"Generating {hours}h of data ({interval_seconds}s interval, {len(NODES)} nodes)...")
    rows = generate_rows(hours, interval_seconds)
    print(f"Generated {len(rows):,} rows. Inserting into ClickHouse...")

    # Insert in batches of 50,000
    batch_size = 50_000
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        client.insert(
            "energy_metrics",
            batch,
            column_names=["timestamp", "node_id", "app_name", "metric", "value"],
        )
        print(f"  Inserted {min(i + batch_size, len(rows)):>8,} / {len(rows):,} rows")

    # Verify
    count = client.query("SELECT count() FROM energy_metrics").result_rows[0][0]
    print(f"\nDone. Total rows in energy_metrics: {count:,}")


if __name__ == "__main__":
    import sys
    hours    = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    main(hours, interval)
