import requests
import json
import os
from dotenv import load_dotenv
import time  # For testing token expiration (optional)

# Load environment variables
load_dotenv()

# --- Configuration ---
SALES_API_BASE_URL = "http://127.0.0.1:5001"  # Base URL for your Sales Tracker API
USER_MANAGEMENT_API_URL = (
    "http://127.0.0.1:5000"  # Base URL for your User Management API
)
PRODUCT_CATALOG_API_URL = os.getenv(
    "PRODUCT_CATALOG_API_URL"
)  # URL for your Django Product Catalog API

# Test User Credentials (from your User Management API)
# Use an existing user from your User Management API (e.g., the 'admin' user or a registered regular user)
TEST_USER_CREDENTIALS = {
    "username_or_email": "admin",  # Or a regular user's username/email
    "password": "admin_password_123",  # Or the password for your chosen user
}

# --- Test Data ---
# You'll need an actual product ID from your Product Catalog API for this test.
# Run your Django Product Catalog API locally (python manage.py runserver)
# and create a product in its admin panel or via its API, then get its ID.
# For example, if you created "Animal Farm" with ID 1 in Django:
TEST_PRODUCT_ID = (
    1  # <<< IMPORTANT: Replace with a valid product ID from your Product Catalog API
)

# --- Global Variables for Tokens ---
access_token = ""
refresh_token = ""


# --- Helper Functions ---
def print_status(message, response):
    """Prints the status code and response for an API call."""
    print(f"\n--- {message} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")


