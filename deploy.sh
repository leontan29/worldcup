#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# WorldCup Hub — deployment script
# Usage: ./deploy.sh [--update]
#   (no flag)  : fresh install
#   --update   : pull latest code, rebuild frontend, restart service
# ---------------------------------------------------------------------------

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="worldcup"
BACKEND="$APP_DIR/backend"
FRONTEND="$APP_DIR/frontend"
ENV_FILE="$BACKEND/.env"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

# ---------------------------------------------------------------------------
# Update-only path
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--update" ]]; then
    info "Pulling latest code..."
    git -C "$APP_DIR" pull

    info "Rebuilding frontend..."
    cd "$FRONTEND" && npm install --silent && npm run build

    info "Installing Python deps..."
    pip install -r "$BACKEND/requirements.txt" -q

    info "Restarting service..."
    sudo systemctl restart "$SERVICE_NAME"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 0
fi

# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------

# -- Check prerequisites ---------------------------------------------------
command -v python3 >/dev/null || error "python3 not found"
command -v pip    >/dev/null || error "pip not found"
command -v node   >/dev/null || error "node not found"
command -v npm    >/dev/null || error "npm not found"
command -v mysql  >/dev/null || error "mysql client not found (install mysql-server)"
command -v redis-cli >/dev/null || error "redis-cli not found (install redis-server)"

# -- .env ------------------------------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env not found — copying from .env.example"
    cp "$BACKEND/.env.example" "$ENV_FILE"
    warn "Edit $ENV_FILE before proceeding (DB_PASSWORD, SECRET_KEY, etc.)"
    echo
    read -rp "Press Enter once .env is configured, or Ctrl-C to abort: "
fi

source "$ENV_FILE"

DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-worldcup}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD must be set in .env}"
DB_NAME="${DB_NAME:-worldcup}"

# -- MySQL -----------------------------------------------------------------
info "Setting up MySQL database '$DB_NAME'..."
mysql -h "$DB_HOST" -u root -p \
    -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;
        CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';
        GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'$DB_HOST';
        FLUSH PRIVILEGES;" 2>/dev/null || warn "Root MySQL setup skipped (may already exist)"

info "Applying schema..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$BACKEND/schema.sql"

info "Seeding data..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$BACKEND/seed.sql"

# -- Python ----------------------------------------------------------------
info "Installing Python dependencies..."
pip install -r "$BACKEND/requirements.txt" -q

# -- Frontend --------------------------------------------------------------
info "Installing Node dependencies..."
cd "$FRONTEND" && npm install --silent

info "Building frontend..."
npm run build
cd "$APP_DIR"

# -- Systemd service -------------------------------------------------------
PYTHON_BIN="$(command -v python3)"
GUNICORN_BIN="$(command -v gunicorn || echo "$(dirname "$PYTHON_BIN")/gunicorn")"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
info "Writing systemd service to $SERVICE_FILE..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=WorldCup Hub (Gunicorn)
After=network.target mysql.service redis.service

[Service]
User=$USER
WorkingDirectory=$BACKEND
EnvironmentFile=$ENV_FILE
ExecStart=$GUNICORN_BIN wsgi:app --config gunicorn.conf.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# -- Done ------------------------------------------------------------------
echo
info "Deployment complete."
sudo systemctl status "$SERVICE_NAME" --no-pager
echo
info "App running on port 8080. To check logs: journalctl -u $SERVICE_NAME -f"
info "To update later: ./deploy.sh --update"
