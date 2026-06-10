from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute_query, fetch_all, fetch_one
from decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@roles_required("admin")
def dashboard():
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM product) AS total_products,
            (SELECT COUNT(*) FROM supplier) AS total_suppliers,
            (SELECT COUNT(*) FROM "user") AS total_users,
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders) AS revenue
        """
    )
    low_stock = fetch_all(
        """
        SELECT product_id, product_name, brand, stock_quantity
        FROM product
        WHERE stock_quantity <= 10
        ORDER BY stock_quantity ASC
        LIMIT 6
        """
    )
    recent_orders = fetch_all(
        """
        SELECT o.order_id, u.name AS customer_name, o.order_date, o.total_amount, o.order_status
        FROM orders o
        JOIN "user" u ON u.user_id = o.user_id
        ORDER BY o.order_date DESC
        LIMIT 8
        """
    )
    return render_template("admin/dashboard.html", stats=stats, low_stock=low_stock, recent_orders=recent_orders)


@admin_bp.route("/products")
@roles_required("admin")
def products():
    products_data = fetch_all(
        """
        SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity, p.image, p.created_at,
               c.category_name, s.name AS supplier_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        JOIN supplier s ON s.supplier_id = p.supplier_id
        ORDER BY p.created_at DESC
        """
    )
    categories = fetch_all("SELECT category_id, category_name FROM category ORDER BY category_name")
    suppliers = fetch_all("SELECT supplier_id, name FROM supplier ORDER BY name")
    return render_template("admin/products.html", products=products_data, categories=categories, suppliers=suppliers, edit_product=None)


@admin_bp.route("/products/add", methods=["POST"])
@roles_required("admin")
def add_product():
    form = request.form
    product_id = execute_query(
        """
        INSERT INTO product (category_id, supplier_id, product_name, brand, description, price, stock_quantity, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            form.get("category_id"),
            form.get("supplier_id"),
            form.get("product_name"),
            form.get("brand"),
            form.get("description"),
            form.get("price"),
            form.get("stock_quantity"),
            form.get("image"),
        ),
    )
    execute_query(
        "INSERT INTO inventory (product_id, warehouse_location, stock_quantity) VALUES (%s, %s, %s)",
        (product_id, form.get("warehouse_location"), form.get("stock_quantity")),
    )
    flash("Product added successfully.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@roles_required("admin")
def edit_product(product_id):
    if request.method == "POST":
        form = request.form
        execute_query(
            """
            UPDATE product
            SET category_id = %s, supplier_id = %s, product_name = %s, brand = %s,
                description = %s, price = %s, stock_quantity = %s, image = %s
            WHERE product_id = %s
            """,
            (
                form.get("category_id"),
                form.get("supplier_id"),
                form.get("product_name"),
                form.get("brand"),
                form.get("description"),
                form.get("price"),
                form.get("stock_quantity"),
                form.get("image"),
                product_id,
            ),
        )
        execute_query(
            """
            UPDATE inventory
            SET warehouse_location = %s, stock_quantity = %s, last_updated = CURRENT_TIMESTAMP
            WHERE product_id = %s
            """,
            (form.get("warehouse_location"), form.get("stock_quantity"), product_id),
        )
        flash("Product updated successfully.", "success")
        return redirect(url_for("admin.products"))

    product = fetch_one(
        """
        SELECT p.*, i.warehouse_location
        FROM product p
        LEFT JOIN inventory i ON i.product_id = p.product_id
        WHERE p.product_id = %s
        """,
        (product_id,),
    )
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin.products"))

    products_data = fetch_all(
        """
        SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity, p.image, p.created_at,
               c.category_name, s.name AS supplier_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        JOIN supplier s ON s.supplier_id = p.supplier_id
        ORDER BY p.created_at DESC
        """
    )
    categories = fetch_all("SELECT category_id, category_name FROM category ORDER BY category_name")
    suppliers = fetch_all("SELECT supplier_id, name FROM supplier ORDER BY name")
    return render_template("admin/products.html", products=products_data, categories=categories, suppliers=suppliers, edit_product=product)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@roles_required("admin")
def delete_product(product_id):
    execute_query("DELETE FROM inventory WHERE product_id = %s", (product_id,))
    execute_query("DELETE FROM cart WHERE product_id = %s", (product_id,))
    execute_query("DELETE FROM order_items WHERE product_id = %s", (product_id,))
    execute_query("DELETE FROM product WHERE product_id = %s", (product_id,))
    flash("Product deleted successfully.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@roles_required("admin")
def categories():
    if request.method == "POST":
        execute_query(
            "INSERT INTO category (category_name, description) VALUES (%s, %s)",
            (request.form.get("category_name"), request.form.get("description")),
        )
        flash("Category created successfully.", "success")
        return redirect(url_for("admin.categories"))

    categories_data = fetch_all(
        """
        SELECT c.category_id, c.category_name, c.description, COUNT(p.product_id) AS product_count
        FROM category c
        LEFT JOIN product p ON p.category_id = c.category_id
        GROUP BY c.category_id, c.category_name, c.description
        ORDER BY c.category_name
        """
    )
    edit_category = None
    category_id = request.args.get("edit")
    if category_id:
        edit_category = fetch_one("SELECT * FROM category WHERE category_id = %s", (category_id,))
    return render_template("admin/categories.html", categories=categories_data, edit_category=edit_category)


@admin_bp.route("/categories/<int:category_id>/update", methods=["POST"])
@roles_required("admin")
def update_category(category_id):
    execute_query(
        "UPDATE category SET category_name = %s, description = %s WHERE category_id = %s",
        (request.form.get("category_name"), request.form.get("description"), category_id),
    )
    flash("Category updated successfully.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@roles_required("admin")
def delete_category(category_id):
    product_count = fetch_one("SELECT COUNT(*) AS total FROM product WHERE category_id = %s", (category_id,))
    if product_count and product_count["total"] > 0:
        flash("Category cannot be deleted while products are assigned to it.", "warning")
        return redirect(url_for("admin.categories"))

    execute_query("DELETE FROM category WHERE category_id = %s", (category_id,))
    flash("Category deleted successfully.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/orders")
@roles_required("admin")
def orders():
    orders_data = fetch_all(
        """
        SELECT o.order_id, o.order_date, o.total_amount, o.order_status, o.shipping_address,
               u.name AS customer_name, u.email AS customer_email
        FROM orders o
        JOIN "user" u ON u.user_id = o.user_id
        ORDER BY o.order_date DESC
        """
    )
    report = fetch_one(
        """
        SELECT
            COUNT(*) AS total_orders,
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            SUM(CASE WHEN order_status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
            SUM(CASE WHEN order_status = 'Processing' THEN 1 ELSE 0 END) AS processing_orders
        FROM orders
        """
    )
    return render_template("admin/orders.html", orders=orders_data, report=report)


@admin_bp.route("/users")
@roles_required("admin")
def users():
    users_data = fetch_all(
        'SELECT user_id, name, email, phone, role, address, created_at FROM "user" ORDER BY created_at DESC'
    )
    return render_template("admin/users.html", users=users_data)


@admin_bp.route("/users/<int:user_id>")
@roles_required("admin")
def user_details(user_id):
    user = fetch_one('SELECT * FROM "user" WHERE user_id = %s', (user_id,))
    return render_template("admin/user_details.html", user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@roles_required("admin")
def delete_user(user_id):
    execute_query('DELETE FROM "user" WHERE user_id = %s', (user_id,))
    flash("User deleted successfully", "info")
    return redirect(url_for("admin.users"))