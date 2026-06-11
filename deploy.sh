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

# -- Detect package manager ------------------------------------------------
if command -v apt-get >/dev/null; then
    PKG_INSTALL="sudo apt-get install -y"
    PKG_UPDATE="sudo apt-get update -qq"
elif command -v dnf >/dev/null; then
    PKG_INSTALL="sudo dnf install -y"
    PKG_UPDATE="sudo dnf check-update -q || true"
elif command -v yum >/dev/null; then
    PKG_INSTALL="sudo yum install -y"
    PKG_UPDATE="sudo yum check-update -q || true"
elif command -v brew >/dev/null; then
    PKG_INSTALL="brew install"
    PKG_UPDATE="brew update"
else
    error "No supported package manager found (apt/dnf/yum/brew)"
fi

_ensure() {
    local cmd="$1" pkg="${2:-$1}"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        info "Installing $pkg..."
        [[ -z "${_PKG_UPDATED:-}" ]] && { $PKG_UPDATE; _PKG_UPDATED=1; }
        $PKG_INSTALL "$pkg"
    fi
}

# -- Install prerequisites -------------------------------------------------
_ensure python3
_ensure pip python3-pip

# Node/npm: use NodeSource for a recent version on apt systems
if ! command -v node >/dev/null 2>&1; then
    info "Installing Node.js..."
    if command -v apt-get >/dev/null; then
        [[ -z "${_PKG_UPDATED:-}" ]] && { $PKG_UPDATE; _PKG_UPDATED=1; }
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
        sudo apt-get install -y nodejs
    elif command -v brew >/dev/null; then
        brew install node
    else
        $PKG_INSTALL nodejs npm
    fi
fi

if ! command -v mysql >/dev/null 2>&1; then
    info "Installing MySQL client..."
    [[ -z "${_PKG_UPDATED:-}" ]] && { $PKG_UPDATE; _PKG_UPDATED=1; }
    if command -v apt-get >/dev/null; then
        $PKG_INSTALL default-mysql-client || $PKG_INSTALL mysql-client
    elif command -v brew >/dev/null; then
        brew install mysql-client && export PATH="/usr/local/opt/mysql-client/bin:$PATH"
    else
        $PKG_INSTALL mysql
    fi
fi

if ! command -v redis-cli >/dev/null 2>&1; then
    info "Installing Redis..."
    [[ -z "${_PKG_UPDATED:-}" ]] && { $PKG_UPDATE; _PKG_UPDATED=1; }
    if command -v apt-get >/dev/null; then
        $PKG_INSTALL redis-server
    elif command -v brew >/dev/null; then
        brew install redis
    else
        $PKG_INSTALL redis
    fi
fi

# Verify all required tools are now present
for cmd in python3 pip node npm mysql redis-cli; do
    command -v "$cmd" >/dev/null || error "$cmd still not found after install attempt"
done

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
