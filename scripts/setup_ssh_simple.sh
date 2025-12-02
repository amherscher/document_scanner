#!/bin/bash
# Simple SSH setup - run this ON THE PI

echo "Simple SSH Setup for Sync"
echo "========================="
echo ""

echo "1. Starting SSH agent..."
eval "$(ssh-agent -s)"

echo ""
echo "2. Adding SSH key to agent..."
if [ -f ~/.ssh/id_ed25519 ]; then
    ssh-add ~/.ssh/id_ed25519
elif [ -f ~/.ssh/id_rsa ]; then
    ssh-add ~/.ssh/id_rsa
else
    echo "No SSH key found. Generating one..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
    ssh-add ~/.ssh/id_ed25519
fi

echo ""
echo "3. Adding server to known_hosts..."
ssh-keyscan -H 10.29.0.1 >> ~/.ssh/known_hosts 2>/dev/null

echo ""
echo "4. Copying SSH key to server..."
echo "   You'll need to enter the server password:"
if [ -f ~/.ssh/id_ed25519.pub ]; then
    ssh-copy-id -i ~/.ssh/id_ed25519.pub amherscher@10.29.0.1
elif [ -f ~/.ssh/id_rsa.pub ]; then
    ssh-copy-id -i ~/.ssh/id_rsa.pub amherscher@10.29.0.1
fi

echo ""
echo "5. Testing passwordless connection..."
ssh -o BatchMode=yes amherscher@10.29.0.1 "echo 'Passwordless SSH works!'" 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Passwordless SSH is working!"
else
    echo "   ✗ Still needs password"
fi

echo ""
echo "6. Creating server directory..."
ssh amherscher@10.29.0.1 "mkdir -p /home/data/Purdue/pi/scans && chmod 755 /home/data/Purdue/pi/scans" 2>&1

echo ""
echo "✅ Setup complete!"

