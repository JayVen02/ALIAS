-- =====================================
-- ALIAS DATABASE
-- File: alias_db.sql
-- =====================================

CREATE DATABASE IF NOT EXISTS alias_db;
USE alias_db;

-- =====================================
-- USERS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- =====================================
-- DEFAULT ADMIN ACCOUNT
-- =====================================
INSERT INTO users (username, password)
VALUES ('admin', 'admin123');