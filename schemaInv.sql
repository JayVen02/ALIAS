-- ALIAS Inventory Schema
-- alias_db

CREATE DATABASE IF NOT EXISTS alias_db;
USE alias_db;

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS subcategories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE (name, category_id)
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    subcategory_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    article VARCHAR(255),
    stock_number VARCHAR(100),
    unit_of_measure VARCHAR(100),
    unit_value DECIMAL(15, 2),
    balance_per_card INT,
    on_hand_per_count INT,
    shortage_quantity INT,
    overage_value DECIMAL(15, 2),
    remarks TEXT,
    date_created DATE NOT NULL DEFAULT (CURDATE()),
    date_updated DATE NOT NULL DEFAULT (CURDATE()),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
);

-- Seed default categories
INSERT IGNORE INTO categories (name) VALUES ('SUPPLY'), ('VEHICLE');

-- Seed default subcategories
INSERT IGNORE INTO subcategories (name, category_id)
VALUES
  ('EMERGENCY', (SELECT id FROM categories WHERE name='SUPPLY')),
  ('VETERINARY', (SELECT id FROM categories WHERE name='SUPPLY')),
  ('MEDICAL',   (SELECT id FROM categories WHERE name='SUPPLY')),
  ('VEHICLE',   (SELECT id FROM categories WHERE name='VEHICLE'));
