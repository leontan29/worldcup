#!/usr/bin/env bash
# Starts MySQL and Redis as background processes (no systemctl).
# Run this after a reboot. Assumes install_mysql.sh and install_redis.sh have been run.
set -euo pipefail

# --- MySQL ---
echo "==> Starting MySQL..."
if sudo mysqladmin ping --silent 2>/dev/null; then
  echo "    MySQL already running, skipping."
else
  # Wait for any lingering mysqld process to fully exit before starting
  echo -n "    Waiting for clean stop"
  for i in $(seq 1 15); do
    if ! pgrep -x mysqld > /dev/null 2>&1; then
      echo " clear."
      break
    fi
    echo -n "."
    sleep 1
  done

  sudo mkdir -p /var/run/mysqld
  sudo chown mysql:mysql /var/run/mysqld
  sudo -u mysql mysqld_safe --skip-networking=0 --daemonize || true

  echo -n "    Waiting for ready"
  for i in $(seq 1 30); do
    if sudo mysqladmin ping --silent 2>/dev/null; then
      echo " ready."
      break
    fi
    echo -n "."
    sleep 1
  done
fi

# --- Redis ---
echo "==> Starting Redis..."
if redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "    Redis already running, skipping."
else
  redis-server --daemonize yes \
    --bind 127.0.0.1 \
    --port 6379 \
    --logfile /tmp/redis.log \
    --pidfile /tmp/redis.pid

  echo -n "    Waiting"
  for i in $(seq 1 10); do
    if redis-cli ping 2>/dev/null | grep -q PONG; then
      echo " ready."
      break
    fi
    echo -n "."
    sleep 1
  done
fi

echo "==> All services up."
