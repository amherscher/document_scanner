#!/bin/bash
# Setup SSH keys for sync from Pi to Server

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}
SERVER_USER=${SERVER_USER:-amherscher}
SERVER_HOST=${SERVER_HOST:-10.29.0.1}
SERVER_DIR=${SERVER_DIR:-/home/data/Purdue/pi/scans}

echo "Setting up SSH keys for sync..."
echo "Pi: ${PI_USER}@${PI_HOST}"
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo ""

ssh ${PI_USER}@${PI_HOST} << EOF
echo "1. Checking for SSH key on Pi..."
if [ ! -f ~/.ssh/id_rsa.pub ] && [ ! -f ~/.ssh/id_ed25519.pub ]; then
    echo "   Generating SSH key..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "pi-scanner-sync"
    KEY_FILE=~/.ssh/id_ed25519.pub
else
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        KEY_FILE=~/.ssh/id_ed25519.pub
    else
        KEY_FILE=~/.ssh/id_rsa.pub
    fi
    echo "   Using existing key: \$KEY_FILE"
fi

echo ""
echo "2. Copying SSH key to server..."
echo "   You may need to enter the server password once:"
ssh-copy-id -i \$KEY_FILE ${SERVER_USER}@${SERVER_HOST} || {
    echo "   Failed to copy key automatically. Manual method:"
    echo "   Run this command manually:"
    echo "   ssh-copy-id -i \$KEY_FILE ${SERVER_USER}@${SERVER_HOST}"
}

echo ""
echo "3. Testing passwordless SSH connection..."
ssh -o ConnectTimeout=5 -o BatchMode=yes ${SERVER_USER}@${SERVER_HOST} "echo 'SSH connection successful'" 2>&1
if [ \$? -eq 0 ]; then
    echo "   ✓ Passwordless SSH is working!"
else
    echo "   ✗ Passwordless SSH failed"
fi

echo ""
echo "4. Creating server directory..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_DIR} && chmod 755 ${SERVER_DIR}" 2>&1
echo "   Exit code: \$?"

echo ""
echo "5. Verifying server directory exists..."
ssh ${SERVER_USER}@${SERVER_HOST} "test -d ${SERVER_DIR} && echo 'Directory exists' || echo 'Directory missing'" 2>&1
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Test sync status:"
echo "  curl -s -H 'X-Auth: changeme' http://pi-scan.local:5000/api/sync/status | python3 -m json.tool"

