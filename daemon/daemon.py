#!/usr/bin/env python3
"""MLab Energy Monitoring Daemon — collects KPIs and sends them to the backend."""

import time
import logging
import yaml
import httpx
from datetime import datetime, timezone
from pathlib import Path

from collectors.cpu import get_cpu_utilization, get_cpu_frequency
from collectors.memory import get_ram_utilization
from collectors.temperature import get_temperature
from collectors.power import get_voltage, get_power_watts, get_energy_wh
from collectors.uptime import get_uptime_seconds
from buffer import RetryBuffer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("energy-daemon")


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def collect_metrics() -> dict:
    return {
        "voltage": get_voltage(),
        "cpu_freq": get_cpu_frequency(),
        "cpu_util": get_cpu_utilization(),
        "ram_util": get_ram_utilization(),
        "temperature": get_temperature(),
        "power_w": get_power_watts(),
        "energy_wh": get_energy_wh(),
        "uptime_s": get_uptime_seconds(),
    }


def build_payload(config: dict, metrics: dict) -> dict:
    return {
        "node_id": config["node_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }


def send_payload(client: httpx.Client, url: str, api_key: str, payload: dict) -> bool:
    try:
        resp = client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            log.info("Sent metrics for %s", payload["node_id"])
            return True
        else:
            log.warning("Backend returned %d: %s", resp.status_code, resp.text)
            return False
    except httpx.RequestError as e:
        log.error("Connection error: %s", e)
        return False


def flush_buffer(client: httpx.Client, url: str, api_key: str, buf: RetryBuffer):
    batch = buf.peek_batch(10)
    sent = 0
    for payload in batch:
        if send_payload(client, url, api_key, payload):
            sent += 1
        else:
            break
    if sent:
        buf.remove_batch(sent)
        log.info("Flushed %d buffered records (%d remaining)", sent, len(buf))


def main():
    config = load_config()
    buf = RetryBuffer(max_records=config.get("buffer_max_records", 3600))
    interval = config["collection_interval_seconds"]
    retry_interval = config.get("retry_interval_seconds", 30)
    last_retry = 0.0

    log.info(
        "Daemon starting — node=%s interval=%ds backend=%s",
        config["node_id"], interval, config["backend_url"],
    )

    with httpx.Client() as client:
        while True:
            metrics = collect_metrics()
            payload = build_payload(config, metrics)
            log.debug("Collected: %s", metrics)

            if not send_payload(client, config["backend_url"], config["api_key"], payload):
                buf.add(payload)
                log.warning("Buffered payload (%d total)", len(buf))

            # Periodically try to flush buffer
            now = time.time()
            if not buf.is_empty and (now - last_retry) >= retry_interval:
                flush_buffer(client, config["backend_url"], config["api_key"], buf)
                last_retry = now

            time.sleep(interval)


if __name__ == "__main__":
    main()
