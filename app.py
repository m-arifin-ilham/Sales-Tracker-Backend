from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timezone
import requests # For making HTTP requests to Product Catalog API
import os
from dotenv import load_dotenv
from flask_cors import CORS # Import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # Initialize CORS for your Flask app. This will allow all origins by default.

# --- Configuration ---
DATABASE_NAME = 'sales.db'
# Get Product Catalog API URL from environment variables
PRODUCT_CATALOG_API_URL = os.getenv('PRODUCT_CATALOG_API_URL')

# Basic check to ensure the URL is set
if not PRODUCT_CATALOG_API_URL:
    raise RuntimeError("PRODUCT_CATALOG_API_URL environment variable is not set.")

# --- Database Connection Helper ---
def get_db_connection():
    """Establishes a connection to the SQLite database for sales."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing rows as dictionaries
    return conn

# --- API Endpoints ---

@app.route('/sales', methods=['GET'])
def get_sales():
    """
    Retrieves all sales records from the database.
    """
    conn = get_db_connection()
    sales = conn.execute('SELECT * FROM sales ORDER BY sale_date DESC').fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to dictionaries for jsonify
    sales_list = [dict(sale) for sale in sales]
    return jsonify(sales_list)


@app.route('/sales', methods=['POST'])
def create_sale():
    """
    Creates a new sales record.
    Integrates with Product Catalog API to get product price and decrement stock.
    """
    data = request.get_json()

    # 1. Basic Input Validation
    if not data:
        return jsonify({"message": "Request body cannot be empty."}), 400
    
    product_id = data.get('product_id')
    quantity_sold = data.get('quantity_sold')

    if not product_id:
        return jsonify({"message": "product_id is required."}), 400
    if not isinstance(product_id, int) or product_id <= 0:
        return jsonify({"message": "product_id must be a positive integer."}), 400

    if not quantity_sold and quantity_sold != 0:
        return jsonify({"message": "quantity_sold is required."}), 400
    if not isinstance(quantity_sold, int) or quantity_sold <= 0:
        return jsonify({"message": "Quantity sold must be a positive integer."}), 400

    # 2. Integrate with Product Catalog API
    product_details = None
    try:
        # Call Product Catalog API to get product details
        product_response = requests.get(f"{PRODUCT_CATALOG_API_URL}/products/{product_id}/")
        
        if product_response.status_code == 404:
            return jsonify({"message": f"Product with ID {product_id} not found in catalog."}), 404
        elif product_response.status_code != 200:
            # Handle other potential errors from catalog API
            return jsonify({"message": f"Error fetching product from catalog: {product_response.text}"}), product_response.status_code
        
        product_details = product_response.json()
        product_price = product_details.get('price')
        product_stock = product_details.get('stock_quantity')

        if product_price is None: # Should not happen if product found, but good check
            return jsonify({"message": "Product price not available from catalog."}), 500
        
        # Convert price to float for calculation (it comes as string from DRF JSON)
        product_price = float(product_price)

        # Check stock quantity before proceeding
        if product_stock is None or product_stock < quantity_sold:
            return jsonify({"message": f"Not enough stock for product ID {product_id}. Available: {product_stock}, Requested: {quantity_sold}."}), 400

        # Now, call the purchase endpoint on the Product Catalog API to decrement stock
        purchase_payload = {"quantity": quantity_sold}
        purchase_response = requests.post(
            f"{PRODUCT_CATALOG_API_URL}/products/{product_id}/purchase/",
            json=purchase_payload
        )
        
        if purchase_response.status_code != 200:
            # If stock update fails, we should ideally rollback the sale if it was already recorded.
            # For this demo, we'll return an error and not record the sale.
            return jsonify({"message": f"Failed to update product stock in catalog: {purchase_response.text}"}), purchase_response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"message": "Could not connect to Product Catalog API. Please ensure it is running."}), 503 # Service Unavailable
    except Exception as e:
        return jsonify({"message": f"An unexpected error occurred during product catalog interaction: {str(e)}"}), 500

    # 3. Calculate Total Revenue
    total_revenue = product_price * quantity_sold

    # 4. Store Sale Record in Sales Database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sales (product_id, quantity_sold, total_revenue, sale_date) VALUES (?, ?, ?, ?)",
            (product_id, quantity_sold, total_revenue, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        sale_id = cursor.lastrowid

        # Return the created sale record
        new_sale = conn.execute('SELECT * FROM sales WHERE id = ?', (sale_id,)).fetchone()
        return jsonify(dict(new_sale)), 201 # 201 Created
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"message": "Database error storing sale", "error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize the sales database when app.py is run directly
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            total_revenue REAL NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Sales database initialized (if not already).")
    app.run(debug=True)
