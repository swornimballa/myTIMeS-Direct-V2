#!/bin/bash

echo "=== myTIMeS Health Check ==="

if ! command -v curl &> /dev/null; then
  echo "curl is required. Please install it."
  exit 1
fi

curl -s --max-time 5 http://localhost:5000/health/ping
if [ $? -ne 0 ]; then
  echo "✗ Backend is not running or not responding."
  echo "  Start it with: ./scripts/start.sh"
  exit 1
fi

curl -s http://localhost:5000/health | python3 -m json.tool
echo "=== Health check complete ==="
