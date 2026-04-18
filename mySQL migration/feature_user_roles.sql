-- FEATURE: Role-Based Access Control (RBAC)
-- Purpose: Adds a 'role' column to users to distinguish between Admin, Staff, and Viewers.

USE alias_db;

-- 1. Add role column with a default value
ALTER TABLE users ADD COLUMN role ENUM('admin', 'staff', 'viewer') DEFAULT 'staff';

-- 2. Update existing admin to have 'admin' role
UPDATE users SET role = 'admin' WHERE username = 'admin';

-- 3. (Optional) Example of adding a new staff user
-- INSERT IGNORE INTO users (username, password, role) VALUES ('staff_user', 'hashed_password_here', 'staff');
