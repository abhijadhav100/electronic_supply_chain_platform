# Electronic Supply Chain Platform - Setup & Run Guide

## ✅ MIGRATION COMPLETED: MySQL → PostgreSQL

All files have been updated to use **PostgreSQL** instead of MySQL.

---

## 📋 SYSTEM REQUIREMENTS

- **Python**: 3.10.11 (Already installed on your machine ✓)
- **PostgreSQL**: Installed and running on your machine (verify with: `psql --version`)
- **Virtual Environment**: Recommended (venv)

---

## 🚀 STEP-BY-STEP SETUP & RUN INSTRUCTIONS

### 1. **Verify PostgreSQL is Running**

```bash
# Windows: Check if PostgreSQL service is running
Get-Service postgresql-x64*

# Or connect to PostgreSQL
psql -U postgres -h localhost
```

If not installed, install PostgreSQL from: https://www.postgresql.org/download/windows/

### 2. **Create PostgreSQL Database**

Before running the app, create the database in PostgreSQL:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE electronic_supply_chain_platform;

# List databases to verify
\l

# Exit psql
\q
```

Or create via GUI tools like pgAdmin.

### 3. **Create Virtual Environment**

```bash
# Navigate to project directory
cd d:\electronic_supply_chain_platform\electronic_supply_chain_platform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 4. **Install Dependencies**

```bash
pip install --upgrade pip

# Install from requirements.txt (now with PostgreSQL driver)
pip install -r requirements.txt
```

**What will be installed:**
- Flask 3.0.5 (Web framework)
- psycopg2-binary 2.9.9 (PostgreSQL driver)
- Werkzeug 3.0.1 (WSGI utilities)

### 5. **Initialize Database Schema**

```bash
# Run the database initialization command
flask --app app init-db
```

Expected output:
```
Database initialized successfully.
```

This will:
- Create all tables (user, admin, product, inventory, etc.)
- Create ENUM type for user roles
- Insert demo data (users, categories, suppliers, products)

### 6. **Run the Application**

```bash
# Start the Flask development server
flask --app app run --debug

# Or alternatively:
python app.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 7. **Access the Application**

Open your browser and go to:
```
http://localhost:5000
```

---

## 🔑 DEMO CREDENTIALS

Use these credentials to test different roles:

| Role | Email | Password | Features |
|------|-------|----------|----------|
| **Admin** | admin@electrohub.com | admin123 | Manage users, products, categories, view orders |
| **Supplier** | supplier@electrohub.com | supplier123 | Create/edit products, manage inventory, view orders |
| **Customer** | customer@electrohub.com | customer123 | Browse products, add to cart, checkout, view orders |

---

## 🗄️ DATABASE CONFIGURATION

### Current Configuration (PostgreSQL)

File: `config.py`

```python
DB_HOST = "localhost"        # PostgreSQL server host
DB_PORT = 5432              # PostgreSQL default port
DB_USER = "postgres"        # PostgreSQL username
DB_NAME = "electronic_supply_chain_platform"  # Database name
```

### Customize Connection (Optional)

Set environment variables before running the app:

```bash
# Windows PowerShell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "your_password"
$env:DB_NAME = "electronic_supply_chain_platform"