def make_request(method, base_url, endpoint, data=None, token=None):
    """A helper function to make API requests with optional authentication."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{base_url}{endpoint}"

    if method == "POST":
        return requests.post(url, json=data, headers=headers)
    elif method == "GET":
        return requests.get(url, params=data, headers=headers)
    # Add PUT/DELETE if needed later


# --- Authentication Flow ---
def login_user_and_get_tokens():
    """Logs into the User Management API and stores tokens."""
    global access_token, refresh_token
    print("\n--- Logging into User Management API ---")
    response = make_request(
        "POST", USER_MANAGEMENT_API_URL, "/login", TEST_USER_CREDENTIALS
    )
    print_status("User Management Login", response)
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]
        print("Tokens obtained successfully.")
        return True
    else:
        print(
            "Failed to log in to User Management API. Please check credentials and ensure it's running."
        )
        return False


# Data for creating a new sales record
VALID_SALE_PAYLOAD = {"product_id": TEST_PRODUCT_ID, "quantity_sold": 2}
# This payload assumes your product has limited stock. Adjust quantity if needed.
INVALID_SALE_PAYLOAD_INSUFFICIENT_QTY = {
    "product_id": TEST_PRODUCT_ID,
    "quantity_sold": 9999999,  # A very large quantity
}
INVALID_SALE_PAYLOAD_INVALID_ID = {
    "product_id": 999999,  # Non-existent product ID
    "quantity_sold": 1,
}
INVALID_SALE_PAYLOAD_MISSING_QTY = {"product_id": TEST_PRODUCT_ID}
INVALID_SALE_PAYLOAD_ZERO_QTY = {"product_id": TEST_PRODUCT_ID, "quantity_sold": 0}
INVALID_SALE_PAYLOAD_NEGATIVE_QTY = {"product_id": TEST_PRODUCT_ID, "quantity_sold": -1}


# --- Main Test Execution ---
def run_tests():
    global access_token, refresh_token

    print("--- Starting Sales Tracker API Tests ---")
    print(f"Product Catalog API URL: {PRODUCT_CATALOG_API_URL}")
    print(f"Using TEST_PRODUCT_ID: {TEST_PRODUCT_ID}")

    # Ensure Product Catalog API is running (if using local URL)
    try:
        product_response = requests.get(
            f"{PRODUCT_CATALOG_API_URL}/products/{TEST_PRODUCT_ID}/"
        )
        if product_response.status_code == 200:
            print(
                f"Successfully connected to Product Catalog API for product ID {TEST_PRODUCT_ID}."
            )
        else:
            print(
                f"WARNING: Could not connect to Product Catalog API for product ID {TEST_PRODUCT_ID}. Status: {product_response.status_code}"
            )
            print(
                "Please ensure your Product Catalog API is running and TEST_PRODUCT_ID is valid."
            )
            return
    except requests.exceptions.ConnectionError:
        print(
            "ERROR: Could not connect to Product Catalog API. Please ensure it is running."
        )
        return

    # Log in to User Management API
    if not login_user_and_get_tokens():
        return  # Stop if login fails

    # 1. Test Sales Tracker API Endpoints (Authenticated)
    print("\n\n#################################################")
    print("#  TESTS FOR SALES TRACKER API (AUTHENTICATED)  #")
    print("#################################################")

    # Test 1.1: Create a valid sales record (authenticated)
    print("\nTest 1.1: Creating a valid sales record (authenticated)...")
    response = make_request(
        "POST", SALES_API_BASE_URL, "/sales", VALID_SALE_PAYLOAD, token=access_token
    )
    print_status("Create Sale (Valid & Authenticated)", response)
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["product_id"] == VALID_SALE_PAYLOAD["product_id"]
    assert response.json()["quantity_sold"] == VALID_SALE_PAYLOAD["quantity_sold"]
    assert response.json()["total_revenue"] > 0  # Should be calculated

    # Test 1.2: Get all sales records (authenticated)
    print("\nTest 1.2: Getting all sales records (authenticated)...")
    response = make_request("GET", SALES_API_BASE_URL, "/sales", token=access_token)
    print_status("Get All Sales (Authenticated)", response)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1  # Should have at least the one just created

    # Test 1.3: Create a sales record with insufficient stock (authenticated)
    print(
        "\nTest 1.3: Creating a sales record with insufficient stock (authenticated)..."
    )
    response = make_request(
        "POST",
        SALES_API_BASE_URL,
        "/sales",
        INVALID_SALE_PAYLOAD_INSUFFICIENT_QTY,
        token=access_token,
    )
    print_status("Create Sale (Insufficient Stock)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "Not enough stock" in response.json()["message"]

    # Test 1.4: Create a sales record with invalid product ID (authenticated)
    print(
        "\nTest 1.4: Creating a sales record with invalid product ID (authenticated)..."
    )
    response = make_request(
        "POST",
        SALES_API_BASE_URL,
        "/sales",
        INVALID_SALE_PAYLOAD_INVALID_ID,
        token=access_token,
    )
    print_status("Create Sale (Invalid Product ID)", response)
    assert response.status_code == 404
    assert "message" in response.json()
    assert (
        "Product with ID" in response.json()["message"]
        and "not found" in response.json()["message"]
    )

    # Test 1.5: Create a sales record with missing quantity
    print(
        "\nTest 1.5: Creating a sales record with missing quantity (authenticated)..."
    )
    response = make_request(
        "POST",
        SALES_API_BASE_URL,
        "/sales",
        INVALID_SALE_PAYLOAD_MISSING_QTY,
        token=access_token,
    )
    print_status("Create Sale (Missing Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "quantity_sold is required" in response.json()["message"]

    # Test 1.6: Create a sales record with zero quantity
    print("\nTest 1.6: Creating a sales record with zero quantity (authenticated)...")
    response = make_request(
        "POST",
        SALES_API_BASE_URL,
        "/sales",
        INVALID_SALE_PAYLOAD_ZERO_QTY,
        token=access_token,
    )
    print_status("Create Sale (Zero Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "Quantity sold must be a positive integer" in response.json()["message"]

    # Test 1.7: Create a sales record with negative quantity
    print(
        "\nTest 1.7: Creating a sales record with negative quantity (authenticated)..."
    )
    response = make_request(
        "POST",
        SALES_API_BASE_URL,
        "/sales",
        INVALID_SALE_PAYLOAD_NEGATIVE_QTY,
        token=access_token,
    )
    print_status("Create Sale (Negative Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "Quantity sold must be a positive integer" in response.json()["message"]

    # 2. Test Sales Tracker API Endpoints (Unauthenticated / Invalid Token)
    print("\n\n#####################################################")
    print("#  TESTS FOR SALES TRACKER API (UNAUTHENTICATED)  #")
    print("#####################################################")

    # Test 2.1: Get all sales records (unauthenticated)
    print("\nTest 2.1: Getting all sales records (unauthenticated)...")
    response = make_request("GET", SALES_API_BASE_URL, "/sales")  # No token
    print_status("Get All Sales (Unauthenticated)", response)
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Authorization Token is missing!" in response.json()["message"]

    # Test 2.2: Create a sales record (unauthenticated)
    print("\nTest 2.2: Creating a sales record (unauthenticated)...")
    response = make_request(
        "POST", SALES_API_BASE_URL, "/sales", VALID_SALE_PAYLOAD
    )  # No token
    print_status("Create Sale (Unauthenticated)", response)
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Authorization Token is missing!" in response.json()["message"]

    # Test 2.3: Get all sales records (invalid token)
    print("\nTest 2.3: Getting all sales records (invalid token)...")
    response = make_request(
        "GET", SALES_API_BASE_URL, "/sales", token="invalid.jwt.token"
    )
    print_status("Get All Sales (Invalid Token)", response)
    assert response.status_code == 401
    assert "message" in response.json()
    assert "Token is invalid!" in response.json()["message"]

    # Test 2.4: Create a sales record (expired token) - OPTIONAL
    # To test this, you'd need to modify your User Management API's JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    # to a very short time (e.g., 0.01 minutes), restart it, log in, wait, then run this test.
    # print("\nTest 2.4: Creating a sales record (expired token)...")
    # time.sleep(1) # Wait for token to expire if set to 1 second
    # response = make_request("POST", SALES_API_BASE_URL, "/sales", valid_sale_payload, token=access_token)
    # print_status("Create Sale (Expired Token)", response)
    # assert response.status_code == 401
    # assert "Token has expired!" in response.json()["message"]

    print("\n--- Sales Tracker API Tests Completed ---")


if __name__ == "__main__":
    # Ensure your Flask app is NOT running yet.
    # Ensure your Django Product Catalog API is running on http://127.0.0.1:8000
    # And you have a product with TEST_PRODUCT_ID in it.
    run_tests()
