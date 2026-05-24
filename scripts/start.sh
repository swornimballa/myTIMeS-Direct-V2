#!/bin/bash

echo "=== Starting myTIMeS backend ==="

if [ ! -f "backend/.env" ]; then
  echo "✗ backend/.env not found. Run ./scripts/setup.sh first."
  exit 1
fi

if [ ! -f "backend/firebase_credentials.json" ]; then
  echo "⚠ Warning: firebase_credentials.json not found. Firebase features will be disabled."
fi

docker compose up --build

echo "Backend running at http://localhost:5000"
echo "Health check: http://localhost:5000/health"
echo "To start the React Native app: cd frontend && npx expo start"
