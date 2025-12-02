#!/bin/bash
# Setup SSH keys for passwordless deployment to Pi

PI_USER=amherscher
PI_HOST=10.29.0.14

echo "=========================================="
echo "Setting up SSH keys for passwordless access"
echo "=========================================="
echo "Target: ${PI_USER}@${PI_HOST}"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ] && [ ! -f ~/.ssh/id_ed25519.pub ]; then
    echo "📝 Generating SSH key..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "pi-scanner-deploy"
    echo "✅ SSH key generated"
else
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        KEY_FILE=~/.ssh/id_ed25519.pub
    else
        KEY_FILE=~/.ssh/id_rsa.pub
    fi
    echo "✅ Using existing SSH key: $KEY_FILE"
fi

# Determine which key to use
if [ -f ~/.ssh/id_ed25519.pub ]; then
    KEY_FILE=~/.ssh/id_ed25519.pub
else
    KEY_FILE=~/.ssh/id_rsa.pub
fi

echo ""
echo "📤 Copying SSH key to Pi..."
echo "   You'll need to enter your Pi password ONCE"
echo ""

# Copy key to Pi
ssh-copy-id -i $KEY_FILE ${PI_USER}@${PI_HOST} || {
    echo ""
    echo "❌ Failed to copy key. Trying manual method..."
    echo ""
    echo "Run this command manually:"
    echo "  ssh-copy-id -i $KEY_FILE ${PI_USER}@${PI_HOST}"
    echo ""
    echo "Or manually add the key:"
    echo "  cat $KEY_FILE | ssh ${PI_USER}@${PI_HOST} 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'"
    exit 1
}

echo ""
echo "✅ SSH key copied successfully!"
echo ""
echo "🧪 Testing passwordless connection..."
ssh -o BatchMode=yes ${PI_USER}@${PI_HOST} "echo 'Connection successful!'" && {
    echo "✅ Passwordless SSH is working!"
    echo ""
    echo "You can now run deploy_to_pi.sh without entering passwords!"
} || {
    echo "⚠️  Passwordless connection test failed"
    echo "   You may need to check Pi SSH configuration"
}

