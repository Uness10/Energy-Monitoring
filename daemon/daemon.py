#!/usr/bin/env python3
"""
MLab Energy Monitoring Daemon
Flexible version - works with command-line arguments or config file.
Can run multiple instances with different node IDs.

Usage:
  python daemon.py --node-id workstation-01 --backend http://localhost:8000
  python daemon.py --node-id workstation-02 --backend http://localhost:8000
  python daemon.py --node-id remote-machine --backend http://192.168.1.100:8000
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
    """Load config from command-line args, environment variables, or config file."""
    
    parser = argparse.ArgumentParser(
        description="Energy Monitoring Daemon - Flexible Node Registration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single node on localhost
  python daemon.py --node-id workstation-01 --backend http://localhost:8000
  
  # Multiple nodes on same machine
  python daemon.py --node-id node-1 --backend http://localhost:8000
  python daemon.py --node-id node-2 --backend http://localhost:8000
  
  # Remote machine
  python daemon.py --node-id office-pc --backend http://192.168.1.100:8000
  
  # Load from config file
  python daemon.py --config config.yaml
        """
    )
    parser.add_argument("--node-id", help="Node identifier (default: hostname)")
    parser.add_argument("--backend", help="Backend URL (e.g., http://localhost:8000)")
    parser.add_argument("--config", help="Path to config.yaml file")
    parser.add_argument("--interval", type=int, help="Collection interval in seconds (default: 10)")
    args = parser.parse_args()
    
    config = {}
    
    # 1. Load from config file if provided
    if args.config:
        config_path = args.config
    else:
        config_path = Path(__file__).parent / "config.yaml"
    
    if Path(config_path).exists():
        try:
            with open(config_path) as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
            log.info(f"Loaded config from {config_path}")
        except Exception as e:
            log.warning(f"Could not load config file: {e}")
    
    # 2. Override with environment variables
    config["node_id"] = os.getenv("NODE_ID") or args.node_id or config.get("node_id") or socket.gethostname()
    config["node_type"] = os.getenv("NODE_TYPE") or config.get("node_type", "workstation")
    config["backend_url"] = os.getenv("BACKEND_URL") or args.backend or config.get("backend_url")
    config["collection_interval_seconds"] = args.interval or config.get("collection_interval_seconds", 10)
    config["retry_interval_seconds"] = config.get("retry_interval_seconds", 30)
    config["buffer_max_records"] = config.get("buffer_max_records", 3600)
    
    if not config.get("app_tracking"):
        config["app_tracking"] = {"enabled": True, "mode": "top_n", "top_n": 10}
    
    # 3. Validate backend URL
    if not config.get("backend_url"):
        log.error("ERROR: Backend URL not provided!")
        log.error("Provide via: --backend, BACKEND_URL env var, or config.yaml")
        log.error("\nExample:")
        log.error("  python daemon.py --node-id workstation-01 --backend http://localhost:8000")
        sys.exit(1)
    
    # 4. Auto-generate API key from node_id
    # Format: sk-{node_id}-2026
    config["api_key"] = f"sk-{config['node_id']}-2026"
    
    # 5. Normalize backend URL
    backend_url = config["backend_url"].rstrip("/")
    if not backend_url.endswith("/api/v1/metrics"):
        if backend_url.endswith("/api/v1"):
            backend_url = backend_url + "/metrics"
        else:
            backend_url = backend_url + "/api/v1/metrics"
    config["backend_url"] = backend_url
    
    return config


def collect_system_metrics() -> dict:
    """Collect all system metrics."""
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
    """Build payload to send to backend."""
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
    """Send metrics to backend."""
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
                f"Sent metrics for {payload['node_id']} | system KPIs: {len(payload['metrics'])} | apps: {apps}"
            )
            return True
        else:
            log.warning(f"Backend returned {resp.status_code}: {resp.text[:200]}")
            return False
    except httpx.RequestError as e:
        log.error(f"Connection error: {e}")
        return False


def flush_buffer(
    client: httpx.Client,
    url: str,
    api_key: str,
    buf: RetryBuffer,
):
    """Flush buffered metrics."""
    if buf.is_empty:
        return
    
    batch = buf.peek_batch(10)
    sent = 0
    for payload in batch:
        if send_payload(client, url, api_key, payload):
            sent += 1
        else:
            break
    if sent:
        buf.remove_batch(sent)
        log.info(f"Flushed {sent} buffered records ({len(buf)} remaining)")


def main():
    """Main daemon loop."""
    config = load_config()
    buf = RetryBuffer(max_records=config.get("buffer_max_records", 3600))
    interval = config["collection_interval_seconds"]
    retry_interval = config.get("retry_interval_seconds", 30)
    last_retry = 0.0

    log.info("=" * 80)
    log.info("Daemon starting")
    log.info(f"  node_id: {config['node_id']}")
    log.info(f"  node_type: {config['node_type']}")
    log.info(f"  backend: {config['backend_url']}")
    log.info(f"  api_key: {config['api_key']}")
    log.info(f"  interval: {interval}s")
    log.info(f"  app_tracking: {config.get('app_tracking', {}).get('enabled', False)}")
    log.info("=" * 80)

    with httpx.Client() as client:
        while True:
            try:
                # Collect metrics
                system_metrics = collect_system_metrics()
                app_metrics = collect_app_energy(config)

                if app_metrics:
                    top_apps = ", ".join(f"{a['app_name']}={a['power_w']:.1f}W" for a in app_metrics[:3])
                    log.debug(f"Top apps by power: {top_apps}")

                payload = build_payload(config, system_metrics, app_metrics)

                # Send metrics
                if not send_payload(client, config["backend_url"], config["api_key"], payload):
                    buf.add(payload)
                    log.warning(f"Payload buffered ({len(buf)} total in buffer)")

                # Flush buffer periodically
                now = time.time()
                if not buf.is_empty and (now - last_retry) >= retry_interval:
                    flush_buffer(client, config["backend_url"], config["api_key"], buf)
                    last_retry = now

                time.sleep(interval)

            except KeyboardInterrupt:
                log.info("Shutdown requested")
                break
            except Exception as e:
                log.error(f"Unexpected error: {e}")
                time.sleep(interval)

    log.info("Daemon stopped")


if __name__ == "__main__":
    main()