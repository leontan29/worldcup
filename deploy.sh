#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# WorldCup Hub — deployment script
# Usage: ./deploy.sh [--update|--stop|--restart|--logs]
# ---------------------------------------------------------------------------

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$APP_DIR/backend"
FRONTEND="$APP_DIR/frontend"
ENV_FILE="$BACKEND/.env"
PID_FILE="$APP_DIR/worldcup.pid"
LOG_FILE="$APP_DIR/worldcup.log"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

GUNICORN_BIN="$(command -v gunicorn 2>/dev/null || echo "$HOME/.local/bin/gunicorn")"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_start() {
    source "$ENV_FILE"
    info "Starting gunicorn..."
    cd "$BACKEND"
    nohup "$GUNICORN_BIN" wsgi:app --config gunicorn.conf.py \
        >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        info "Started (PID $(cat "$PID_FILE")). Logs: $LOG_FILE"
    else
        error "Failed to start — check $LOG_FILE"
    fi
}

_stop() {
    if [[ -f "$PID_FILE" ]]; then
        PID="$(cat "$PID_FILE")"
        if kill -0 "$PID" 2>/dev/null; then
            info "Stopping PID $PID..."
            kill "$PID"
            rm -f "$PID_FILE"
        else
            warn "Process $PID not running, removing stale PID file"
            rm -f "$PID_FILE"
        fi
    else
        warn "No PID file found — app may not be running"
    fi
}

# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

case "${1:-}" in
    --stop)
        _stop; exit 0 ;;
    --restart)
        _stop; sleep 1; _start; exit 0 ;;
    --logs)
        tail -f "$LOG_FILE"; exit 0 ;;
    --update)
        info "Pulling latest code..."
        git -C "$APP_DIR" pull

        info "Installing Python deps..."
        pip install -r "$BACKEND/requirements.txt" -q

        info "Rebuilding frontend..."
        cd "$FRONTEND" && npm install --silent && npm run build && cd "$APP_DIR"

        _stop; sleep 1; _start
        exit 0 ;;
esac

# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------

command -v python3  >/dev/null || error "python3 not found"
command -v pip      >/dev/null || error "pip not found"
command -v node     >/dev/null || error "node not found"
command -v npm      >/dev/null || error "npm not found"
command -v mysql    >/dev/null || error "mysql client not found"
command -v redis-cli >/dev/null || error "redis-cli not found"

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
info "Installing Node dependencies and building frontend..."
cd "$FRONTEND" && npm install --silent && npm run build && cd "$APP_DIR"

# -- Start -----------------------------------------------------------------
_start

echo
info "Deployment complete. App on port 8080."
info "Commands:"
info "  ./deploy.sh --update   pull + rebuild + restart"
info "  ./deploy.sh --restart  restart"
info "  ./deploy.sh --stop     stop"
info "  ./deploy.sh --logs     tail logs"
