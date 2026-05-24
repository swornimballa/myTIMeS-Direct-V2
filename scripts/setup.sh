#!/bin/bash

echo "=== myTIMeS Direct V2 — First Time Setup ==="

# Step 1
if [ ! -f "backend/.env" ]; then
  cp backend/.env.example backend/.env
  echo "✓ Created backend/.env — fill in your Firebase credentials before starting"
else
  echo "✓ backend/.env already exists"
fi

# Step 2
if [ ! -f "frontend/.env" ]; then
  cp frontend/.env.example frontend/.env
  echo "✓ Created frontend/.env — fill in your Firebase config values"
else
  echo "✓ frontend/.env already exists"
fi

# Step 3
mkdir -p backend/database/
mkdir -p backend/models_storage/
echo "✓ Required directories ready"

# Step 4
if [ ! -f "backend/firebase_credentials.json" ]; then
  echo ""
  echo "⚠ ACTION REQUIRED: Firebase credentials not found."
  echo "  1. Go to: https://console.firebase.google.com"
  echo "  2. Project Settings → Service Accounts → Generate new private key"
  echo "  3. Save the file as: backend/firebase_credentials.json"
  echo ""
fi

# Step 5
if [ ! -f "backend/haarcascade_frontalface_default.xml" ]; then
  echo ""
  echo "⚠ ACTION REQUIRED: Haar Cascade file not found."
  echo "  1. Download haarcascade_frontalface_default.xml from:"
  echo "     https://github.com/opencv/opencv/tree/master/data/haarcascades"
  echo "  2. Save it as: backend/haarcascade_frontalface_default.xml"
  echo ""
fi

echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Fill in backend/.env with your real Firebase and secret values"
echo "  2. Fill in frontend/.env with your Firebase web config values"
echo "  3. Complete any ACTION REQUIRED steps above"
echo "  4. Then run: ./scripts/start.sh"
