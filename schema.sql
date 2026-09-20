-- NoteShare Database Schema
-- Run once: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS notes_db;
USE notes_db;

CREATE TABLE IF NOT EXISTS users (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email    VARCHAR(120) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(200) NOT NULL,
    subject        VARCHAR(100) NOT NULL,
    filename       VARCHAR(300) NOT NULL,
    user_id        INT NOT NULL,
    upload_date    DATETIME DEFAULT CURRENT_TIMESTAMP,
    download_count INT DEFAULT 0,
    total_rating   INT DEFAULT 0,
    rating_count   INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    note_id      INT NOT NULL,
    user_id      INT NOT NULL,
    comment_text TEXT NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);