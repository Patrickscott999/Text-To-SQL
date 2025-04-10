import sqlite3
import datetime
import random

# Create a sample database with multiple related tables
conn = sqlite3.connect('sample_retail.db')
cursor = conn.cursor()

# Create customers table
cursor.execute('''
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zipcode TEXT,
    signup_date TEXT,
    loyalty_points INTEGER DEFAULT 0
)
''')

# Create products table
cursor.execute('''
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL,
    description TEXT,
    stock_quantity INTEGER DEFAULT 0,
    supplier_id INTEGER,
    created_at TEXT
)
''')

# Create orders table
cursor.execute('''
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TEXT,
    total_amount REAL,
    status TEXT,
    payment_method TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
)
''')

# Create order_items table (for order details)
cursor.execute('''
CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price_per_unit REAL,
    subtotal REAL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
)
''')

# Create suppliers table
cursor.execute('''
CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zipcode TEXT
)
''')

# Sample data - Customers
customers = [
    (1, 'John Smith', 'john.smith@email.com', '555-123-4567', '123 Main St', 'New York', 'NY', '10001', '2022-01-15', 250),
    (2, 'Emily Johnson', 'emily.j@email.com', '555-234-5678', '456 Oak Ave', 'Los Angeles', 'CA', '90001', '2022-02-20', 175),
    (3, 'Michael Brown', 'mbrown@email.com', '555-345-6789', '789 Pine Rd', 'Chicago', 'IL', '60007', '2022-03-10', 325),
    (4, 'Sarah Davis', 'sarah.d@email.com', '555-456-7890', '101 Maple Dr', 'Houston', 'TX', '77001', '2022-04-05', 100),
    (5, 'Robert Wilson', 'rwilson@email.com', '555-567-8901', '202 Cedar Ln', 'Phoenix', 'AZ', '85001', '2022-05-12', 475),
    (6, 'Jennifer Taylor', 'jtaylor@email.com', '555-678-9012', '303 Birch St', 'Philadelphia', 'PA', '19019', '2022-06-22', 50),
    (7, 'David Martinez', 'dmartinez@email.com', '555-789-0123', '404 Elm Blvd', 'San Antonio', 'TX', '78201', '2022-07-17', 200),
    (8, 'Lisa Anderson', 'lisa.a@email.com', '555-890-1234', '505 Walnut Ave', 'San Diego', 'CA', '92093', '2022-08-30', 150)
]

# Sample data - Suppliers
suppliers = [
    (1, 'TechSupplies Inc.', 'Mark Johnson', 'mark@techsupplies.com', '555-111-2222', '100 Tech Pkwy', 'San Jose', 'CA', '95123'),
    (2, 'HomeGoods Co.', 'Susan Lee', 'susan@homegoods.com', '555-222-3333', '200 Home Blvd', 'Seattle', 'WA', '98101'),
    (3, 'Foods & More', 'James Wilson', 'james@foodsmore.com', '555-333-4444', '300 Market St', 'Chicago', 'IL', '60603'),
    (4, 'Clothing Unlimited', 'Maria Garcia', 'maria@clothingunltd.com', '555-444-5555', '400 Fashion Ave', 'New York', 'NY', '10018')
]

# Sample data - Products
products = [
    (1, 'Laptop Pro', 'Electronics', 1299.99, 'High-performance laptop with 16GB RAM', 25, 1, '2022-01-10'),
    (2, 'Wireless Mouse', 'Electronics', 29.99, 'Ergonomic wireless mouse', 100, 1, '2022-01-15'),
    (3, 'Coffee Maker', 'Kitchen', 79.99, 'Programmable 12-cup coffee maker', 40, 2, '2022-02-05'),
    (4, 'Bath Towel Set', 'Home', 34.99, 'Set of 4 premium cotton bath towels', 75, 2, '2022-02-10'),
    (5, 'Organic Apples', 'Groceries', 4.99, 'Bag of 6 organic apples', 150, 3, '2022-03-01'),
    (6, 'Protein Bars', 'Groceries', 9.99, 'Box of 12 protein bars', 200, 3, '2022-03-05'),
    (7, 'T-Shirt', 'Clothing', 19.99, 'Cotton graphic t-shirt', 120, 4, '2022-04-10'),
    (8, 'Jeans', 'Clothing', 49.99, 'Classic fit denim jeans', 85, 4, '2022-04-15'),
    (9, 'Bluetooth Speaker', 'Electronics', 89.99, 'Portable waterproof speaker', 30, 1, '2022-05-10'),
    (10, 'LED Desk Lamp', 'Home', 24.99, 'Adjustable LED desk lamp with USB charging port', 60, 2, '2022-05-15')
]

# Generate random orders
orders = []
order_items = []
order_id = 1
item_id = 1

# Generate orders for the past year
for month in range(1, 13):
    # Each customer makes 1-3 orders per month
    for customer_id in range(1, 9):
        num_orders = random.randint(0, 3)  # Some customers might not order every month
        for _ in range(num_orders):
            # Generate random date in the month
            day = random.randint(1, 28)
            date = datetime.date(2023, month, day).isoformat()
            
            # Pick random payment method
            payment = random.choice(['Credit Card', 'PayPal', 'Apple Pay', 'Google Pay'])
            
            # Start with empty order
            order_total = 0
            
            # Add to orders table (status will be updated later)
            orders.append((order_id, customer_id, date, 0, 'Pending', payment))
            
            # Add 1-5 items to order
            num_items = random.randint(1, 5)
            order_product_ids = random.sample(range(1, 11), min(num_items, 10))
            
            for product_id in order_product_ids:
                # Find product price from products list
                product_price = next((p[3] for p in products if p[0] == product_id), 0)
                quantity = random.randint(1, 3)
                subtotal = product_price * quantity
                
                # Add to order_items
                order_items.append((item_id, order_id, product_id, quantity, product_price, subtotal))
                item_id += 1
                
                # Add to order total
                order_total += subtotal
            
            # Update the order with the calculated total
            orders[len(orders)-1] = (order_id, customer_id, date, round(order_total, 2), 
                                     random.choice(['Completed', 'Shipped', 'Delivered', 'Cancelled']), payment)
            
            order_id += 1

# Insert data into tables
cursor.executemany('INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?)', customers)
cursor.executemany('INSERT INTO suppliers VALUES (?,?,?,?,?,?,?,?,?)', suppliers)
cursor.executemany('INSERT INTO products VALUES (?,?,?,?,?,?,?,?)', products)
cursor.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)', orders)
cursor.executemany('INSERT INTO order_items VALUES (?,?,?,?,?,?)', order_items)

conn.commit()
conn.close()

print('Sample retail database created successfully: sample_retail.db')
print(f'Created tables: customers ({len(customers)} rows), suppliers ({len(suppliers)} rows), products ({len(products)} rows)')
print(f'Generated {len(orders)} orders with {len(order_items)} order items') 