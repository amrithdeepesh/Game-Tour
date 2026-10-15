-- Empty schema for the tournament application.
-- The Python backend also applies safe migrations and provisions the configured admin.

CREATE DATABASE IF NOT EXISTS game_tour_ds
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE game_tour_ds;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(40) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL,
    faction VARCHAR(80) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role ENUM('admin', 'student') NOT NULL DEFAULT 'student',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tournaments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL DEFAULT '',
    starts_at DATETIME NULL,
    ends_at DATETIME NULL,
    registration_closes_at DATETIME NULL,
    points_first INT NOT NULL DEFAULT 10,
    points_second INT NOT NULL DEFAULT 7,
    points_third INT NOT NULL DEFAULT 5,
    points_participation INT NOT NULL DEFAULT 1,
    status ENUM('upcoming', 'active', 'completed')
        NOT NULL DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS games (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tournament_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT '',
    rounds INT NOT NULL DEFAULT 1,
    starts_at DATETIME NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    venue VARCHAR(160) NOT NULL,
    capacity INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (tournament_id, starts_at),
    CONSTRAINT fk_game_tournament
        FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS game_choices (
    user_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, game_id),
    INDEX (game_id),
    CONSTRAINT fk_choice_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_choice_game FOREIGN KEY (game_id) REFERENCES games(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id BIGINT NOT NULL,
    round_number INT NOT NULL,
    participant_id BIGINT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    points_awarded INT NOT NULL DEFAULT 0,
    result_status ENUM('played', 'no_show', 'disqualified')
        NOT NULL DEFAULT 'played',
    placement INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_result_game_round_participant
        (game_id, round_number, participant_id),
    INDEX (game_id, placement),
    CONSTRAINT fk_result_game FOREIGN KEY (game_id) REFERENCES games(id),
    CONSTRAINT fk_result_user FOREIGN KEY (participant_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sessions (
    token_hash CHAR(64) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    expires_at DATETIME NOT NULL,
    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS result_audit (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id BIGINT NOT NULL,
    round_number INT NOT NULL,
    participant_id BIGINT NOT NULL,
    actor_user_id BIGINT NULL,
    action VARCHAR(20) NOT NULL,
    before_values JSON NULL,
    after_values JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (game_id, created_at)
) ENGINE=InnoDB;
