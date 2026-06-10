from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute_query, fetch_one

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("public.dashboard_redirect"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip().lower()

        user = fetch_one(
            """
            SELECT user_id, name, email, password, role
            FROM "user"
            WHERE email = %s AND role = %s
            """,
            (email, role),
        )

        if not user or not check_password_hash(user["password"], password):
            flash("Invalid email, password, or role selection.", "danger")
            return render_template("login.html")

        if role == "admin":
            admin_record = fetch_one("SELECT admin_id FROM admin WHERE email = %s", (email,))
            if not admin_record:
                flash("Admin account is not configured correctly.", "danger")
                return render_template("login.html")

        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]
        session["email"] = user["email"]

        if role == "supplier":
            supplier = fetch_one("SELECT supplier_id FROM supplier WHERE email = %s", (email,))
            if not supplier:
                flash("Supplier profile is missing for this account.", "danger")
                session.clear()
                return render_template("login.html")
            session["supplier_id"] = supplier["supplier_id"]

        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("public.dashboard_redirect"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "customer").strip().lower()

        if role not in {"customer", "supplier"}:
            flash("Only customer and supplier registrations are available from this page.", "danger")
            return render_template("register.html")

        if not all([name, email, phone, address, password, confirm_password]):
            flash("Please fill in all required fields.", "warning")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = fetch_one('SELECT user_id FROM "user" WHERE email = %s', (email,))
        if existing_user:
            flash("An account already exists with that email address.", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        execute_query(
            """
            INSERT INTO "user" (name, email, phone, password, role, address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, phone, password_hash, role, address),
        )

        if role == "supplier":
            execute_query(
                """
                INSERT INTO supplier (name, contact_person, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, name, phone, email, address),
            )

        flash("Registration successful. Please log in to continue.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))