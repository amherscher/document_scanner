#!/bin/bash
# Test sync configuration and connection

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}
SERVER_HOST=${SERVER_HOST:-10.29.0.1}
SERVER_USER=${SERVER_USER:-amherscher}
SERVER_DIR=${SERVER_DIR:-/home/data/Purdue/pi/scans}

echo "=========================================="
echo "Testing Sync Configuration"
echo "=========================================="
echo ""

echo "1. Checking sync configuration on Pi..."
ssh ${PI_USER}@${PI_HOST} << EOF
cd /opt/scanner
echo "SYNC_ENABLED: \${SYNC_ENABLED:-not set}"
echo "SYNC_SERVER_HOST: \${SYNC_SERVER_HOST:-not set}"
echo "SYNC_SERVER_USER: \${SYNC_SERVER_USER:-not set}"
echo "SYNC_SERVER_DIR: \${SYNC_SERVER_DIR:-not set}"
echo "AUTO_SYNC: \${AUTO_SYNC:-not set}"
echo ""

echo "2. Checking service environment variables..."
sudo systemctl show pi-scan | grep -i sync || echo "No sync env vars in service"
echo ""

echo "3. Testing SSH connection to server..."
ssh -o ConnectTimeout=5 -o BatchMode=yes ${SERVER_USER}@${SERVER_HOST} "echo 'SSH connection successful'" 2>&1
echo "Exit code: \$?"
echo ""

echo "4. Checking if server directory exists..."
ssh ${SERVER_USER}@${SERVER_HOST} "test -d ${SERVER_DIR} && echo 'Directory exists' || echo 'Directory does not exist'" 2>&1
echo ""

echo "5. Testing rsync to server..."
TEST_FILE="/tmp/sync_test_$(date +%s).txt"
echo "test" > \$TEST_FILE
rsync -avz --remove-source-files \$TEST_FILE ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/ 2>&1
echo "Exit code: \$?"
echo ""

echo "6. Checking files on server..."
ssh ${SERVER_USER}@${SERVER_HOST} "ls -lh ${SERVER_DIR}/ | head -10" 2>&1
EOF

echo ""
echo "=========================================="
echo "Sync Test Complete"
echo "=========================================="
echo ""
echo "To enable sync on Pi, edit /etc/systemd/system/pi-scan.service:"
echo "  Environment=\"SYNC_ENABLED=true\""
echo "  Environment=\"SYNC_SERVER_HOST=${SERVER_HOST}\""
echo "  Environment=\"SYNC_SERVER_USER=${SERVER_USER}\""
echo "  Environment=\"SYNC_SERVER_DIR=${SERVER_DIR}\""
echo ""
echo "On server (${SERVER_HOST}), ensure directory exists:"
echo "  mkdir -p ${SERVER_DIR}"
echo "  chmod 755 ${SERVER_DIR}"
echo ""
echo "Then restart: sudo systemctl restart pi-scan"

