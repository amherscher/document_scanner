#!/bin/bash
# Disable all USB ports to turn off USB LED

echo "Disabling all USB ports..."

# Find all hubs
HUBS=$(sudo uhubctl 2>/dev/null | grep -oP 'hub \K\d+' | sort -u)

if [ -z "$HUBS" ]; then
    echo "No hubs found, trying defaults..." >&2
    HUBS="1 2 3 4"
fi

DISABLED_COUNT=0

# Disable all ports on all hubs
for hub in $HUBS; do
    for port in 1 2 3 4 5; do
        if sudo uhubctl -l $hub -p $port -a 0 >/dev/null 2>&1; then
            echo "USB port $port on hub $hub disabled" >&2
            ((DISABLED_COUNT++))
        fi
    done
done

if [ $DISABLED_COUNT -gt 0 ]; then
    echo "Disabled $DISABLED_COUNT USB port(s) - LED should be off now"
    exit 0
else
    echo "Failed to disable any USB ports" >&2
    exit 1
fi

