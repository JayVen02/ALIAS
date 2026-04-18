-- FEATURE: Inventory Item Attachments
-- Purpose: Allows uploading and linking images or documents (PDFs, receipts) to specific inventory items.

USE alias_db;

CREATE TABLE IF NOT EXISTS item_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
);

-- Example Query to get all images for an item:
-- SELECT * FROM item_attachments WHERE item_id = 5 AND file_type LIKE 'image%';
