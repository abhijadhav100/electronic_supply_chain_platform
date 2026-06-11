from flask import Blueprint, redirect, render_template, request, session, url_for

from db import execute_query, fetch_all, fetch_one

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    featured_products = fetch_all(
        """
        SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity, p.image,
               c.category_name, s.name AS supplier_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        JOIN supplier s ON s.supplier_id = p.supplier_id
        ORDER BY p.created_at DESC
        LIMIT 8
        """
    )
    categories = fetch_all(
        """
        SELECT c.category_id, c.category_name, c.description, COUNT(p.product_id) AS product_count
        FROM category c
        LEFT JOIN product p ON p.category_id = c.category_id
        GROUP BY c.category_id, c.category_name, c.description
        ORDER BY c.category_name
        """
    )
    return render_template("home.html", featured_products=featured_products, categories=categories)


@public_bp.route("/products")
def products():
    search_term = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()

    query = """
        SELECT p.product_id, p.product_name, p.brand, p.description, p.price, p.stock_quantity,
               p.image, p.view_count, c.category_name, s.name AS supplier_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        JOIN supplier s ON s.supplier_id = p.supplier_id
        WHERE 1 = 1
    """
    params = []

    if search_term:
        query += " AND (p.product_name LIKE %s OR p.brand LIKE %s OR p.description LIKE %s)"
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term, like_term])

    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)

    query += " ORDER BY p.created_at DESC"

    products_data = fetch_all(query, tuple(params))
    categories = fetch_all("SELECT category_id, category_name FROM category ORDER BY category_name")

    return render_template(
        "products.html",
        products=products_data,
        categories=categories,
        selected_category=category_id,
        search_term=search_term,
    )


@public_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    # Increment view count every time product page is visited
    execute_query(
        "UPDATE product SET view_count = view_count + 1 WHERE product_id = %s",
        (product_id,),
    )
    product = fetch_one(
        """
        SELECT p.*, c.category_name, s.name AS supplier_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        JOIN supplier s ON s.supplier_id = p.supplier_id
        WHERE p.product_id = %s
        """,
        (product_id,),
    )
    if not product:
        return redirect(url_for("public.products"))

    return render_template("product_detail.html", product=product)


@public_bp.route("/dashboard")
def dashboard_redirect():
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "supplier":
        return redirect(url_for("supplier.dashboard"))
    if role == "customer":
        return redirect(url_for("customer.dashboard"))
    return redirect(url_for("public.home"))