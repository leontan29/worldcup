#!/usr/bin/env bash
# Stops MySQL and Redis background processes.
set -euo pipefail

echo "==> Stopping MySQL..."
if sudo mysqladmin ping --silent 2>/dev/null; then
  sudo mysqladmin shutdown
  echo "    MySQL stopped."
else
  echo "    MySQL was not running."
fi

echo "==> Stopping Redis..."
if redis-cli ping 2>/dev/null | grep -q PONG; then
  redis-cli shutdown nosave 2>/dev/null || true
  echo "    Redis stopped."
else
  echo "    Redis was not running."
fi

echo "==> Done."
