# Setting Up Energy Daemon on External Linux Devices

This guide shows how to easily connect any external Linux device (VM, Raspberry Pi, workstation) to your Energy Monitoring backend.

## Quick Start (Easiest Method)

### On any Linux device with Python 3.8+:

```bash
# 1. Get the daemon files
git clone https://github.com/your-repo/Energy-Monitoring.git
cd Energy-Monitoring/daemon

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the daemon (replace with your backend IP)
export BACKEND_URL="http://192.168.1.100:8000"
export NODE_ID="my-device-name"
python daemon.py
```

That's it! The daemon will:
- Auto-register with your backend
- Generate an API key automatically
- Start collecting and sending metrics

## Configuration Options

### Option 1: Environment Variables (Recommended for deployment)

```bash
export BACKEND_URL="http://192.168.1.100:8000"      # Backend IP:port
export NODE_ID="raspberry-pi-01"                     # Unique device name
export NODE_TYPE="raspberry_pi"                      # Device type
export API_KEY="sk-your-key-if-you-have-one"       # Optional
python daemon.py
```

### Option 2: Command-Line Arguments

```bash
python daemon.py \
  --backend http://192.168.1.100:8000 \
  --node-id my-linux-vm \
  --node-type linux
```

### Option 3: From config.yaml (Traditional)

Edit `config.yaml`:
```yaml
node_id: "my-external-device"
node_type: "raspberry_pi"
backend_url: "http://192.168.1.100:8000"
collection_interval_seconds: 10
```

Then run:
```bash
python daemon.py
```

### Option 4: Mix and Match

Priority order (highest to lowest):
1. Command-line arguments (`--backend`, `--node-id`)
2. Environment variables (`BACKEND_URL`, `NODE_ID`)
3. config.yaml file
4. Defaults (hostname, localhost)

```bash
# Uses BACKEND_URL from env, NODE_ID from cli
python daemon.py --node-id override-device-name
```

## Finding Your Backend IP

From the machine running the Energy Monitoring backend:

```bash
# Get local network IP
hostname -I          # Linux
ipconfig            # Windows
ifconfig            # macOS

# Or simply use if accessing from same network
http://localhost:8000      # Same machine
http://192.168.x.x:8000   # Other machines on network
```

## Running as a Service (Linux)

### Using systemd

Create `/etc/systemd/system/energy-daemon.service`:

```ini
[Unit]
Description=Energy Monitoring Daemon
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Energy-Monitoring/daemon
Environment="BACKEND_URL=http://192.168.1.100:8000"
Environment="NODE_ID=raspberry-pi-01"
ExecStart=/usr/bin/python3 daemon.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable energy-daemon
sudo systemctl start energy-daemon
sudo systemctl status energy-daemon
```

## Troubleshooting

### "Cannot reach backend" error

```bash
# Check if backend is running
curl -s http://192.168.1.100:8000/docs | head -20

# Check network connectivity
ping 192.168.1.100

# Try with localhost if on same machine
export BACKEND_URL="http://localhost:8000"
```

### "Invalid or unknown API key" error

The device should auto-register on first run. If it fails:

```bash
# On the backend machine, manually register:
docker exec clickhouse-01 clickhouse-client --user mlab --password mlab_secure_2026 -q \
  "INSERT INTO energy_monitoring.nodes (node_id, node_type, api_key, description) \
   VALUES ('my-device', 'linux', 'sk-my-device-key-2026', 'My device')"

# Then set API key on device:
export API_KEY="sk-my-device-key-2026"
python daemon.py
```

### No metrics showing in dashboard

1. Verify daemon is running: `ps aux | grep daemon.py`
2. Check daemon logs for errors
3. Verify backend is accessible: `curl http://backend:8000/docs`
4. Check firewall rules on backend machine

## What Gets Collected

Per device, every 10 seconds (configurable):

- **Voltage** (V)
- **CPU Frequency** (MHz)
- **CPU Utilization** (%)
- **RAM Utilization** (%)
- **Temperature** (°C)
- **Power Consumption** (W)
- **Energy Consumption** (Wh)
- **Uptime** (seconds)
- **Top 10 Application Metrics** (CPU %, power usage)

## Data Retention

- Raw data: 1 year (configurable in backend)
- Hourly aggregates: Available via materialized views
- Daily summaries: Available via materialized views

## Architecture

```
┌─────────────────┐
│  Linux Device   │
│  (daemon.py)    │  --[HTTP POST]-->  ┌─────────────┐
│  (this script)  │                    │ Backend API │
└─────────────────┘                    │  :8000      │
                                       └──────┬──────┘
                                              │
                                       ┌──────▼──────┐
                                       │ ClickHouse  │
                                       │   (OLAP DB) │
                                       └──────┬──────┘
                                              │
                                       ┌──────▼──────┐
                                       │  Dashboard  │
                                       │  (React)    │
                                       │  :3000      │
                                       └─────────────┘
```

---

For more info, see the main [README.md](./README.md)
