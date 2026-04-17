CREATE DATABASE IF NOT EXISTS alias_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE alias_db;

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    role          ENUM('admin','inventory_staff') NOT NULL DEFAULT 'inventory_staff',
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    item_code    VARCHAR(50)  NOT NULL UNIQUE,
    category     VARCHAR(100) NOT NULL,
    subcategory  VARCHAR(100) NOT NULL,
    name         VARCHAR(200) NOT NULL,
    unit_measure VARCHAR(50)  DEFAULT 'unit',
    unit_value   DECIMAL(15,2) DEFAULT 0,
    system_qty   INT NOT NULL DEFAULT 0,
    is_deleted   BOOLEAN DEFAULT FALSE,
    created_by   INT NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS history (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT NOT NULL,
    action    VARCHAR(500) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
