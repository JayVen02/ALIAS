-- ======================================================
-- ALIAS MASTER DATABASE MIGRATION
-- Project: Alubijid Local Inventory and Audit System
-- Description: One-stop setup for the entire ALIAS system.
-- ======================================================

/*
  ------------------------------------------------------
  BEGINNER'S GUIDE: HOW TO USE THIS FILE
  ------------------------------------------------------
  
  1. HOW TO RUN THIS FILE (Terminal Command):
     Open your terminal and run:
     mysql -u adminAlias -ppasswordadmin alias_db < "mySQL migration/DATABASE_MASTER.sql"

  2. MANUAL EXAMPLES (If you want to add data manually):
     
     -- To add a New Category:
     INSERT INTO categories (name) VALUES ('ELECTRONICS');

     -- To add a New User (Staff):
     INSERT INTO users (username, password, role) VALUES ('staff_joven', 'pass123', 'staff');

  3. TROUBLESHOOTING:
     - Error 1045 (Access Denied): Double check your password! 
       It should be: passwordadmin
     - Database Not Found: This script will create 'alias_db' for you automatically.
  ------------------------------------------------------
*/

CREATE DATABASE IF NOT EXISTS alias_db;
USE alias_db;

-- ------------------------------------------------------
-- PHASE 1: CORE INVENTORY SYSTEM
-- Purpose: Basic structure for items, categories, and subcategories.
-- ------------------------------------------------------

-- 1. Categories
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Subcategories
CREATE TABLE IF NOT EXISTS subcategories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE (name, category_id)
);

-- 3. Inventory Items
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

-- Seed Phase 1 Data Example
INSERT IGNORE INTO categories (name) VALUES 
('OFFICE SUPPLIES'), ('DRUGS & MEDICINES'), ('ICT EQUIPMENT'), 
('FURNITURE & FIXTURES'), ('VEHICLE & SPARE PARTS'), ('CONSTRUCTION MATERIALS');

INSERT IGNORE INTO subcategories (name, category_id) VALUES
('STATIONERY', (SELECT id FROM categories WHERE name='OFFICE SUPPLIES')),
('ANTIBIOTICS', (SELECT id FROM categories WHERE name='DRUGS & MEDICINES')),
('LAPTOPS', (SELECT id FROM categories WHERE name='ICT EQUIPMENT')),
('TABLES', (SELECT id FROM categories WHERE name='FURNITURE & FIXTURES')),
('TIRES', (SELECT id FROM categories WHERE name='VEHICLE & SPARE PARTS')),
('CEMENT', (SELECT id FROM categories WHERE name='CONSTRUCTION MATERIALS'));


-- ------------------------------------------------------
-- PHASE 2: USER MANAGEMENT & PROFILES
-- Purpose: Authentication, Profile fields, and Role-Based Access.
-- ------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    age INT,
    birthdate DATE,
    address TEXT,
    contact_number VARCHAR(50),
    skills TEXT,
    work_experience TEXT,
    profile_picture VARCHAR(512),
    role ENUM('admin', 'staff', 'viewer') DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Admin User (Password: passwordadmin)
INSERT IGNORE INTO users (username, password, role) 
VALUES ('admin', 'passwordadmin', 'admin');


-- ------------------------------------------------------
-- PHASE 3: ADVANCED FEATURES
-- Purpose: Audit logging, Departments, and File Attachments.
-- ------------------------------------------------------

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(255)
);

-- Link system to departments
ALTER TABLE inventory_items ADD COLUMN department_id INT;
ALTER TABLE inventory_items ADD FOREIGN KEY (department_id) REFERENCES departments(id);
ALTER TABLE users ADD COLUMN department_id INT;
ALTER TABLE users ADD FOREIGN KEY (department_id) REFERENCES departments(id);

-- 2. Audit Logs (Transaction Tracking)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    user_id INT NOT NULL,
    action_type ENUM('CREATE', 'UPDATE', 'DELETE', 'QUANTITY_ADJUST') NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 3. File Attachments
CREATE TABLE IF NOT EXISTS item_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
);

-- Seed Phase 3 Data
INSERT IGNORE INTO departments (name) VALUES ('HEALTH'), ('ENGINEERING'), ('ICT'), ('ADMIN');

-- ======================================================
-- MIGRATION COMPLETE
-- ======================================================

/*
  ------------------------------------------------------
  INCREMENTAL UPDATES (For existing databases)
  ------------------------------------------------------
  If you already have the database but are missing the 
  new Profile fields, run these commands:

  USE alias_db;
  ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS email VARCHAR(255),
  ADD COLUMN IF NOT EXISTS full_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS age INT,
  ADD COLUMN IF NOT EXISTS birthdate DATE,
  ADD COLUMN IF NOT EXISTS address TEXT,
  ADD COLUMN IF NOT EXISTS contact_number VARCHAR(50),
  ADD COLUMN IF NOT EXISTS skills TEXT,
  ADD COLUMN IF NOT EXISTS work_experience TEXT,
  ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(512),
  ADD COLUMN IF NOT EXISTS role ENUM('admin', 'staff', 'viewer') DEFAULT 'staff';
  ------------------------------------------------------
*/
