#!/usr/bin/env bash
set -euo pipefail

echo "Enabling promiscuous mode on eth0..."
if command -v sudo >/dev/null 2>&1; then
  sudo ip link set eth0 promisc on
else
  ip link set eth0 promisc on
fi

echo "Installing backend dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ -f "frontend/package.json" ]; then
  echo "Installing frontend dependencies..."
  if command -v npm >/dev/null 2>&1; then
    (cd frontend && npm install)
  else
    echo "npm not found. Skipping frontend dependency install."
  fi
fi

echo "Setup complete."
