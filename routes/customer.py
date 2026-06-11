import uuid

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from db import execute_query, fetch_all, fetch_one
from decorators import roles_required

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


@customer_bp.route("/dashboard")
@roles_required("customer")
def dashboard():
    user_id = session["user_id"]
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM cart WHERE user_id = %s) AS cart_lines,
            (SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE user_id = %s) AS cart_quantity,
            (SELECT COUNT(*) FROM orders WHERE user_id = %s) AS total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE user_id = %s) AS total_spend
        """,
        (user_id, user_id, user_id, user_id),
    )
    recent_orders = fetch_all(
        """
        SELECT order_id, order_date, total_amount, order_status, shipping_address
        FROM orders
        WHERE user_id = %s
        ORDER BY order_date DESC
        LIMIT 5
        """,
        (user_id,),
    )
    trending_products = fetch_all(
        """
        SELECT p.product_id, p.product_name, p.brand, p.price, p.image, c.category_name
        FROM product p
        JOIN category c ON c.category_id = p.category_id
        ORDER BY p.created_at DESC
        LIMIT 4
        """
    )
    return render_template(
        "customer/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        trending_products=trending_products,
    )


@customer_bp.route("/products")
@roles_required("customer")
def products_redirect():
    return redirect(url_for("public.products"))


@customer_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@roles_required("customer")
def add_to_cart(product_id):
    user_id = session["user_id"]
    quantity = max(int(request.form.get("quantity", 1)), 1)

    product = fetch_one(
        "SELECT product_id, product_name, stock_quantity FROM product WHERE product_id = %s",
        (product_id,),
    )
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("public.products"))

    if quantity > product["stock_quantity"]:
        flash("Requested quantity exceeds available stock.", "warning")
        return redirect(url_for("public.products"))

    existing = fetch_one(
        "SELECT cart_id, quantity FROM cart WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )

    if existing:
        new_quantity = existing["quantity"] + quantity
        if new_quantity > product["stock_quantity"]:
            flash("Cart quantity exceeds available stock.", "warning")
            return redirect(url_for("public.products"))
        execute_query("UPDATE cart SET quantity = %s WHERE cart_id = %s", (new_quantity, existing["cart_id"]))
    else:
        execute_query(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
            (user_id, product_id, quantity),
        )

    flash(f"{product['product_name']} added to cart.", "success")
    return redirect(request.referrer or url_for("public.products"))


@customer_bp.route("/cart")
@roles_required("customer")
def cart():
    user_id = session["user_id"]
    cart_items = fetch_all(
        """
        SELECT c.cart_id, c.quantity, p.product_id, p.product_name, p.brand, p.price, p.stock_quantity, p.image
        FROM cart c
        JOIN product p ON p.product_id = c.product_id
        WHERE c.user_id = %s
        ORDER BY c.added_at DESC
        """,
        (user_id,),
    )
    totals = {
        "subtotal": sum(float(item["price"]) * int(item["quantity"]) for item in cart_items),
        "total_items": sum(int(item["quantity"]) for item in cart_items),
    }
    return render_template("customer/cart.html", cart_items=cart_items, totals=totals)


@customer_bp.route("/cart/update/<int:cart_id>", methods=["POST"])
@roles_required("customer")
def update_cart(cart_id):
    quantity = max(int(request.form.get("quantity", 1)), 1)
    item = fetch_one(
        """
        SELECT c.cart_id, p.stock_quantity
        FROM cart c
        JOIN product p ON p.product_id = c.product_id
        WHERE c.cart_id = %s AND c.user_id = %s
        """,
        (cart_id, session["user_id"]),
    )

    if not item:
        flash("Cart item not found.", "danger")
        return redirect(url_for("customer.cart"))

    if quantity > item["stock_quantity"]:
        flash("Requested quantity exceeds available stock.", "warning")
        return redirect(url_for("customer.cart"))

    execute_query("UPDATE cart SET quantity = %s WHERE cart_id = %s", (quantity, cart_id))
    flash("Cart updated successfully.", "success")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/remove/<int:cart_id>", methods=["POST"])
@roles_required("customer")
def remove_cart_item(cart_id):
    execute_query("DELETE FROM cart WHERE cart_id = %s AND user_id = %s", (cart_id, session["user_id"]))
    flash("Item removed from cart.", "info")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/checkout", methods=["GET"])
@roles_required("customer")
def checkout():
    user_id = session["user_id"]
    user = fetch_one('SELECT name, address FROM "user" WHERE user_id = %s', (user_id,))
    cart_items = fetch_all(
        """
        SELECT c.cart_id, c.quantity, p.product_id, p.product_name, p.price, p.stock_quantity
        FROM cart c
        JOIN product p ON p.product_id = c.product_id
        WHERE c.user_id = %s
        ORDER BY c.added_at DESC
        """,
        (user_id,),
    )

    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("customer.cart"))

    subtotal = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)
    return render_template("customer/checkout.html", cart_items=cart_items, subtotal=subtotal, user=user)


@customer_bp.route("/checkout/process", methods=["POST"])
@roles_required("customer")
def process_payment():
    """
    AJAX endpoint called by the dummy payment modal after user 'pays'.
    Creates order, items, updates stock, saves payment with transaction ID.
    """
    user_id = session["user_id"]
    shipping_address = request.form.get("shipping_address", "").strip()
    payment_method   = request.form.get("payment_method", "").strip()

    if not shipping_address or not payment_method:
        return jsonify({"success": False, "message": "Shipping address and payment method are required."})

    cart_items = fetch_all(
        """
        SELECT c.quantity, p.product_id, p.product_name, p.price, p.stock_quantity
        FROM cart c
        JOIN product p ON p.product_id = c.product_id
        WHERE c.user_id = %s
        """,
        (user_id,),
    )

    if not cart_items:
        return jsonify({"success": False, "message": "Your cart is empty."})

    for item in cart_items:
        if int(item["quantity"]) > int(item["stock_quantity"]):
            return jsonify({"success": False, "message": f"Insufficient stock for {item['product_name']}."})

    subtotal = sum(float(item["price"]) * int(item["quantity"]) for item in cart_items)
    transaction_id = "TXN-" + uuid.uuid4().hex[:12].upper()

    order_id = execute_query(
        "INSERT INTO orders (user_id, total_amount, order_status, shipping_address) VALUES (%s, %s, %s, %s)",
        (user_id, subtotal, "Processing", shipping_address),
    )

    for item in cart_items:
        execute_query(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )
        execute_query(
            "UPDATE product SET stock_quantity = stock_quantity - %s WHERE product_id = %s",
            (item["quantity"], item["product_id"]),
        )
        execute_query(
            "UPDATE inventory SET stock_quantity = stock_quantity - %s, last_updated = CURRENT_TIMESTAMP WHERE product_id = %s",
            (item["quantity"], item["product_id"]),
        )

    execute_query(
        "INSERT INTO payment (order_id, payment_method, payment_status, transaction_id) VALUES (%s, %s, %s, %s)",
        (order_id, payment_method, "Paid", transaction_id),
    )
    execute_query("DELETE FROM cart WHERE user_id = %s", (user_id,))

    return jsonify({
        "success": True,
        "order_id": order_id,
        "transaction_id": transaction_id,
        "redirect": url_for("customer.orders")
    })


@customer_bp.route("/orders")
@roles_required("customer")
def orders():
    user_id = session["user_id"]
    orders_data = fetch_all(
        """
        SELECT o.order_id, o.order_date, o.total_amount, o.order_status, o.shipping_address,
               p.payment_method, p.payment_status, p.transaction_id
        FROM orders o
        LEFT JOIN payment p ON p.order_id = o.order_id
        WHERE o.user_id = %s
        ORDER BY o.order_date DESC
        """,
        (user_id,),
    )
    order_items = fetch_all(
        """
        SELECT oi.order_id, oi.quantity, oi.price, pr.product_name, pr.brand, pr.image
        FROM order_items oi
        JOIN product pr ON pr.product_id = oi.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.user_id = %s
        ORDER BY oi.order_id DESC
        """,
        (user_id,),
    )

    grouped_items = {}
    for item in order_items:
        grouped_items.setdefault(item["order_id"], []).append(item)

    return render_template("customer/orders.html", orders=orders_data, grouped_items=grouped_items)


@customer_bp.route("/orders/<int:order_id>/track")
@roles_required("customer")
def track_order(order_id):
    """View detailed order tracking information"""
    user_id = session["user_id"]
    
    # Verify order belongs to this customer
    order = fetch_one(
        "SELECT * FROM orders WHERE order_id = %s AND user_id = %s",
        (order_id, user_id)
    )
    
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("customer.orders"))
    
    # Get order items with product details
    order_items = fetch_all(
        """
        SELECT oi.order_item_id, oi.product_id, pr.product_name, pr.brand, pr.image, oi.quantity, oi.price
        FROM order_items oi
        JOIN product pr ON pr.product_id = oi.product_id
        WHERE oi.order_id = %s
        """,
        (order_id,)
    )
    
    # Get tracking history for the order
    tracking_history = fetch_all(
        """
        SELECT ot.tracking_id, ot.order_item_id, ot.status, ot.warehouse_location, 
               ot.timestamp, ot.notes, pr.product_name, pr.brand
        FROM order_tracking ot
        LEFT JOIN order_items oi ON oi.order_item_id = ot.order_item_id
        LEFT JOIN product pr ON pr.product_id = oi.product_id
        WHERE ot.order_id = %s
        ORDER BY ot.timestamp DESC
        """,
        (order_id,)
    )
    
    # Group tracking by order_item_id for better display
    tracking_by_item = {}
    for track in tracking_history:
        item_id = track["order_item_id"]
        if item_id not in tracking_by_item:
            tracking_by_item[item_id] = []
        tracking_by_item[item_id].append(track)
    
    return render_template(
        "customer/track_order.html",
        order=order,
        order_items=order_items,
        tracking_history=tracking_history,
        tracking_by_item=tracking_by_item
    )