# Electronic Accessories Supply Chain & Sales Management Platform

A full-stack Flask + PostgreSQL web application for managing electronic accessory products, supplier inventory, customer purchases, and admin reporting.

## Stack

- Backend: Python Flask 3.0.5
- Database: PostgreSQL
- Driver: psycopg2-binary
- Frontend: HTML, CSS, Bootstrap 5, Font Awesome

## Project Structure

```text
electronic_supply_chain_platform/
├── app.py
├── config.py
├── db.py
├── decorators.py
├── database.sql
├── requirements.txt
├── SETUP_AND_RUN_GUIDE.md    [Comprehensive setup instructions]
├── routes/
├── static/
│   ├── css/
│   └── images/
└── templates/
    ├── admin/
    ├── customer/
    └── supplier/
```

## Features

- Role-based login for admin, supplier, and customer
- Responsive e-commerce home page with hero section and product cards
- Product browsing with search and category filters
- Cart, checkout, payment simulation, and order tracking
- Admin product/category management, user listing, and order reports
- Supplier product creation, inventory updates, and order visibility
- Flash notifications and shared Bootstrap-based layout

## Demo Credentials

- Admin: `admin@electrohub.com` / `admin123`
- Supplier: `supplier@electrohub.com` / `supplier123`
- Customer: `customer@electrohub.com` / `customer123`

## Quick Start

### Prerequisites
- Python 3.10+ 
- PostgreSQL (with running service)

### Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create PostgreSQL database:
```bash
psql -U postgres
CREATE DATABASE electronic_supply_chain_platform;
\q
```

4. Initialize database schema and demo data:
```bash
flask --app app init-db
```

5. Configure database (optional - set environment variables):
```bash
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_USER="postgres"
$env:DB_PASSWORD=""
$env:DB_NAME="electronic_supply_chain_platform"
$env:SECRET_KEY="change-this-secret"
```

6. Run the app:
```bash
flask --app app run --debug
```

7. Open in browser:
- Home: `http://127.0.0.1:5000/`
- Login: `http://127.0.0.1:5000/login`
- Register: `http://127.0.0.1:5000/register`

## Detailed Setup Guide

**⚠️ For complete setup instructions, troubleshooting, and PostgreSQL configuration, see [SETUP_AND_RUN_GUIDE.md](SETUP_AND_RUN_GUIDE.md)**

## Recent Changes

✅ **MySQL → PostgreSQL Migration**
- Updated database driver from `mysql-connector-python` to `psycopg2-binary`
- Converted SQL schema to PostgreSQL syntax
- Fixed dependency conflicts in requirements.txt

✅ **Dependencies Optimized**
- Flask: Pinned to 3.0.5 (resolves version conflicts)
- psycopg2-binary: 2.9.9 (PostgreSQL driver)
- Werkzeug: 3.0.1 (Flask dependency)

## Notes

- The app uses raw MySQL queries through `mysql-connector-python`.
- Product images are provided as local SVG assets under `static/images/`.
- Supplier registration automatically creates a linked supplier record.
- Admin registration is intentionally disabled from the public form; use the seeded admin account.
