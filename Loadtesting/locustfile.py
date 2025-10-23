import random
import json
from locust import HttpUser, FastHttpUser, task, between

class ProductAPIUser(HttpUser):
    """Standard HttpUser implementation using requests library"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize user session with some data"""
        self.product_ids = ["1", "2", "3"]  # Initial product IDs
        self.created_products = []  # Track products created by this user
        self.product_counter = 1000  # Start creating products from ID 1000

    @task(9)  # Weight of 9 for GET requests (3:1 ratio)
    def get_products(self):
        """Test GET endpoints - both all products and specific products"""
        # Randomly choose between getting all products or a specific product
        if random.random() < 0.5:  # 50% chance for each type
            # Get all products
            with self.client.get("/products", catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    if "products" in data:
                        response.success()
                    else:
                        response.failure("Response missing 'products' field")
                else:
                    response.failure(f"Got status code {response.status_code}")
        else:
            # Get specific product by ID
            if random.random() < 0.8:  # 80% valid requests
                product_id = random.choice(self.product_ids + self.created_products)
            else:  # 20% invalid requests to test 404
                product_id = f"nonexistent_{random.randint(1, 100)}"

            with self.client.get(f"/products/{product_id}", catch_response=True) as response:
                if product_id.startswith("nonexistent"):
                    if response.status_code == 404:
                        response.success()
                    else:
                        response.failure(f"Expected 404 for non-existent product, got {response.status_code}")
                else:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Expected 200 for existing product, got {response.status_code}")

    @task(2)  # Weight of 2 for valid POST
    def create_valid_product(self):
        """Test POST /products with valid data"""
        product_id = f"test_{self.product_counter}"
        self.product_counter += 1

        product_data = {
            "id": product_id,
            "name": f"Product {product_id}",
            "description": f"Description for product {product_id}",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(0, 100)
        }

        headers = {"Content-Type": "application/json"}
        with self.client.post("/products",
                              data=json.dumps(product_data),
                              headers=headers,
                              catch_response=True) as response:
            if response.status_code == 201:
                self.created_products.append(product_id)
                response.success()
            elif response.status_code == 409:
                # Conflict is expected if ID already exists
                response.success()
            else:
                response.failure(f"Got unexpected status code {response.status_code}")

    @task(1)  # Weight of 1 for invalid POST
    def create_invalid_or_duplicate_product(self):
        """Test POST /products with invalid data or duplicate IDs"""
        if random.random() < 0.7:  # 70% invalid data, 30% duplicate
            # Invalid data scenarios
            invalid_scenarios = [
                # Missing required fields
                {
                    "description": "Product without ID, name, or price",
                    "stock": 10
                },
                # Invalid price (zero)
                {
                    "id": f"invalid_{random.randint(1, 1000)}",
                    "name": "Free Product",
                    "price": 0,
                    "stock": 5
                },
                # Invalid price (negative)
                {
                    "id": f"invalid_{random.randint(1, 1000)}",
                    "name": "Negative Price Product",
                    "price": -10.99,
                    "stock": 5
                },
                # Invalid stock (negative)
                {
                    "id": f"invalid_{random.randint(1, 1000)}",
                    "name": "Negative Stock Product",
                    "price": 50.00,
                    "stock": -5
                },
                # Empty name
                {
                    "id": f"invalid_{random.randint(1, 1000)}",
                    "name": "",
                    "price": 100.00,
                    "stock": 10
                }
            ]

            invalid_data = random.choice(invalid_scenarios)
            headers = {"Content-Type": "application/json"}

            with self.client.post("/products",
                                  data=json.dumps(invalid_data),
                                  headers=headers,
                                  catch_response=True) as response:
                if response.status_code == 400:
                    response.success()
                else:
                    response.failure(f"Expected 400 for invalid data, got {response.status_code}")
        else:
            # Duplicate ID scenario
            existing_id = random.choice(self.product_ids)

            product_data = {
                "id": existing_id,
                "name": "Duplicate Product",
                "description": "This should fail with 409",
                "price": 99.99,
                "stock": 10
            }

            headers = {"Content-Type": "application/json"}
            with self.client.post("/products",
                                  data=json.dumps(product_data),
                                  headers=headers,
                                  catch_response=True) as response:
                if response.status_code == 409:
                    response.success()
                else:
                    response.failure(f"Expected 409 for duplicate ID, got {response.status_code}")


class ProductAPIFastUser(FastHttpUser):
    """FastHttpUser implementation using geventhttpclient for better performance"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize user session with some data"""
        self.product_ids = ["1", "2", "3"]  # Initial product IDs
        self.created_products = []  # Track products created by this user
        self.product_counter = 2000  # Start from 2000 to avoid conflicts with HttpUser

    @task(9)  # Weight of 9 for GET requests (3:1 ratio)
    def get_products(self):
        """Test GET endpoints - both all products and specific products"""
        # Randomly choose between getting all products or a specific product
        if random.random() < 0.5:  # 50% chance for each type
            # Get all products
            response = self.client.get("/products")
            if response.status_code == 200:
                data = json.loads(response.text)
                if "products" not in data:
                    response.failure("Response missing 'products' field")
            else:
                response.failure(f"Got status code {response.status_code}")
        else:
            # Get specific product by ID
            if random.random() < 0.8:  # 80% valid requests
                product_id = random.choice(self.product_ids + self.created_products)
            else:  # 20% invalid requests to test 404
                product_id = f"nonexistent_{random.randint(1, 100)}"

            response = self.client.get(f"/products/{product_id}")
            if product_id.startswith("nonexistent"):
                if response.status_code != 404:
                    response.failure(f"Expected 404 for non-existent product, got {response.status_code}")
            else:
                if response.status_code != 200:
                    response.failure(f"Expected 200 for existing product, got {response.status_code}")

    @task(2)  # Weight of 2 for valid POST
    def create_valid_product(self):
        """Test POST /products with valid data"""
        product_id = f"fast_test_{self.product_counter}"
        self.product_counter += 1

        product_data = {
            "id": product_id,
            "name": f"Fast Product {product_id}",
            "description": f"Description for fast product {product_id}",
            "price": round(random.uniform(10.0, 1000.0), 2),
            "stock": random.randint(0, 100)
        }

        headers = {"Content-Type": "application/json"}
        response = self.client.post("/products",
                                    data=json.dumps(product_data),
                                    headers=headers)

        if response.status_code == 201:
            self.created_products.append(product_id)
        elif response.status_code == 409:
            # Conflict is expected if ID already exists
            pass
        else:
            response.failure(f"Got unexpected status code {response.status_code}")

    @task(1)  # Weight of 1 for invalid POST
    def create_invalid_or_duplicate_product(self):
        """Test POST /products with invalid data or duplicate IDs"""
        if random.random() < 0.7:  # 70% invalid data, 30% duplicate
            # Invalid data scenarios
            invalid_scenarios = [
                # Missing required fields
                {
                    "description": "Product without ID, name, or price",
                    "stock": 10
                },
                # Invalid price (zero)
                {
                    "id": f"fast_invalid_{random.randint(1, 1000)}",
                    "name": "Free Product",
                    "price": 0,
                    "stock": 5
                },
                # Invalid price (negative)
                {
                    "id": f"fast_invalid_{random.randint(1, 1000)}",
                    "name": "Negative Price Product",
                    "price": -10.99,
                    "stock": 5
                },
                # Invalid stock (negative)
                {
                    "id": f"fast_invalid_{random.randint(1, 1000)}",
                    "name": "Negative Stock Product",
                    "price": 50.00,
                    "stock": -5
                },
                # Empty name
                {
                    "id": f"fast_invalid_{random.randint(1, 1000)}",
                    "name": "",
                    "price": 100.00,
                    "stock": 10
                }
            ]

            invalid_data = random.choice(invalid_scenarios)
            headers = {"Content-Type": "application/json"}

            response = self.client.post("/products",
                                        data=json.dumps(invalid_data),
                                        headers=headers)

            if response.status_code != 400:
                response.failure(f"Expected 400 for invalid data, got {response.status_code}")
        else:
            # Duplicate ID scenario
            existing_id = random.choice(self.product_ids)

            product_data = {
                "id": existing_id,
                "name": "Fast Duplicate Product",
                "description": "This should fail with 409",
                "price": 99.99,
                "stock": 10
            }

            headers = {"Content-Type": "application/json"}
            response = self.client.post("/products",
                                        data=json.dumps(product_data),
                                        headers=headers)

            if response.status_code != 409:
                response.failure(f"Expected 409 for duplicate ID, got {response.status_code}")
