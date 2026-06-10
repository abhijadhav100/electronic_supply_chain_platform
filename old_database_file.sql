-- PostgreSQL database schema for Electronic Supply Chain Platform
-- Create ENUM type for user roles
CREATE TYPE user_role AS ENUM ('admin', 'supplier', 'customer');

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS return_refund;
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS supplier;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS "user";

-- Create user table
CREATE TABLE "user" (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin table
CREATE TABLE admin (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Create category table
CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(120) NOT NULL UNIQUE,
    description TEXT
);

-- Create supplier table
CREATE TABLE supplier (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    contact_person VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    address TEXT NOT NULL
);

-- Create product table
CREATE TABLE product (
    product_id SERIAL PRIMARY KEY,
    category_id INT NOT NULL,
    supplier_id INT NOT NULL,
    product_name VARCHAR(160) NOT NULL,
    brand VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    image VARCHAR(255) DEFAULT '/static/images/product-default.svg',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category(category_id),
    CONSTRAINT fk_product_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

-- Create inventory table
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL UNIQUE,
    warehouse_location VARCHAR(120) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- Create trigger function for updating last_updated timestamp
CREATE OR REPLACE FUNCTION update_inventory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for inventory table
CREATE TRIGGER inventory_update_trigger
BEFORE UPDATE ON inventory
FOR EACH ROW
EXECUTE FUNCTION update_inventory_timestamp();

-- Create cart table
CREATE TABLE cart (
    cart_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES "user"(user_id),
    CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT uq_cart_user_product UNIQUE (user_id, product_id)
);

-- Create orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    order_status VARCHAR(40) NOT NULL DEFAULT 'Processing',
    shipping_address TEXT NOT NULL,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES "user"(user_id)
);

-- Create order_items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- Create payment table
CREATE TABLE payment (
    payment_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    payment_method VARCHAR(60) NOT NULL,
    payment_status VARCHAR(40) NOT NULL DEFAULT 'Pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Create return_refund table
CREATE TABLE return_refund (
    return_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'Requested',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_return_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Insert demo data
INSERT INTO "user" (name, email, phone, password, role, address) VALUES
('Platform Admin', 'admin@electrohub.com', '9876500000', 'pbkdf2:sha256:600000$fixedsaltadm$10d45578bd9f25e25473c0bd7404c0573de183945806b74731c95dfeded6f248', 'admin', 'Corporate HQ, Bangalore'),
('Volt Supply', 'supplier@electrohub.com', '9876500011', 'pbkdf2:sha256:600000$fixedsaltsup$bcd1bf92216459c9ab8bc1b5191d7ee64d0a01a5fc0932f942c41078ead563d3', 'supplier', 'No. 21, Electronic City, Bangalore'),
('Rahul Sharma', 'customer@electrohub.com', '9876500022', 'pbkdf2:sha256:600000$fixedsaltcus$85de2cebf8a44c8aef4aeea0d1b368f50c59f4ed4f51a2e013a4bb76a0bb6ff9', 'customer', 'Sector 18, Noida');

INSERT INTO admin (username, email, password) VALUES
('platform_admin', 'admin@electrohub.com', 'pbkdf2:sha256:600000$fixedsaltadm$10d45578bd9f25e25473c0bd7404c0573de183945806b74731c95dfeded6f248');

INSERT INTO category (category_name, description) VALUES
('Mobile Accessories', 'Chargers, power banks, earphones, and phone essentials'),
('Computer Peripherals', 'Keyboards, mice, webcams, and workstation accessories'),
('Smart Wearables', 'Smartwatches, fitness trackers, and connected gadgets'),
('Audio Devices', 'Bluetooth speakers, headsets, and home audio gear');

INSERT INTO supplier (name, contact_person, phone, email, address) VALUES
('Volt Supply', 'Arjun Mehta', '9876500011', 'supplier@electrohub.com', 'No. 21, Electronic City, Bangalore'),
('NextGen Electronics', 'Priya Iyer', '9876500033', 'sales@nextgen.com', 'MIDC Industrial Hub, Pune');

INSERT INTO product (category_id, supplier_id, product_name, brand, description, price, stock_quantity, image) VALUES
(1, 1, 'TurboCharge 65W Adapter', 'Voltix', 'Fast charging GaN adapter for phones, tablets, and ultrabooks.', 2499.00, 42, '/static/images/charger.svg'),
(2, 2, 'Mechanical RGB Keyboard', 'ClickForge', 'Compact wireless mechanical keyboard with multi-device support.', 4599.00, 28, '/static/images/keyboard.svg'),
(1, 1, 'MagSafe Power Bank 10000mAh', 'Voltix', 'Slim magnetic power bank with USB-C fast recharge.', 3299.00, 35, '/static/images/powerbank.svg'),
(3, 2, 'ActiveFit Smart Watch', 'PulseOne', 'AMOLED smartwatch with GPS, health insights, and 7-day battery.', 6999.00, 20, '/static/images/smartwatch.svg'),
(4, 2, 'BassFlow Bluetooth Speaker', 'SonicArc', 'Portable speaker with deep bass, IPX6 protection, and 12-hour playback.', 3899.00, 18, '/static/images/speaker.svg'),
(1, 1, 'Noise-Cancel Earbuds Pro', 'Voltix', 'ANC true wireless earbuds with quad microphones and low-latency mode.', 5499.00, 24, '/static/images/earbuds.svg');

INSERT INTO inventory (product_id, warehouse_location, stock_quantity) VALUES
(1, 'Bangalore WH-A1', 42),
(2, 'Pune WH-C3', 28),
(3, 'Bangalore WH-B2', 35),
(4, 'Pune WH-S1', 20),
(5, 'Pune WH-A5', 18),
(6, 'Bangalore WH-E4', 24);

INSERT INTO orders (user_id, total_amount, order_status, shipping_address) VALUES
(3, 10898.00, 'Shipped', 'Sector 18, Noida'),
(3, 2499.00, 'Processing', 'Sector 18, Noida');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 4, 1, 6999.00),
(1, 5, 1, 3899.00),
(2, 1, 1, 2499.00);

INSERT INTO payment (order_id, payment_method, payment_status) VALUES
(1, 'UPI', 'Paid'),
(2, 'Credit Card', 'Paid');

INSERT INTO return_refund (order_id, reason, status) VALUES
(1, 'Requested replacement due to transit damage on speaker grill.', 'Under Review');
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_return_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

INSERT INTO user (name, email, phone, password, role, address) VALUES
('Platform Admin', 'admin@electrohub.com', '9876500000', 'pbkdf2:sha256:600000$fixedsaltadm$10d45578bd9f25e25473c0bd7404c0573de183945806b74731c95dfeded6f248', 'admin', 'Corporate HQ, Bangalore'),
('Volt Supply', 'supplier@electrohub.com', '9876500011', 'pbkdf2:sha256:600000$fixedsaltsup$bcd1bf92216459c9ab8bc1b5191d7ee64d0a01a5fc0932f942c41078ead563d3', 'supplier', 'No. 21, Electronic City, Bangalore'),
('Rahul Sharma', 'customer@electrohub.com', '9876500022', 'pbkdf2:sha256:600000$fixedsaltcus$85de2cebf8a44c8aef4aeea0d1b368f50c59f4ed4f51a2e013a4bb76a0bb6ff9', 'customer', 'Sector 18, Noida');

INSERT INTO admin (username, email, password) VALUES
('platform_admin', 'admin@electrohub.com', 'pbkdf2:sha256:600000$fixedsaltadm$10d45578bd9f25e25473c0bd7404c0573de183945806b74731c95dfeded6f248');

INSERT INTO category (category_name, description) VALUES
('Mobile Accessories', 'Chargers, power banks, earphones, and phone essentials'),
('Computer Peripherals', 'Keyboards, mice, webcams, and workstation accessories'),
('Smart Wearables', 'Smartwatches, fitness trackers, and connected gadgets'),
('Audio Devices', 'Bluetooth speakers, headsets, and home audio gear');

INSERT INTO supplier (name, contact_person, phone, email, address) VALUES
('Volt Supply', 'Arjun Mehta', '9876500011', 'supplier@electrohub.com', 'No. 21, Electronic City, Bangalore'),
('NextGen Electronics', 'Priya Iyer', '9876500033', 'sales@nextgen.com', 'MIDC Industrial Hub, Pune');

INSERT INTO product (category_id, supplier_id, product_name, brand, description, price, stock_quantity, image) VALUES
(1, 1, 'TurboCharge 65W Adapter', 'Voltix', 'Fast charging GaN adapter for phones, tablets, and ultrabooks.', 2499.00, 42, '/static/images/charger.svg'),
(2, 2, 'Mechanical RGB Keyboard', 'ClickForge', 'Compact wireless mechanical keyboard with multi-device support.', 4599.00, 28, '/static/images/keyboard.svg'),
(1, 1, 'MagSafe Power Bank 10000mAh', 'Voltix', 'Slim magnetic power bank with USB-C fast recharge.', 3299.00, 35, '/static/images/powerbank.svg'),
(3, 2, 'ActiveFit Smart Watch', 'PulseOne', 'AMOLED smartwatch with GPS, health insights, and 7-day battery.', 6999.00, 20, '/static/images/smartwatch.svg'),
(4, 2, 'BassFlow Bluetooth Speaker', 'SonicArc', 'Portable speaker with deep bass, IPX6 protection, and 12-hour playback.', 3899.00, 18, '/static/images/speaker.svg'),
(1, 1, 'Noise-Cancel Earbuds Pro', 'Voltix', 'ANC true wireless earbuds with quad microphones and low-latency mode.', 5499.00, 24, '/static/images/earbuds.svg');

INSERT INTO inventory (product_id, warehouse_location, stock_quantity) VALUES
(1, 'Bangalore WH-A1', 42),
(2, 'Pune WH-C3', 28),
(3, 'Bangalore WH-B2', 35),
(4, 'Pune WH-S1', 20),
(5, 'Pune WH-A5', 18),
(6, 'Bangalore WH-E4', 24);

INSERT INTO orders (user_id, total_amount, order_status, shipping_address) VALUES
(3, 10898.00, 'Shipped', 'Sector 18, Noida'),
(3, 2499.00, 'Processing', 'Sector 18, Noida');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 4, 1, 6999.00),
(1, 5, 1, 3899.00),
(2, 1, 1, 2499.00);

INSERT INTO payment (order_id, payment_method, payment_status) VALUES
(1, 'UPI', 'Paid'),
(2, 'Credit Card', 'Paid');

INSERT INTO return_refund (order_id, reason, status) VALUES
(1, 'Requested replacement due to transit damage on speaker grill.', 'Under Review');
