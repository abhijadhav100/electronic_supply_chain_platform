from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute_query, fetch_all, fetch_one
from decorators import roles_required

supplier_bp = Blueprint("supplier", __name__, url_prefix="/supplier")


@supplier_bp.route("/dashboard")
@roles_required("supplier")
def dashboard():
    supplier_id = session["supplier_id"]
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM product WHERE supplier_id = %s) AS total_products,
            (SELECT COUNT(*) FROM product WHERE supplier_id = %s AND stock_quantity <= 10) AS low_stock_count,
            (
                SELECT COUNT(DISTINCT oi.order_id)
                FROM order_items oi
                JOIN product p ON p.product_id = oi.product_id
                WHERE p.supplier_id = %s
            ) AS assigned_orders,
            (
                SELECT COALESCE(SUM(oi.quantity * oi.price), 0)
                FROM order_items oi
                JOIN product p ON p.product_id = oi.product_id
                WHERE p.supplier_id = %s
            ) AS gross_sales
        """,
        (supplier_id, supplier_id, supplier_id, supplier_id),
    )
    latest_products = fetch_all(
        """
        SELECT product_id, product_name, brand, price, stock_quantity, image
        FROM product
        WHERE supplier_id = %s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (supplier_id,),
    )
    latest_orders = fetch_all(
        """
        SELECT DISTINCT o.order_id, o.order_date, o.order_status, u.name AS customer_name
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN product p ON p.product_id = oi.product_id
        JOIN "user" u ON u.user_id = o.user_id
        WHERE p.supplier_id = %s
        ORDER BY o.order_date DESC
        LIMIT 6
        """,
        (supplier_id,),
    )
    return render_template("supplier/dashboard.html", stats=stats, latest_products=latest_products, latest_orders=latest_orders)


@supplier_bp.route("/products", methods=["GET", "POST"])
@roles_required("supplier")
def products():
    supplier_id = session["supplier_id"]

    if request.method == "POST":
        form = request.form
        product_id = execute_query(
            """
            INSERT INTO product (category_id, supplier_id, product_name, brand, description, price, stock_quantity, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                form.get("category_id"),
                supplier_id,
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
        flash("Product created successfully.", "success")
        return redirect(url_for("supplier.products"))

    categories = fetch_all("SELECT category_id, category_name FROM category ORDER BY category_name")
    products_data = fetch_all(
        """
        SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity, p.image,
               p.created_at, i.warehouse_location
        FROM product p
        LEFT JOIN inventory i ON i.product_id = p.product_id
        WHERE p.supplier_id = %s
        ORDER BY p.created_at DESC
        """,
        (supplier_id,),
    )
    return render_template("supplier/products.html", categories=categories, products=products_data)


@supplier_bp.route("/products/<int:product_id>/stock", methods=["POST"])
@roles_required("supplier")
def update_stock(product_id):
    supplier_id = session["supplier_id"]
    quantity = request.form.get("stock_quantity")
    warehouse_location = request.form.get("warehouse_location")

    product = fetch_one(
        "SELECT product_id FROM product WHERE product_id = %s AND supplier_id = %s",
        (product_id, supplier_id),
    )
    if not product:
        flash("Product not found for this supplier.", "danger")
        return redirect(url_for("supplier.products"))

    execute_query("UPDATE product SET stock_quantity = %s WHERE product_id = %s", (quantity, product_id))
    execute_query(
        """
        UPDATE inventory
        SET stock_quantity = %s, warehouse_location = %s, last_updated = CURRENT_TIMESTAMP
        WHERE product_id = %s
        """,
        (quantity, warehouse_location, product_id),
    )
    flash("Stock updated successfully.", "success")
    return redirect(url_for("supplier.products"))


@supplier_bp.route("/orders")
@roles_required("supplier")
def orders():
    supplier_id = session["supplier_id"]
    orders_data = fetch_all(
        """
        SELECT o.order_id, o.order_date, o.order_status, u.name AS customer_name,
               pr.product_name, oi.quantity, oi.price
        FROM orders o
        JOIN "user" u ON u.user_id = o.user_id
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN product pr ON pr.product_id = oi.product_id
        WHERE pr.supplier_id = %s
        ORDER BY o.order_date DESC
        """,
        (supplier_id,),
    )
    return render_template("supplier/orders.html", orders=orders_data)