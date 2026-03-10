import time
import psutil
import requests
import json
import os
from datetime import datetime
import logging

# -----------------------------
# CONFIGURATION
# -----------------------------
# Backend URL (replace with your actual backend endpoint)
BACKEND_URL = "http://127.0.0.1:8000/api/v1/metrics"
HEARTBEAT_URL = "http://127.0.0.1:8000/api/v1/heartbeat"
INTERVAL_SECONDS = 10   # shorter for testing
NODE_ID = "test-windows-node-01"
DEVICE_TYPE = "workstation"
# -----------------------------
# LOGGING SETUP
# -----------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "agent.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def collect_metrics():
    """Collect energy-related KPIs"""
    try:
        cpu_usage = psutil.cpu_percent()
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        ram_usage = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        battery_level = battery.percent if battery else None
        power_watts = None  # Optional: can add if you have sensor

        data = {
            "device_id": NODE_ID,
            "device_type": DEVICE_TYPE,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_utilization": cpu_usage,
            "cpu_frequency": cpu_freq,
            "ram_utilization": ram_usage,
            "power_watts": power_watts,
            "battery_level": battery_level
        }
        return data
    except Exception as e:
        logging.error(f"Error collecting metrics: {e}")
        return None

def send_to_backend(data):
    """Send metrics to backend, retry if fails"""
    if data is None:
        return
    try:
        response = requests.post(BACKEND_URL, json=[data], timeout=5)
        if response.status_code == 200:
            logging.info(f"Metrics sent successfully: {data}")
        else:
            logging.warning(f"Backend returned {response.status_code}: {response.text}")
            buffer_data(data)
    except Exception as e:
        logging.error(f"Failed to send metrics: {e}")
        buffer_data(data)

def send_heartbeat():
    """Send a heartbeat signal"""
    heartbeat = {
        "device_id": NODE_ID,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        response = requests.post(HEARTBEAT_URL, json=heartbeat, timeout=5)
        if response.status_code == 200:
            logging.info("Heartbeat sent successfully")
        else:
            logging.warning(f"Heartbeat failed: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send heartbeat: {e}")

# Buffer failed sends locally
BUFFER_FILE = os.path.join(LOG_DIR, "failed_sends.json")
def buffer_data(data):
    try:
        with open(BUFFER_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        logging.info("Data buffered locally")
    except Exception as e:
        logging.error(f"Failed to buffer data: {e}")

def resend_buffered_data():
    """Try sending buffered data"""
    if not os.path.exists(BUFFER_FILE):
        return
    try:
        lines = []
        with open(BUFFER_FILE, "r") as f:
            lines = f.readlines()
        if not lines:
            return

        success_lines = []
        for line in lines:
            try:
                data = json.loads(line)
                response = requests.post(BACKEND_URL, json=[data], timeout=5)
                if response.status_code == 200:
                    logging.info(f"Buffered data sent successfully: {data}")
                else:
                    success_lines.append(line)  # keep for later
            except Exception:
                success_lines.append(line)

        # Rewrite buffer with remaining failed lines
        with open(BUFFER_FILE, "w") as f:
            f.writelines(success_lines)

    except Exception as e:
        logging.error(f"Error resending buffered data: {e}")

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    logging.info("Daemon started")
    while True:
        data = collect_metrics()
        send_to_backend(data)
        send_heartbeat()
        resend_buffered_data()
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()