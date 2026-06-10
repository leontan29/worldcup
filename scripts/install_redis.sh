#!/usr/bin/env bash
# Installs Redis on Ubuntu/Debian and starts it as a background process.
# Works without systemctl (container-friendly). Safe to re-run (idempotent).
set -euo pipefail

echo "==> Installing Redis..."
sudo apt-get update -qq
sudo apt-get install -y redis-server

echo "==> Starting Redis (no systemctl)..."
# Kill any existing instance first
pkill redis-server 2>/dev/null || true
sleep 1

redis-server --daemonize yes \
  --bind 127.0.0.1 \
  --port 6379 \
  --logfile /tmp/redis.log \
  --pidfile /tmp/redis.pid

# Wait for Redis to be ready
echo -n "==> Waiting for Redis"
for i in $(seq 1 10); do
  if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo " ready."
    break
  fi
  echo -n "."
  sleep 1
done

echo "==> Done. Connection details:"
echo "    REDIS_URL=redis://127.0.0.1:6379/0"
echo ""
echo "    Test: redis-cli ping  (should return PONG)"
echo ""
echo "NOTE: Redis is running as a background process (not a service)."
echo "      It will stop when this machine reboots. Re-run this script to restart it."
echo "      Or start it manually: redis-server --daemonize yes --bind 127.0.0.1 --port 6379"
