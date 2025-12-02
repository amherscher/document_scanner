#!/bin/bash
# Fix SSH host key verification - run this ON THE PI

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}
SERVER_USER=${SERVER_USER:-amherscher}
SERVER_HOST=${SERVER_HOST:-10.29.0.1}
SERVER_DIR=${SERVER_DIR:-/home/data/Purdue/pi/scans}

echo "Fixing SSH host key verification..."
echo ""

ssh ${PI_USER}@${PI_HOST} << EOF
echo "1. Adding server host key to known_hosts..."
ssh-keyscan -H ${SERVER_HOST} >> ~/.ssh/known_hosts 2>/dev/null

echo "2. Verifying host key was added..."
grep ${SERVER_HOST} ~/.ssh/known_hosts || echo "Host key not found"

echo ""
echo "3. Testing SSH connection (will prompt for password first time)..."
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST} "echo 'Connection test successful'" 2>&1

echo ""
echo "4. Now trying to copy SSH key..."
if [ -f ~/.ssh/id_ed25519.pub ]; then
    KEY_FILE=~/.ssh/id_ed25519.pub
elif [ -f ~/.ssh/id_rsa.pub ]; then
    KEY_FILE=~/.ssh/id_rsa.pub
else
    echo "No SSH key found. Generating one..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "pi-scanner-sync"
    KEY_FILE=~/.ssh/id_ed25519.pub
fi

echo "Using key: \$KEY_FILE"
echo ""
echo "Copying key to server (you'll need to enter server password):"
ssh-copy-id -i \$KEY_FILE ${SERVER_USER}@${SERVER_HOST}

echo ""
echo "5. Testing passwordless connection..."
ssh -o BatchMode=yes ${SERVER_USER}@${SERVER_HOST} "echo 'Passwordless SSH works!'" 2>&1
if [ \$? -eq 0 ]; then
    echo "   ✓ Passwordless SSH is working!"
else
    echo "   ✗ Passwordless SSH still needs setup"
fi

echo ""
echo "6. Creating server directory..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_DIR} && chmod 755 ${SERVER_DIR}" 2>&1

echo ""
echo "7. Verifying directory..."
ssh ${SERVER_USER}@${SERVER_HOST} "test -d ${SERVER_DIR} && echo 'Directory exists' || echo 'Directory missing'" 2>&1
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Now test sync status on Pi:"
echo "  curl -s -H 'X-Auth: changeme' http://localhost:5000/api/sync/status | python3 -m json.tool"

