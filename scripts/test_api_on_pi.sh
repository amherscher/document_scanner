#!/bin/bash
# Test API on Pi - run this ON THE PI

echo "Testing API on Pi..."
echo ""

echo "1. Check if service is running:"
sudo systemctl status pi-scan --no-pager | head -5
echo ""

echo "2. Check if port 5000 is listening:"
sudo netstat -tlnp | grep 5000 || ss -tlnp | grep 5000 || echo "Port 5000 not found"
echo ""

echo "3. Test API without JSON parsing:"
curl -v -H "X-Auth: changeme" http://localhost:5000/api/sync/status 2>&1
echo ""

echo "4. Test root endpoint:"
curl -s http://localhost:5000/ | head -5
echo ""

echo "5. Check service logs:"
sudo journalctl -u pi-scan -n 20 --no-pager | tail -10
echo ""

