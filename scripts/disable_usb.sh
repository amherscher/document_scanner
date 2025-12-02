#!/bin/bash
# Disable all USB ports to turn off USB LED

if ! command -v uhubctl &> /dev/null; then
    echo "Error: uhubctl not installed. Install with: sudo apt-get install uhubctl" >&2
    exit 1
fi

echo "Disabling all USB ports..." >&2

# Find all hubs
HUBS=$(sudo uhubctl 2>&1 | grep -oP 'hub \K\d+' | sort -u)

if [ -z "$HUBS" ]; then
    echo "No hubs found, trying common hub numbers..." >&2
    HUBS="1 2 3 4"
fi

DISABLED_COUNT=0

# Disable all ports on all hubs
for hub in $HUBS; do
    for port in 1 2 3 4 5; do
        if sudo uhubctl -l $hub -p $port -a 0 2>&1 | grep -q "port"; then
            echo "USB port $port on hub $hub disabled" >&2
            ((DISABLED_COUNT++))
        fi
    done
done

if [ $DISABLED_COUNT -gt 0 ]; then
    echo "Disabled $DISABLED_COUNT USB port(s) - LED should be off now" >&2
    exit 0
else
    echo "Warning: Failed to disable any USB ports. Check uhubctl output:" >&2
    sudo uhubctl 2>&1 | head -10 >&2
    exit 1
fi

