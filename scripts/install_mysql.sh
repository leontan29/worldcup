#!/usr/bin/env bash
# Installs MySQL 8.0 on Ubuntu/Debian and creates the worldcup database + user.
# Works without systemctl (container-friendly). Safe to re-run (idempotent).
set -euo pipefail

DB_NAME="${DB_NAME:-worldcup}"
DB_USER="${DB_USER:-worldcup}"
DB_PASSWORD="${DB_PASSWORD:-worldcup_dev}"

echo "==> Installing MySQL 8.0..."
sudo apt-get update -qq
sudo apt-get install -y mysql-server

echo "==> Starting MySQL (no systemctl)..."
if sudo mysqladmin ping --silent 2>/dev/null; then
  echo "    MySQL already running, skipping."
else
  sudo mkdir -p /var/run/mysqld
  sudo chown mysql:mysql /var/run/mysqld
  sudo -u mysql mysqld_safe --skip-networking=0 --daemonize || true

  echo -n "    Waiting"
  for i in $(seq 1 30); do
    if sudo mysqladmin ping --silent 2>/dev/null; then
      echo " ready."
      break
    fi
    echo -n "."
    sleep 1
  done
fi

echo "==> Creating database and user..."
sudo mysql -e "
  CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
  GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
  FLUSH PRIVILEGES;
"

echo "==> Done. Connection details:"
echo "    Host:     127.0.0.1"
echo "    Port:     3306"
echo "    Database: ${DB_NAME}"
echo "    User:     ${DB_USER}"
echo "    Password: ${DB_PASSWORD}"
echo ""
echo "    Test: mysql -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} -e 'SELECT 1'"
echo ""
echo "NOTE: MySQL is running as a background process (not a service)."
echo "      It will stop when this machine reboots. Re-run this script to restart it."
echo "      Or start it manually: sudo -u mysql mysqld_safe --skip-networking=0 --daemonize"
