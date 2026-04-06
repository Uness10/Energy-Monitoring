# Energy Daemon - Easy Installation Guide

External devices (Raspberry Pi, Linux VMs, Windows PCs) can easily connect to your Energy Monitoring backend using one of three methods.

## 🚀 Quick Start (Pick One)

### **Option 1: Automated Installer (Easiest)**

The installer script downloads everything automatically.

**Linux/Raspberry Pi:**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/install-daemon.sh) \
  "http://192.168.1.100:8000" "my-device-01" "linux"
```

**Windows:**
```cmd
powershell -Command "iex(New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/install-daemon.bat')" "http://192.168.1.100:8000" "my-device-01" "windows"
```

**What it does:**
✅ Download daemon files  
✅ Create virtual environment  
✅ Install dependencies  
✅ Setup configuration  
✅ Create startup scripts  

After running: `cd ~/energy-daemon && bash run.sh`

---

### **Option 2: Docker (No Python Needed)**

For devices with Docker:

```bash
# Build once
cd Energy-Monitoring
docker build -t energy-daemon:latest -f Dockerfile.daemon .

# Run on any device
docker run -d \
  -e BACKEND_URL="http://192.168.1.100:8000" \
  -e NODE_ID="my-device" \
  --name energy-daemon \
  energy-daemon:latest

# See logs
docker logs -f energy-daemon
```

---

### **Option 3: Manual Setup**

```bash
# Clone repo
git clone https://github.com/your-repo/Energy-Monitoring.git
cd Energy-Monitoring/daemon

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
export BACKEND_URL="http://192.168.1.100:8000"
export NODE_ID="my-device"
python daemon.py
```

---

## 📋 Configuration

The daemon auto-registers with the backend, so just set:

- `BACKEND_URL` - Backend IP:port (e.g., `http://192.168.1.100:8000`)
- `NODE_ID` - Device name (e.g., `pi-lab`, `workstation-01`)
- `NODE_TYPE` - Device type (e.g., `linux`, `raspberry_pi`, `windows`)

**Configuration Priority:**
1. Command-line: `--backend`, `--node-id`, `--node-type`
2. Environment: `BACKEND_URL`, `NODE_ID`, `NODE_TYPE`
3. config.yaml file
4. System hostname (fallback)

---

## 🔍 Finding Your Backend IP

From the machine running the Energy Monitoring backend:

```bash
# Linux
hostname -I

# Windows
ipconfig

# macOS
ifconfig
```

Or use if on same network: `http://localhost:8000`

---

## 🔧 Run as System Service

### **Linux (systemd)**

The installer creates `energy-daemon.service`. To enable:

```bash
sudo cp ~/energy-daemon/energy-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable energy-daemon
sudo systemctl start energy-daemon
sudo systemctl status energy-daemon

# View logs
sudo journalctl -u energy-daemon -f
```

### **Windows (Task Scheduler)**

1. Open Task Scheduler
2. Create Basic Task → "Energy Daemon"
3. Trigger: "At startup"
4. Action: "Start a program"
5. Program: `C:\Users\<username>\energy-daemon\run.bat`
6. Check "Run with highest privileges"

---

## 📊 What Gets Collected

Every 10 seconds from each device:

- Voltage, CPU Frequency, CPU Usage, RAM Usage
- Temperature, Power Draw, Energy Used, Uptime
- Top 10 applications by CPU usage

---

## ❓ Troubleshooting

### "Cannot reach backend"
```bash
# Test connectivity
curl http://192.168.1.100:8000/docs

# Check firewall
telnet 192.168.1.100 8000
```

### "Backend is not responding" 
```bash
# Verify backend is running (on backend machine)
docker ps
curl http://localhost:8000/docs
```

### "Connection refused"
- Make sure `BACKEND_URL` uses correct IP (not `localhost`)
- Check firewall allows port 8000
- Verify backend is actually running

### "daemon.py not found"
- Use the automated installer (easiest)
- Or ensure you cloned the full repository

---

## 🎯 Example: Setup Multiple Devices

**Device 1 (Raspberry Pi):**
```bash
bash install-daemon.sh http://192.168.1.50:8000 "pi-lab-01" "raspberry_pi"
```

**Device 2 (Linux VM):**
```bash
bash install-daemon.sh http://192.168.1.50:8000 "vm-server-02" "linux"
```

**Device 3 (Windows Workstation):**
```cmd
install-daemon.bat http://192.168.1.50:8000 "workstation-03" "windows"
```

All devices will automatically register and appear on the dashboard!

---

## 📚 More Information

- [Main README](./README.md)
- [Backend Documentation](./backend/README.md)
- [Full Architecture](./docs/project-plan.md)
