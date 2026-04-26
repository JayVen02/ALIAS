# Alubijid Local Inventory & Audit System (ALIAS)

ALIAS is a modern, high-fidelity web application designed for the Alubijid Local Government Unit to manage inventory tracking and generate comprehensive physical count audits.

## Key Features

- **Unified Inventory Management**: Track articles, subcategories, and stock levels across multiple departments.
- **Dynamic Audit System**: Generate real-time audit reports for specific categories and export them as professional PDFs.
- **Role-Based Access**: Secure login system with email-based authentication and department-specific tracking.
- **Transaction History**: Comprehensive logging of all inventory changes for full accountability.

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: Vanilla JS, CSS3, HTML5
- **Reports**: ReportLab (PDF Generation)
- **Asset Management**: Cloudinary (Cloud-hosted branding assets)

## Setup & Installation

### 1. Clone & Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install flask flask-mysqldb python-dotenv reportlab
```

### 3. Database Migration
ALIAS uses a master migration script to set up the entire database structure and seed data.
```bash
# Connect to your MySQL and run the master script
mysql -u your_user -p alias_db < "mySQL migration/DATABASE_MASTER.sql"
```

### 4. Configuration
Create a `.env` file in the root directory with your credentials:
```env
MYSQL_HOST=localhost
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DB=alias_db
SECRET_KEY=your_secure_random_key
```

### 5. Run the Application
```bash
python app.py
```

## Project Structure
- `/templates`: HTML fragments and layout templates.
- `/static`: Design system (CSS) and interactivity (JS).
- `/mySQL migration`: Database schema and master migration scripts.
- `app.py`: Main Flask server and API routes.
- `pdf_generator.py`: Core logic for professional PDF reports.

---
*Developed for ITCC42 - Alubijid Local Inventory and Audit System Project.*
