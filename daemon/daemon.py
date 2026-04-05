#!/usr/bin/env python3
"""
MLab Energy Monitoring Daemon
Collects 8 system KPIs + per-application energy and sends them to the backend.
"""

import time
import logging
import yaml
import httpx
import os
import sys
import argparse
import socket
from datetime import datetime, timezone
from pathlib import Path

from collectors.cpu import get_cpu_utilization, get_cpu_frequency
from collectors.memory import get_ram_utilization
from collectors.power import get_voltage, get_power_watts, get_energy_wh
from collectors.temperature import get_temperature
from collectors.uptime import get_uptime_seconds
from collectors.app_energy import collect_app_energy
from buffer import RetryBuffer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("energy-daemon")


def load_config() -> dict:
    """Load config from file, environment variables, or command-line arguments."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Energy Monitoring Daemon")
    parser.add_argument("--backend", help="Backend URL (e.g., http://192.168.1.100:8000)")
    parser.add_argument("--node-id", help="Node identifier (default: hostname)")
    parser.add_argument("--node-type", help="Node type (workstation, raspberry_pi, linux, etc.)")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--interval", type=int, help="Collection interval in seconds")
    parser.add_argument("--config", help="Path to config.yaml file")
    args = parser.parse_args()
    
    config = {}
    
    # 1. Try loading from config file
    config_path = args.config or Path(__file__).parent / "config.yaml"
    if Path(config_path).exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        log.info("Loaded config from %s", config_path)
    
    # 2. Override with environment variables
    config["node_id"] = os.getenv("NODE_ID") or args.node_id or config.get("node_id") or socket.gethostname()
    config["node_type"] = os.getenv("NODE_TYPE") or args.node_type or config.get("node_type", "linux")
    config["backend_url"] = os.getenv("BACKEND_URL") or args.backend or config.get("backend_url")
    config["api_key"] = os.getenv("API_KEY") or args.api_key or config.get("api_key")
    config["collection_interval_seconds"] = args.interval or config.get("collection_interval_seconds", 10)
    config["retry_interval_seconds"] = config.get("retry_interval_seconds", 30)
    config["buffer_max_records"] = config.get("buffer_max_records", 3600)
    
    if not config.get("app_tracking"):
        config["app_tracking"] = {"enabled": True, "mode": "top_n", "top_n": 10}
    
    # Validate backend URL
    if not config.get("backend_url"):
        log.error("ERROR: Backend URL not provided!")
        log.error("Provide via: --backend, BACKEND_URL env var, or config.yaml")
        sys.exit(1)
    
    # Ensure backend_url points to /api/v1/metrics
    backend_url = config["backend_url"]
    if not backend_url.endswith("/"):
        backend_url += "/"
    if not backend_url.endswith("api/v1/metrics"):
        backend_url = backend_url.rstrip("/") + "/api/v1/metrics"
    config["backend_url"] = backend_url
    
    # 3. Auto-register if no API key provided
    if not config.get("api_key"):
        config["api_key"] = auto_register_with_backend(
            backend_url=config["backend_url"].replace("/api/v1/metrics", ""),
            node_id=config["node_id"],
            node_type=config["node_type"]
        )
        if config["api_key"]:
            log.info("Auto-registered with backend. API Key: %s", config["api_key"])
        else:
            log.error("Failed to auto-register with backend. Provide API key via --api-key or API_KEY env var")
            sys.exit(1)
    
    return config


def auto_register_with_backend(backend_url: str, node_id: str, node_type: str) -> str:
    """Auto-register device with backend and return API key."""
    try:
        # First, try to register/get API key from backend
        # This endpoint should generate and return an API key
        register_url = f"{backend_url}/api/v1/auth/register-device"
        
        payload = {
            "node_id": node_id,
            "node_type": node_type,
            "description": f"Auto-registered {node_type} device"
        }
        
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(register_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("api_key") or f"sk-{node_id}-auto"
    except Exception as e:
        log.warning("Could not auto-register: %s (proceeding with generated key)", e)
    
    # Fallback: generate a deterministic API key
    return f"sk-{node_id}-auto-2026"


def collect_system_metrics() -> dict:
    return {
        "voltage":     get_voltage(),
        "cpu_freq":    get_cpu_frequency(),
        "cpu_util":    get_cpu_utilization(),
        "ram_util":    get_ram_utilization(),
        "temperature": get_temperature(),
        "power_w":     get_power_watts(),
        "energy_wh":   get_energy_wh(),
        "uptime_s":    get_uptime_seconds(),
    }


def build_payload(config: dict, metrics: dict, app_metrics: list) -> dict:
    payload = {
        "node_id":   config["node_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics":   metrics,
    }
    if app_metrics:
        payload["app_metrics"] = app_metrics
    return payload


def send_payload(
    client: httpx.Client,
    url: str,
    api_key: str,
    payload: dict,
) -> bool:
    try:
        resp = client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            apps = len(payload.get("app_metrics", []))
            log.info(
                "Sent metrics for %s | system KPIs: %d | apps: %d",
                payload["node_id"],
                len(payload["metrics"]),
                apps,
            )
            return True
        else:
            log.warning("Backend returned %d: %s", resp.status_code, resp.text[:200])
            return False
    except httpx.RequestError as e:
        log.error("Connection error: %s", e)
        return False


def flush_buffer(
    client: httpx.Client,
    url: str,
    api_key: str,
    buf: RetryBuffer,
):
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

    log.info("=" * 80)
    log.info("Daemon starting")
    log.info("  node_id: %s", config["node_id"])
    log.info("  node_type: %s", config["node_type"])
    log.info("  backend: %s", config["backend_url"])
    log.info("  interval: %ds", interval)
    log.info("  app_tracking: %s", config.get("app_tracking", {}).get("enabled", False))
    log.info("=" * 80)

    with httpx.Client() as client:
        while True:
            # ── Collect ──────────────────────────────────────────────────────
            system_metrics = collect_system_metrics()
            app_metrics = collect_app_energy(config)

            if app_metrics:
                log.debug(
                    "Top apps by power: %s",
                    ", ".join(f"{a['app_name']}={a['power_w']:.1f}W" for a in app_metrics[:3]),
                )

            payload = build_payload(config, system_metrics, app_metrics)

            # ── Send ─────────────────────────────────────────────────────────
            if not send_payload(client, config["backend_url"], config["api_key"], payload):
                buf.add(payload)
                log.warning("Payload buffered (%d total in buffer)", len(buf))

            # ── Flush buffer periodically ─────────────────────────────────────
            now = time.time()
            if not buf.is_empty and (now - last_retry) >= retry_interval:
                flush_buffer(client, config["backend_url"], config["api_key"], buf)
                last_retry = now

            time.sleep(interval)


if __name__ == "__main__":
    main()