# Or Windows CMD
set DB_HOST=localhost
set DB_PORT=5432
set DB_USER=postgres
set DB_PASSWORD=your_password
set DB_NAME=electronic_supply_chain_platform
```

---

## ✨ WHAT WAS FIXED

### 1. **Dependency Conflict (requirements.txt)**
- ❌ **Before**: `Flask>=3.0.0` (loose version - caused pip resolution errors)
- ✅ **After**: `Flask==3.0.5` (pinned to stable version)

### 2. **MySQL → PostgreSQL Migration**
- ❌ **Before**: Used `mysql-connector-python`
- ✅ **After**: Uses `psycopg2-binary` (PostgreSQL driver)

### 3. **Database Connection (db.py)**
- ❌ **Before**: MySQL connection with `mysql.connector`
- ✅ **After**: PostgreSQL connection with `psycopg2`
- Updated cursor factory to use `RealDictCursor` for dict-like results

### 4. **Database Schema (database.sql)**
- ❌ **Before**: MySQL-specific syntax
- ✅ **After**: PostgreSQL-compatible syntax
  - `INT AUTO_INCREMENT` → `SERIAL`
  - `ENUM('admin', 'supplier', 'customer')` → `CREATE TYPE user_role AS ENUM(...)`
  - `ON UPDATE CURRENT_TIMESTAMP` → Trigger function
  - Quote user table name as `"user"` (reserved keyword in PostgreSQL)

### 5. **Config File (config.py)**
- ❌ **Before**: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_DATABASE`
- ✅ **After**: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` (PostgreSQL standard names)

### 6. **Database Initialization (app.py)**
- ❌ **Before**: Used MySQL's `cursor.execute(script, multi=True)`
- ✅ **After**: Splits SQL statements and executes them separately (PostgreSQL compatible)

---

## 📂 PROJECT STRUCTURE

```
electronic_supply_chain_platform/
├── app.py                          # Main Flask application
├── config.py                       # Configuration (PostgreSQL settings)
├── db.py                          # Database functions (psycopg2)
├── database.sql                   # PostgreSQL schema & demo data
├── decorators.py                  # Authentication decorators
├── requirements.txt               # Python dependencies (Flask, psycopg2)
├── routes/
│   ├── __init__.py
│   ├── admin.py                  # Admin routes
│   ├── auth.py                   # Authentication routes
│   ├── customer.py               # Customer routes
│   ├── public.py                 # Public routes
│   └── supplier.py               # Supplier routes
├── static/
│   ├── css/style.css
│   └── images/
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── runtime_error.html
    ├── admin/
    ├── customer/
    └── supplier/
```

---

## 🐛 TROUBLESHOOTING

### Issue: "Cannot connect to PostgreSQL"

```
Unable to connect to PostgreSQL. Check your database settings.
```

**Solutions:**
1. Verify PostgreSQL is running: `pg_isready -h localhost`
2. Check DB credentials in `config.py`
3. Ensure database exists: `psql -U postgres -l` (list all databases)
4. Create database if missing: `createdb -U postgres electronic_supply_chain_platform`

### Issue: "Database initialization failed"

```
Error executing statement: CREATE TYPE...
```

**Solution:**
1. Drop existing database: `dropdb -U postgres electronic_supply_chain_platform`
2. Create fresh database: `createdb -U postgres electronic_supply_chain_platform`
3. Run initialization again: `flask --app app init-db`

### Issue: "ModuleNotFoundError: No module named 'psycopg2'"

```bash
# Reinstall dependencies
pip install --force-reinstall psycopg2-binary==2.9.9
```

### Issue: "Port 5000 already in use"

```bash
# Run on different port
flask --app app run --host 127.0.0.1 --port 5001
```

---

## 🔐 Security Notes

- ✅ **SECRET_KEY** is set to `dev-secret-change-me` for development
- ✅ **Change SECRET_KEY** before production: `export SECRET_KEY=your-secure-key`
- ✅ **Passwords** are hashed using Werkzeug's security functions
- ✅ **SQL Injection** is prevented using parameterized queries

---

## 📊 Database Schema Overview

The application includes 9 tables:

1. **user** - User accounts (admin, supplier, customer)
2. **admin** - Admin details
3. **category** - Product categories
4. **supplier** - Supplier information
5. **product** - Product listings
6. **inventory** - Warehouse inventory tracking
7. **cart** - Shopping cart items
8. **orders** - Customer orders
9. **order_items** - Items in orders
10. **payment** - Payment records
11. **return_refund** - Return/refund requests

---

## ✅ VERIFICATION CHECKLIST

After setup, verify everything works:

- [ ] Python 3.10.11 is installed
- [ ] PostgreSQL is running and accessible
- [ ] Virtual environment is created and activated
- [ ] Dependencies installed: `pip list | grep -E "Flask|psycopg2|Werkzeug"`
- [ ] Database created: `psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='electronic_supply_chain_platform'"`
- [ ] Database initialized: `flask --app app init-db` runs successfully
- [ ] Server starts: `flask --app app run --debug` starts without errors
- [ ] Login page accessible: Open http://localhost:5000/login in browser
- [ ] Can login with demo credentials

---

## 🆘 SUPPORT

If you encounter any issues:

1. Check the **TROUBLESHOOTING** section above
2. Verify all prerequisites are installed
3. Review `config.py` for correct PostgreSQL settings
4. Check PostgreSQL logs for database errors

---

**Last Updated**: June 10, 2026 | **Database**: PostgreSQL | **Python**: 3.10.11
