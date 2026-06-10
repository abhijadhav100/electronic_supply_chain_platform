import os
import subprocess
from pathlib import Path
from datetime import datetime

from flask import Flask, flash, render_template, session

from config import Config
from db import close_connection, fetch_one, get_db_connection
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.public import public_bp
from routes.supplier import supplier_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(supplier_bp)

    app.teardown_appcontext(close_connection)

    @app.context_processor
    def inject_global_data():
        cart_count = 0
        dashboard_endpoint = None
        role = session.get("role")

        if role == "admin":
            dashboard_endpoint = "admin.dashboard"
        elif role == "supplier":
            dashboard_endpoint = "supplier.dashboard"
        elif role == "customer":
            dashboard_endpoint = "customer.dashboard"

        if role == "customer" and session.get("user_id"):
            try:
                cart_data = fetch_one(
                    "SELECT COALESCE(SUM(quantity), 0) AS total_items FROM cart WHERE user_id = %s",
                    (session["user_id"],),
                )
                cart_count = int(cart_data["total_items"]) if cart_data else 0
            except Exception:
                cart_count = 0

        return {
            "cart_count": cart_count,
            "dashboard_endpoint": dashboard_endpoint,
            "current_year": datetime.now().year,
        }

    @app.template_filter("currency")
    def currency_filter(value):
        amount = float(value or 0)
        return f"Rs. {amount:,.2f}"

    @app.errorhandler(RuntimeError)
    def handle_runtime_error(error):
        flash(str(error), "danger")
        return render_template("runtime_error.html", error_message=str(error)), 500

    @app.cli.command("init-db")
    def init_db_command():
        script_path = Path(app.root_path) / "database.sql"
        if not script_path.exists():
            print("database.sql not found.")
            return

        # Get database credentials from config
        db_host = app.config["DB_HOST"]
        db_port = app.config["DB_PORT"]
        db_user = app.config["DB_USER"]
        db_name = app.config["DB_NAME"]
        db_password = app.config["DB_PASSWORD"]
        
        # Prepare environment for psql
        env = os.environ.copy()
        if db_password:
            env["PGPASSWORD"] = db_password
        
        # Build psql command
        cmd = [
            "psql",
            "-h", db_host,
            "-p", str(db_port),
            "-U", db_user,
            "-d", db_name,
            "-f", str(script_path)
        ]
        
        try:
            # Execute psql with the SQL file
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                print(f"❌ Error initializing database:")
                print(result.stderr)
                return
            
            print("✅ Database initialized successfully!")
            if result.stdout:
                print(result.stdout)
                
        except FileNotFoundError:
            print("❌ Error: psql command not found.")
            print("   Make sure PostgreSQL is installed and 'psql' is in your PATH.")
            return
        except Exception as e:
            print(f"❌ Error running psql: {str(e)}")
            return

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
