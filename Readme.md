# Alubijid Local Inventory & Audit System (ALIAS)

ALIAS is a modern, high-fidelity web application designed for the Alubijid Local Government Unit to manage inventory tracking and generate comprehensive physical count audits.

## System Features

- **Inventory Tracking**: Easily add, update, and manage inventory items with automatic history tracking.
- **Audit Reports**: Instantly create professional PDF reports for physical counts.
- **Secure Access**: Login system using official email addresses with Admin and Staff permissions.
- **Account Management**: Admins can create and manage staff accounts from a simple dashboard.
- **User Profiles**: Personal profiles where staff can update their info and profile picture.

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

```bash
ALIAS/
├── app.py              # Application entry point and factory
├── config.py           # Environment-based configuration
├── extensions.py       # Shared Flask extensions (MySQL)
├── routes/             # routes for pages (Auth, Pages, API, PDF)
├── services/           # logic and database queries
├── templates/          # Jinja2 HTML templates and base layouts
├── static/             # Design system (CSS) and modular JS
└── pdf_generator.py    # Core logic for PDF audit reports
```

### Key Modules
- **Routes**: Separates concerns into Authentication, Web Pages, Inventory API, and User Management.
- **Services**: Centralizes database access to ensure consistency and prevent SQL injection.
- **Static**: Organized into CSS design tokens and modular JavaScript handlers.
- **Templates**: Uses a unified layout system (`base.html`).

---
*Developed for ITCC42 - Alubijid Local Inventory and Audit System Project.*
