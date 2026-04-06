#!/bin/bash

# Energy Monitoring Daemon - Installation Script
# Run this on any Linux device to set up the daemon
# Usage: bash install-daemon.sh <BACKEND_URL> <NODE_ID> [NODE_TYPE]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Energy Monitoring Daemon - Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: bash install-daemon.sh <BACKEND_URL> <NODE_ID> [NODE_TYPE]${NC}"
    echo ""
    echo "Examples:"
    echo "  bash install-daemon.sh http://192.168.1.100:8000 raspberry-pi-01 raspberry_pi"
    echo "  bash install-daemon.sh http://192.168.1.100:8000 my-linux-vm linux"
    exit 1
fi

BACKEND_URL=$1
NODE_ID=$2
NODE_TYPE=${3:-"linux"}

echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

echo -e "${YELLOW}Creating daemon directory...${NC}"
DAEMON_DIR="$HOME/energy-daemon"
mkdir -p "$DAEMON_DIR"
cd "$DAEMON_DIR"
echo -e "${GREEN}✓ Daemon directory: $DAEMON_DIR${NC}"

echo -e "${YELLOW}Downloading daemon files...${NC}"
# Base URL for raw files from GitHub (or your repository)
BASE_URL="https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/daemon"

# Create subdirectories
mkdir -p collectors

# Download main daemon files
echo -e "${YELLOW}  Downloading daemon.py...${NC}"
curl -s "$BASE_URL/daemon.py" -o daemon.py || {
    echo -e "${RED}Failed to download daemon.py${NC}"
    exit 1
}

echo -e "${YELLOW}  Downloading buffer.py...${NC}"
curl -s "$BASE_URL/buffer.py" -o buffer.py || true

echo -e "${YELLOW}  Downloading collectors...${NC}"
for collector in cpu memory power temperature uptime app_energy __init__; do
    curl -s "$BASE_URL/collectors/${collector}.py" -o "collectors/${collector}.py" || {
        echo -e "${YELLOW}  ⚠ Could not download collectors/${collector}.py (will try to use locally)${NC}"
    }
done

echo -e "${GREEN}✓ Daemon files downloaded${NC}"

echo -e "${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
cat > requirements.txt << EOF
httpx==0.25.0
pyyaml==6.0
psutil==5.9.6
EOF

pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}Creating config.yaml...${NC}"
cat > config.yaml << EOF
# Energy Monitoring Daemon Config
# Auto-generated - $(date)

node_id: "$NODE_ID"
node_type: "$NODE_TYPE"
backend_url: "$BACKEND_URL"
collection_interval_seconds: 10
retry_interval_seconds: 30
buffer_max_records: 3600

app_tracking:
  enabled: true
  mode: "top_n"
  top_n: 10
  min_cpu_percent: 1.0
EOF

echo -e "${GREEN}✓ Configuration created${NC}"

echo -e "${YELLOW}Creating startup scripts...${NC}"

# Create run script
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python daemon.py
EOF
chmod +x run.sh

# Create systemd service (for Linux)
cat > energy-daemon.service << EOF
[Unit]
Description=Energy Monitoring Daemon
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DAEMON_DIR
Environment="BACKEND_URL=$BACKEND_URL"
Environment="NODE_ID=$NODE_ID"
ExecStart=$DAEMON_DIR/venv/bin/python $DAEMON_DIR/daemon.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Startup scripts created${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Backend URL: $BACKEND_URL"
echo "  Node ID: $NODE_ID"
echo "  Node Type: $NODE_TYPE"
echo "  Directory: $DAEMON_DIR"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo "  1. Test the daemon:"
echo "     cd $DAEMON_DIR && bash run.sh"
echo ""
echo "  2. Install as system service (optional):"
echo "     sudo cp energy-daemon.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable energy-daemon"
echo "     sudo systemctl start energy-daemon"
echo "     sudo systemctl status energy-daemon"
echo ""
echo "  3. View logs:"
echo "     sudo journalctl -u energy-daemon -f"
echo ""
echo -e "${GREEN}The daemon will auto-register with the backend!${NC}"
echo ""
