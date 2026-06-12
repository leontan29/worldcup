#!/usr/bin/env bash
set -euo pipefail

# Load 2022 World Cup data from CSVs into the database.
# Run from any directory; paths are resolved relative to this script.

DIR="$(cd "$(dirname "$0")" && pwd)"

source "$DIR/../../.env"

DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-worldcup}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD not set}"
DB_NAME="${DB_NAME:-worldcup}"

MYSQL="mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME --local-infile=1"

echo "[load] Loading teams..."
$MYSQL <<SQL
LOAD DATA LOCAL INFILE '$DIR/teams.csv'
INTO TABLE teams
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, country_code, group_name, fifa_ranking, coach);
SQL

echo "[load] Loading venues..."
$MYSQL <<SQL
LOAD DATA LOCAL INFILE '$DIR/venues.csv'
INTO TABLE venues
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, city, country, capacity);
SQL

echo "[load] Loading players..."
$MYSQL <<SQL
LOAD DATA LOCAL INFILE '$DIR/players.csv'
INTO TABLE players
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, team_id, name, position, jersey_number, goals, assists);
SQL

echo "[load] Loading matches..."
$MYSQL <<SQL
LOAD DATA LOCAL INFILE '$DIR/matches.csv'
INTO TABLE matches
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, match_date, stage, group_name, home_team_id, away_team_id, venue_id, status, home_score, away_score);
SQL

echo "[load] Creating admin user..."
$MYSQL <<'SQL'
INSERT INTO users (username, email, password_hash, is_admin)
VALUES ('admin', 'leontann29@gmail.com', '$2b$12$hMHSUt/L7o8.4NF25PtQo.6am3wMjisGFQem/20VMQS7AabTi2wfe', 1)
ON DUPLICATE KEY UPDATE email = 'leontann29@gmail.com', password_hash = '$2b$12$hMHSUt/L7o8.4NF25PtQo.6am3wMjisGFQem/20VMQS7AabTi2wfe', is_admin = 1;
SQL

echo "[load] Done. $(mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -se 'SELECT COUNT(*) FROM matches') matches loaded."
