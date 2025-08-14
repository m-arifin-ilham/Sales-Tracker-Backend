import sqlite3
from datetime import datetime

DATABASE_NAME = "sales.db"


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing rows as dictionaries
    return conn


def init_db():
    """Initializes the database schema for sales records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,  -- ID of the product from Product Catalog API
            quantity_sold INTEGER NOT NULL,
            total_revenue REAL NOT NULL,  -- Calculated from product price * quantity
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()
    print("Sales database initialized or already exists.")


if __name__ == "__main__":
    # This block runs only when database.py is executed directly
    init_db()
    print("Database setup complete.")
