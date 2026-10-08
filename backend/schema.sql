-- MySQL 8 schema for durable tournament data (not required to run the demo).
CREATE DATABASE IF NOT EXISTS game_tour_ds CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE game_tour_ds;

CREATE TABLE IF NOT EXISTS participants (
  student_id VARCHAR(20) PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  faction VARCHAR(80) NOT NULL,
  game VARCHAR(80) NOT NULL,
  points INT NOT NULL DEFAULT 0,
  wins INT NOT NULL DEFAULT 0,
  status ENUM('Active','Withdrawn') NOT NULL DEFAULT 'Active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_leaderboard (points DESC, wins DESC)
);

CREATE TABLE IF NOT EXISTS matches (
  match_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(160) NOT NULL,
  game VARCHAR(80) NOT NULL,
  arena VARCHAR(100) NOT NULL,
  starts_at DATETIME NOT NULL,
  ends_at DATETIME NOT NULL,
  status ENUM('Upcoming','In progress','Completed') NOT NULL DEFAULT 'Upcoming',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_schedule (arena, starts_at, ends_at)
);

CREATE TABLE IF NOT EXISTS match_participants (
  match_id BIGINT NOT NULL,
  student_id VARCHAR(20) NOT NULL,
  score INT NOT NULL DEFAULT 0,
  result ENUM('Pending','Win','Loss','Draw') NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (match_id, student_id),
  FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES participants(student_id) ON DELETE CASCADE
);
