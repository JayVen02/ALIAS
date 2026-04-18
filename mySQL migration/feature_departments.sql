-- FEATURE: Department Management
-- Purpose: Organizes inventory items and users by department (e.g., Health, Engineering, ICT).

USE alias_db;

CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(255)
);

-- Link items to departments
ALTER TABLE inventory_items ADD COLUMN department_id INT;
ALTER TABLE inventory_items ADD FOREIGN KEY (department_id) REFERENCES departments(id);

-- Link users to departments
ALTER TABLE users ADD COLUMN department_id INT;
ALTER TABLE users ADD FOREIGN KEY (department_id) REFERENCES departments(id);

-- Seed initial departments
INSERT IGNORE INTO departments (name) VALUES ('HEALTH'), ('ENGINEERING'), ('ICT'), ('ADMIN');
