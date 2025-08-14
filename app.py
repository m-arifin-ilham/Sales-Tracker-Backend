from flask import Flask, request, jsonify, g
import sqlite3
from datetime import datetime, timezone
import requests  # For making HTTP requests to Product Catalog API
import os
from dotenv import load_dotenv
from flask_cors import CORS  # Import CORS
import jwt

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Initialize CORS for your Flask app. This will allow all origins by default.

# --- Configuration ---
DATABASE_NAME = "sales.db"
# Get Product Catalog API URL and API Key from environment variables
PRODUCT_CATALOG_API_URL = os.getenv("PRODUCT_CATALOG_API_URL")
PRODUCT_CATALOG_API_KEY = os.getenv("PRODUCT_CATALOG_API_KEY")

# Get JWT Secret Key from .env (same as your User Management API)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ALGORITHM"] = "HS256"  # Must match your User Management API

# Basic check to ensure the URL and Key is set
if not PRODUCT_CATALOG_API_URL:
    raise RuntimeError("PRODUCT_CATALOG_API_URL environment variable is not set.")
if not PRODUCT_CATALOG_API_KEY:
    raise RuntimeError("PRODUCT_CATALOG_API_KEY environment variable is not set.")
# Check for JWT_SECRET_KEY
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set in .env.")


# --- Database Connection Helper ---
def get_db_connection():
    """Establishes a connection to the SQLite database for sales."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing rows as dictionaries
    return conn


# --- JWT Verification Decorator ---
def jwt_required(f):
    def wrapper(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Authorization Token is missing!"}), 401

        try:
            # Decode the token using the secret key from app.config
            data = jwt.decode(
                token,
                app.config["JWT_SECRET_KEY"],
                algorithms=[app.config["JWT_ALGORITHM"]],
            )

            # Ensure it's an access token from your User Management API
            if data.get("type") != "access":
                return (
                    jsonify(
                        {"message": "Invalid token type. An Access Token is required."}
                    ),
                    401,
                )

            # Check token expiration
            if datetime.now(timezone.utc).timestamp() > data["exp"]:
                return jsonify({"message": "Token has expired!"}), 401

            g.user = data  # Store decoded user info in Flask's global 'g' object
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid!"}), 401
        except Exception as e:
            return jsonify({"message": f"Token error: {str(e)}"}), 401

        return f(*args, **kwargs)

    wrapper.__name__ = (
        f.__name__
    )  # Important for Flask to recognize decorated functions
    return wrapper


# --- API Endpoints ---


# GET all sales records
@app.route("/sales", methods=["GET"])
@jwt_required
def get_sales():
    """
    Retrieves all sales records from the database for the authenticated user.
    (For simplicity, currently retrieves all sales regardless of user_id,
    but can be filtered by user_id in future.)
    """
    conn = get_db_connection()
    sales = conn.execute("SELECT * FROM sales ORDER BY sale_date DESC").fetchall()
    conn.close()

    # Convert sqlite3.Row objects to dictionaries for jsonify
    sales_list = [dict(sale) for sale in sales]
    return jsonify(sales_list)


# CREATE a new sales record
@app.route("/sales", methods=["POST"])
@jwt_required
def create_sale():
    """
    Creates a new sales record.
    Integrates with Product Catalog API to get product price and decrement stock.
    Associates the sale with the authenticated user.
    """
    data = request.get_json()

    # Get user_id from the authenticated token
    user_id = g.user["user_id"]  # This is available because of @jwt_required

    # 1. Basic Input Validation
    if not data:
        return jsonify({"message": "Request body cannot be empty."}), 400

    product_id = data.get("product_id")
    quantity_sold = data.get("quantity_sold")

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
        # Add headers for API Key authentication to GET request if needed (optional, but good practice if GETs are also protected)
        # For now, GET is public, so no headers needed here.
        product_response = requests.get(
            f"{PRODUCT_CATALOG_API_URL}/products/{product_id}/"
        )

        if product_response.status_code == 404:
            return (
                jsonify(
                    {"message": f"Product with ID {product_id} not found in catalog."}
                ),
                404,
            )
        elif product_response.status_code == 403:
            return (
                jsonify(
                    {
                        "message": f"Forbidden to access product details (CORS/permissions issue on GET). Check Django API key setup."
                    }
                ),
                403,
            )
        elif product_response.status_code != 200:
            # Handle other potential errors from catalog API
            return (
                jsonify(
                    {
                        "message": f"Error fetching product from catalog: {product_response.text}"
                    }
                ),
                product_response.status_code,
            )

        product_details = product_response.json()
        product_price = product_details.get("price")
        product_stock = product_details.get("stock_quantity")

        if product_price is None:  # Should not happen if product found, but good check
            return (
                jsonify({"message": "Product price not available from catalog."}),
                500,
            )

        # Convert price to float for calculation (it comes as string from DRF JSON)
        product_price = float(product_price)

        # Check stock quantity before proceeding
        if product_stock is None or product_stock < quantity_sold:
            return (
                jsonify(
                    {
                        "message": f"Not enough stock for product ID {product_id}. Available: {product_stock}, Requested: {quantity_sold}."
                    }
                ),
                400,
            )

        # Now, call the purchase endpoint on the Product Catalog API to decrement stock with API Key
        purchase_payload = {"quantity": quantity_sold}
        purchase_headers = {
            "Authorization": f"Api-Key {PRODUCT_CATALOG_API_KEY}"
        }  # Add API Key header

        purchase_response = requests.post(
            f"{PRODUCT_CATALOG_API_URL}/products/{product_id}/purchase/",
            json=purchase_payload,
            headers=purchase_headers,  # Pass headers
        )

        if purchase_response.status_code == 403:
            return (
                jsonify(
                    {
                        "message": f"Failed to update product stock in catalog: Authentication failed. Check PRODUCT_CATALOG_API_KEY."
                    }
                ),
                403,
            )
        elif purchase_response.status_code != 200:
            # If stock update fails, we should ideally rollback the sale if it was already recorded.
            # For this demo, we'll return an error and not record the sale.
            return (
                jsonify(
                    {
                        "message": f"Failed to update product stock in catalog: {purchase_response.text}"
                    }
                ),
                purchase_response.status_code,
            )

    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "message": "Could not connect to Product Catalog API. Please ensure it is running."
                }
            ),
            503,
        )  # Service Unavailable
    except Exception as e:
        return (
            jsonify(
                {
                    "message": f"An unexpected error occurred during product catalog interaction: {str(e)}"
                }
            ),
            500,
        )

    # 3. Calculate Total Revenue
    total_revenue = product_price * quantity_sold

    # 4. Store Sale Record in Sales Database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sales (user_id, product_id, quantity_sold, total_revenue, sale_date) VALUES (?, ?, ?, ?, ?)",
            (
                user_id,
                product_id,
                quantity_sold,
                total_revenue,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        sale_id = cursor.lastrowid

        # Return the created sale record
        new_sale = conn.execute(
            "SELECT * FROM sales WHERE id = ?", (sale_id,)
        ).fetchone()
        return jsonify(dict(new_sale)), 201  # 201 Created
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"message": "Database error storing sale", "error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize the sales database when app.py is run directly
    # This part should ideally be in database.py's __main__ block,
    # but kept here for simplicity.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            total_revenue REAL NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()
    print("Sales database initialized (if not already).")
    app.run(debug=True, port=5001)
