#!/bin/bash
# Enable all USB ports to turn on USB LED

echo "Enabling all USB ports..."

# Find all hubs
HUBS=$(sudo uhubctl 2>/dev/null | grep -oP 'hub \K\d+' | sort -u)

if [ -z "$HUBS" ]; then
    echo "No hubs found, trying defaults..." >&2
    HUBS="1 2 3 4"
fi

ENABLED_COUNT=0

# Enable all ports on all hubs
for hub in $HUBS; do
    for port in 1 2 3 4 5; do
        if sudo uhubctl -l $hub -p $port -a 1 >/dev/null 2>&1; then
            echo "USB port $port on hub $hub enabled" >&2
            ((ENABLED_COUNT++))
        fi
    done
done

if [ $ENABLED_COUNT -gt 0 ]; then
    echo "Enabled $ENABLED_COUNT USB port(s) - LED should be on now"
    exit 0
else
    echo "Failed to enable any USB ports" >&2
    exit 1
fi

