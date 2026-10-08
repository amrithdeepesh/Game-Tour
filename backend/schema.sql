-- Safe, additive MySQL tables used by the tournament app.
-- Existing unprefixed project tables are left untouched.
CREATE DATABASE IF NOT EXISTS game_tour_ds
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE game_tour_ds;

CREATE TABLE IF NOT EXISTS tournament_games (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  game_id VARCHAR(20) NULL UNIQUE,
  name VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(80) NOT NULL DEFAULT 'Other',
  venue VARCHAR(120) NOT NULL DEFAULT 'Main Arena',
  description VARCHAR(500) NOT NULL DEFAULT '',
  status VARCHAR(20) NOT NULL DEFAULT 'Open',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tournament_participants (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(20) NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  faction VARCHAR(100) NOT NULL DEFAULT '',
  game_id VARCHAR(20) NOT NULL,
  email VARCHAR(254) NOT NULL DEFAULT '',
  notes TEXT NOT NULL,
  points INT NOT NULL DEFAULT 0,
  wins INT NOT NULL DEFAULT 0,
  status ENUM('Pending','Active','Declined') NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tournament_players_game (game_id, status),
  INDEX idx_tournament_players_rank (game_id, points DESC, wins DESC),
  CONSTRAINT fk_tournament_participant_game FOREIGN KEY (game_id)
    REFERENCES tournament_games(game_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tournament_matches (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(160) NOT NULL,
  game_id VARCHAR(20) NOT NULL,
  arena VARCHAR(120) NOT NULL,
  starts_hour TINYINT UNSIGNED NOT NULL,
  ends_hour TINYINT UNSIGNED NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Upcoming',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tournament_schedule (game_id, starts_hour),
  CONSTRAINT fk_tournament_match_game FOREIGN KEY (game_id)
    REFERENCES tournament_games(game_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tournament_results (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  result_id VARCHAR(20) NULL UNIQUE,
  game_id VARCHAR(20) NOT NULL,
  match_title VARCHAR(160) NOT NULL,
  winner_id VARCHAR(20) NOT NULL,
  loser_id VARCHAR(20) NOT NULL,
  winner_score INT NOT NULL,
  loser_score INT NOT NULL,
  played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tournament_results_game (game_id, played_at),
  CONSTRAINT fk_tournament_result_game FOREIGN KEY (game_id)
    REFERENCES tournament_games(game_id),
  CONSTRAINT fk_tournament_result_winner FOREIGN KEY (winner_id)
    REFERENCES tournament_participants(student_id),
  CONSTRAINT fk_tournament_result_loser FOREIGN KEY (loser_id)
    REFERENCES tournament_participants(student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
