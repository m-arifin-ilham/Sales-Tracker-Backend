# Simple Sales Tracker Backend

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgray.svg?logo=flask)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html)
[![Requests](https://img.shields.io/badge/HTTP%20Client-Requests-blue)](https://requests.readthedocs.io/en/latest/)
[![Flask-CORS](https://img.shields.io/badge/CORS-Flask--CORS-purple)](https://flask-cors.readthedocs.io/en/latest/)
[![python-dotenv](https://img.shields.io/badge/Env%20Mgmt-python--dotenv-yellowgreen)](https://pypi.org/project/python-dotenv/)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-brightgreen?style=flat&logo=github)](https://github.com/m-arifin-ilham/Sales-Tracker-Backend)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
---

## Overview

This project is the **backend API** for a Simple Sales Tracker application. Built with **Flask** and **SQLite**, its primary role is to record and manage sales data. A key feature of this API is its **integration with an external Product Catalog API** (like the [Django API](https://github.com/m-arifin-ilham/Product-Catalog-API) I've built), allowing it to fetch product details and decrement stock quantities in real-time when a sale is recorded.

This API serves as the data source for a frontend application (e.g., the [React-based Simple Sales Tracker Frontend](https://github.com/m-arifin-ilham/Sales-Tracker-Frontend) I've built) that provides user input forms and data visualizations.

## Features

* **Sales Record Creation (`POST /sales`):**
    * Allows submission of new sales, including `product_id` and `quantity_sold`.
    * **Inter-API Communication:** Fetches product details (price, stock) from an external Product Catalog API.
    * Calculates `total_revenue` based on fetched product price.
    * **Inventory Management Integration:** Calls the Product Catalog API's custom purchase endpoint to decrement product stock.
    * Includes robust data validation (e.g., positive quantity, sufficient stock, valid product ID).
* **Sales Record Listing (`GET /sales`):**
    * Retrieves a list of all recorded sales, ordered by date.
* **Sales Record Retrieval by ID (`GET /sales/{id}`):**
    * Fetches details for a specific sales record.
* **Secure Inter-API Communication:** Authenticates requests to the Product Catalog API by sending a valid API Key.
* **CORS Enabled:** Configured with `Flask-CORS` to allow cross-origin requests from frontend applications.
---

## Architectural Design

This Flask API is designed as a focused backend service. It adheres to a simple, modular structure to manage sales data and orchestrate communication with external services.

* **API Layer (`app.py`):** Handles HTTP requests, performs basic input validation, and orchestrates calls to external APIs and the database.
* **Database Layer (`database.py`):** Manages the SQLite database connection and schema initialization for sales records.
* **External API Integration:** Uses the `requests` library to communicate with the Product Catalog API, demonstrating backend-to-backend service interaction.

---

## Technologies Used

* **Python:** The core programming language.
* **Flask:** A lightweight Python web framework for building the API.
* **SQLite:** A file-based database for local development and persistence of sales data.
* **Requests:** A popular Python library for making HTTP requests to external APIs.
* **Flask-CORS:** An extension for handling Cross-Origin Resource Sharing.
* **python-dotenv:** For loading environment variables (like external API URLs).

---

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

* Python 3.8+ installed on your system.
* Your **Product Catalog API** running on `http://localhost:8000/api/`. (Ensure it has at least one product with sufficient stock for testing sales).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/m-arifin-ilham/Sales-Tracker-Backend
    cd simple_sales_tracker
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Create a file named `.env` in the project root with the following content. **Ensure `PRODUCT_CATALOG_API_URL` points to your running Django Product Catalog API, and `PRODUCT_CATALOG_API_KEY` is the key generated from Django Admin.**

    ```
    PRODUCT_CATALOG_API_URL='[http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)'
    PRODUCT_CATALOG_API_KEY='your_copied_api_key_string_here' # <<< Paste the key from Django Admin here!
    ```

5.  **Initialize the database:**
    This command will create the `sales.db` file and the `sales` table.

    ```bash
    python database.py
    ```

### Running the API

Ensure your virtual environment is active, then run the Flask application:

```bash
# Set the FLASK_APP environment variable:
# On Windows: set FLASK_APP=app.py
# On macOS/Linux: export FLASK_APP=app.py

# Start the development server:
flask run --port 5001
```

The API will be accessible at `http://127.0.0.1:5001`.

## How to Run Tests

A comprehensive test script is included to validate the API's functionality and its integration with the Product Catalog API.

1.  Ensure your **Django Product Catalog API** is running on `http://localhost:8000/api/` and has a product with the ID specified in `test_api.py` (e.g., `TEST_PRODUCT_ID = 1`) with sufficient stock.

2.  **Crucially, ensure your `PRODUCT_CATALOG_API_KEY` is correctly set in your `.env` file** for this project, as the backend will use it to authenticate with the Product Catalog API.

3.  Run the tests:
    ```bash
    python test_api.py
    ```

## Future Enhancements

* **User Authentication:** Integrate with your User Management API to restrict sales recording to authenticated users.

* **Advanced Filtering & Pagination:** Add query parameters for filtering sales by date range, product, etc., and implement pagination.

* **Error Handling:** Implement more granular error handling and custom error responses.

* **Deployment:** Deploy the API to a cloud platform like Render.

* **Database Migration:** Use a more robust database (e.g., PostgreSQL) and a migration tool for production environments.

## License

This project is licensed under the MIT License.

---

*Developed by [Muhammad Arifin Ilham](https://www.linkedin.com/in/arifin-ilham-at-ska/)*

*Current Date: August 11, 2025*