CREATE DATABASE IF NOT EXISTS worldcup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE worldcup;

-- Tables

CREATE TABLE IF NOT EXISTS teams (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    group_name CHAR(1) NOT NULL,
    fifa_ranking SMALLINT UNSIGNED NOT NULL,
    coach VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    capacity INT UNSIGNED NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    failed_login_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    favorite_team_id INT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT fk_users_team FOREIGN KEY (favorite_team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS players (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    team_id INT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    position ENUM('GK','DEF','MID','FWD') NOT NULL,
    jersey_number TINYINT UNSIGNED NOT NULL,
    goals SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    assists SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT fk_players_team FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    home_team_id INT UNSIGNED NULL,
    away_team_id INT UNSIGNED NULL,
    venue_id INT UNSIGNED NOT NULL,
    match_date DATETIME NOT NULL,
    stage ENUM('group','round_of_32','round_of_16','quarterfinal','semifinal','third_place','final') NOT NULL,
    status ENUM('scheduled','live','completed','cancelled') NOT NULL DEFAULT 'scheduled',
    home_score TINYINT UNSIGNED NULL,
    away_score TINYINT UNSIGNED NULL,
    winner_team_id INT UNSIGNED NULL,
    group_name CHAR(1) NULL,
    CONSTRAINT fk_matches_home FOREIGN KEY (home_team_id) REFERENCES teams(id),
    CONSTRAINT fk_matches_away FOREIGN KEY (away_team_id) REFERENCES teams(id),
    CONSTRAINT fk_matches_venue FOREIGN KEY (venue_id) REFERENCES venues(id),
    CONSTRAINT fk_matches_winner FOREIGN KEY (winner_team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS match_events (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    match_id INT UNSIGNED NOT NULL,
    player_id INT UNSIGNED NOT NULL,
    event_type ENUM('goal','assist','yellow_card','red_card','substitution') NOT NULL,
    minute TINYINT UNSIGNED NOT NULL,
    CONSTRAINT fk_events_match FOREIGN KEY (match_id) REFERENCES matches(id),
    CONSTRAINT fk_events_player FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    match_id INT UNSIGNED NOT NULL,
    home_score TINYINT UNSIGNED NOT NULL,
    away_score TINYINT UNSIGNED NOT NULL,
    points_earned TINYINT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_predictions UNIQUE (user_id, match_id),
    CONSTRAINT fk_pred_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_pred_match FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE TABLE IF NOT EXISTS user_activity (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS session_audit (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    session_id CHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    destroyed_at DATETIME NULL,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes

CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_stage ON matches(stage);
CREATE INDEX idx_teams_group ON teams(group_name);
CREATE INDEX idx_predictions_user ON predictions(user_id);
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_leaderboard ON predictions(user_id, points_earned);
CREATE INDEX idx_activity_user ON user_activity(user_id);
CREATE INDEX idx_activity_created ON user_activity(created_at);

-- Trigger: update player goal/assist counts when match_events is inserted

DELIMITER $$

CREATE TRIGGER update_player_stats
AFTER INSERT ON match_events
FOR EACH ROW
BEGIN
    IF NEW.event_type = 'goal' THEN
        UPDATE players SET goals = goals + 1 WHERE id = NEW.player_id;
    ELSEIF NEW.event_type = 'assist' THEN
        UPDATE players SET assists = assists + 1 WHERE id = NEW.player_id;
    END IF;
END$$

-- Stored procedure: score all predictions for a completed match

CREATE PROCEDURE calculate_prediction_points(IN p_match_id INT UNSIGNED)
BEGIN
    DECLARE v_home TINYINT UNSIGNED;
    DECLARE v_away TINYINT UNSIGNED;

    SELECT home_score, away_score INTO v_home, v_away
    FROM matches WHERE id = p_match_id;

    UPDATE predictions
    SET points_earned = CASE
        WHEN home_score = v_home AND away_score = v_away THEN 3
        WHEN (home_score > away_score AND v_home > v_away)
          OR (home_score < away_score AND v_home < v_away)
          OR (home_score = away_score AND v_home = v_away) THEN 1
        ELSE 0
    END
    WHERE match_id = p_match_id;
END$$

-- Stored procedure: group standings with tie-breakers

CREATE PROCEDURE get_group_standings(IN p_group CHAR(1))
BEGIN
    SELECT
        t.id,
        t.name,
        t.country_code,
        t.fifa_ranking,
        COUNT(m.id) AS matches_played,
        SUM(CASE
            WHEN (m.home_team_id = t.id AND m.home_score > m.away_score)
              OR (m.away_team_id = t.id AND m.away_score > m.home_score) THEN 1 ELSE 0
        END) AS wins,
        SUM(CASE WHEN m.home_score = m.away_score THEN 1 ELSE 0 END) AS draws,
        SUM(CASE
            WHEN (m.home_team_id = t.id AND m.home_score < m.away_score)
              OR (m.away_team_id = t.id AND m.away_score < m.home_score) THEN 1 ELSE 0
        END) AS losses,
        SUM(CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE m.away_score END) AS goals_for,
        SUM(CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END) AS goals_against,
        SUM(CASE WHEN m.home_team_id = t.id THEN m.home_score - m.away_score
                 ELSE m.away_score - m.home_score END) AS goal_difference,
        SUM(CASE
            WHEN (m.home_team_id = t.id AND m.home_score > m.away_score)
              OR (m.away_team_id = t.id AND m.away_score > m.home_score) THEN 3
            WHEN m.home_score = m.away_score THEN 1
            ELSE 0
        END) AS points
    FROM teams t
    LEFT JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
        AND m.status = 'completed'
        AND m.stage = 'group'
    WHERE t.group_name = p_group
    GROUP BY t.id, t.name, t.country_code, t.fifa_ranking
    ORDER BY points DESC, goal_difference DESC, goals_for DESC, t.fifa_ranking ASC;
END$$

DELIMITER ;
