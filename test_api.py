import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
BASE_URL = "http://127.0.0.1:5000" # Base URL for your Sales Tracker API
PRODUCT_CATALOG_API_URL = os.getenv('PRODUCT_CATALOG_API_URL') # URL for your Product Catalog API

# --- Helper Functions ---
def print_status(message, response):
    """Prints the status code and response for an API call."""
    print(f"\n--- {message} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")

def make_request(method, endpoint, data=None):
    """A helper function to make API requests to the Sales Tracker API."""
    headers = {"Content-Type": "application/json"}
    url = f"{BASE_URL}{endpoint}"
    
    if method == "POST":
        return requests.post(url, json=data, headers=headers)
    elif method == "GET":
        return requests.get(url, params=data, headers=headers)
    # Add PUT/DELETE if needed later

# --- Test Data ---
# You'll need an actual product ID from your Product Catalog API for this test.
# Run your Django Product Catalog API locally (python manage.py runserver)
# and create a product in its admin panel or via its API, then get its ID.
# For example, if you created "Animal Farm" with ID 1 in Django:
TEST_PRODUCT_ID = 1 # <<< IMPORTANT: Replace with a valid product ID from your Product Catalog API

# Data for creating a new sales record
VALID_SALE_PAYLOAD = {
    "product_id": TEST_PRODUCT_ID,
    "quantity_sold": 2
}
INVALID_SALE_PAYLOAD_MISSING_QTY = {
    "product_id": TEST_PRODUCT_ID
}
INVALID_SALE_PAYLOAD_ZERO_QTY = {
    "product_id": TEST_PRODUCT_ID,
    "quantity_sold": 0
}
INVALID_SALE_PAYLOAD_NEGATIVE_QTY = {
    "product_id": TEST_PRODUCT_ID,
    "quantity_sold": -1
}

# --- Main Test Execution ---
def run_tests():
    print("--- Starting Sales Tracker API Tests ---")
    print(f"Product Catalog API URL: {PRODUCT_CATALOG_API_URL}")
    print(f"Using TEST_PRODUCT_ID: {TEST_PRODUCT_ID}")

    # Ensure Product Catalog API is running (if using local URL)
    try:
        product_response = requests.get(f"{PRODUCT_CATALOG_API_URL}/products/{TEST_PRODUCT_ID}/")
        if product_response.status_code == 200:
            print(f"Successfully connected to Product Catalog API for product ID {TEST_PRODUCT_ID}.")
        else:
            print(f"WARNING: Could not connect to Product Catalog API for product ID {TEST_PRODUCT_ID}. Status: {product_response.status_code}")
            print("Please ensure your Product Catalog API is running and TEST_PRODUCT_ID is valid.")
            return
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Product Catalog API. Please ensure it is running.")
        return

    # Test 1: Create a valid sales record
    print("\nTest 1.1: Creating a valid sales record...")
    response = make_request("POST", "/sales", VALID_SALE_PAYLOAD)
    print_status("Create Sale (Valid)", response)
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["product_id"] == VALID_SALE_PAYLOAD["product_id"]
    assert response.json()["quantity_sold"] == VALID_SALE_PAYLOAD["quantity_sold"]
    assert response.json()["total_revenue"] > 0 # Should be calculated

    # Test 2: Create a sales record with missing quantity
    print("\nTest 1.2: Creating a sales record with missing quantity...")
    response = make_request("POST", "/sales", INVALID_SALE_PAYLOAD_MISSING_QTY)
    print_status("Create Sale (Missing Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "quantity_sold is required" in response.json()["message"]

    # Test 3: Create a sales record with zero quantity
    print("\nTest 1.3: Creating a sales record with zero quantity...")
    response = make_request("POST", "/sales", INVALID_SALE_PAYLOAD_ZERO_QTY)
    print_status("Create Sale (Zero Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "Quantity sold must be a positive integer" in response.json()["message"]

    # Test 4: Create a sales record with negative quantity
    print("\nTest 1.4: Creating a sales record with negative quantity...")
    response = make_request("POST", "/sales", INVALID_SALE_PAYLOAD_NEGATIVE_QTY)
    print_status("Create Sale (Negative Quantity)", response)
    assert response.status_code == 400
    assert "message" in response.json()
    assert "Quantity sold must be a positive integer" in response.json()["message"]

    print("\n--- Sales Tracker API Tests Completed ---")

if __name__ == "__main__":
    # Ensure your Flask app is NOT running yet.
    # Ensure your Django Product Catalog API is running on http://127.0.0.1:8000
    # And you have a product with TEST_PRODUCT_ID in it.
    run_tests()