#!/bin/bash
# Emergency script to re-enable all USB ports

echo "Re-enabling all USB ports..."

# Find all hubs
HUBS=$(sudo uhubctl 2>/dev/null | grep -oP 'hub \K\d+' | sort -u)

if [ -z "$HUBS" ]; then
    echo "No hubs found, trying defaults..."
    HUBS="1 2 3 4"
fi

echo "Found hubs: $HUBS"

# Enable all ports on all hubs
for hub in $HUBS; do
    for port in 1 2 3 4 5; do
        echo "Enabling hub $hub port $port..."
        sudo uhubctl -l $hub -p $port -a 1 2>&1
    done
done

echo "Done! Check USB status with: sudo uhubctl"

