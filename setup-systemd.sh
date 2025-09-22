#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== KVV Display Systemd Setup ===${NC}"

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run with sudo: sudo bash setup-systemd.sh${NC}"
    exit 1
fi

# Create service file
echo -e "${YELLOW}Creating kvv-display.service...${NC}"
cat > /etc/systemd/system/kvv-display.service << 'EOF'
[Unit]
Description=KVV Transit and Tibber Energy Display
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/e-Paper/RaspberryPi_JetsonNano/python/kvv-rpi-display
ExecStart=/usr/bin/python3 /home/pi/e-Paper/RaspberryPi_JetsonNano/python/kvv-rpi-display/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="HA_TOKEN=your_actual_token_here"
Environment="PYTHONUNBUFFERED=1"
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Create restart timer
echo -e "${YELLOW}Creating daily restart timer...${NC}"
cat > /etc/systemd/system/kvv-display-restart.timer << 'EOF'
[Unit]
Description=Daily restart of KVV Display service at 3 AM
Requires=kvv-display-restart.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 03:00:00
AccuracySec=1m
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create restart service
cat > /etc/systemd/system/kvv-display-restart.service << 'EOF'
[Unit]
Description=Restart KVV Display service
Requires=kvv-display.service

[Service]
Type=oneshot
ExecStart=/bin/systemctl restart kvv-display.service
EOF

# Reload systemd
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable services
echo -e "${YELLOW}Enabling services...${NC}"
systemctl enable kvv-display.service
systemctl enable kvv-display-restart.timer

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl start kvv-display.service
systemctl start kvv-display-restart.timer

# Check status
echo -e "${GREEN}=== Service Status ===${NC}"
systemctl status kvv-display.service --no-pager -l
echo ""
echo -e "${GREEN}=== Timer Status ===${NC}"
systemctl status kvv-display-restart.timer --no-pager -l

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo -e "${YELLOW}Useful commands:${NC}"
echo "  sudo systemctl status kvv-display.service    # Check service status"
echo "  sudo systemctl restart kvv-display.service   # Manual restart"
echo "  sudo systemctl stop kvv-display.service      # Stop service"
echo "  sudo systemctl start kvv-display.service     # Start service"
echo "  sudo journalctl -u kvv-display -f            # View logs (live)"
echo "  sudo journalctl -u kvv-display --since today # Today's logs"
echo "  systemctl list-timers                        # View all timers"
echo ""
echo -e "${YELLOW}The display will automatically:${NC}"
echo "  - Start on boot"
echo "  - Restart if it crashes"
echo "  - Restart daily at 3:00 AM"