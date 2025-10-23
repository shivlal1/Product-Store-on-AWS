## Introduction 

Let's build an online store! So... we need some items in the store before we can do any business :) we'll implement a Product API based on a given OpenAPI specification.  The Product API represents a simple first step e-commerce system with endpoints for creating and retrieving products.

## Instructions

### Prepare Credentials

Retrieve you temporary credentials from Learner's Lab.
Enter your configuration when prompted:
```
aws configure
```

And set your session token:
```
aws configure set aws_session_token <YOUR-TEMP-SESSION-TOKEBN>
```

### Apply Infrastructure
```
cd terraform
terraform init
terraform apply -auto-approve
```

### Send Requests
Make sure you are in terraform folder

Get public ip address
```
aws ec2 describe-network-interfaces \
--network-interface-ids $(
    aws ecs describe-tasks \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --tasks $(
        aws ecs list-tasks \
        --cluster $(terraform output -raw ecs_cluster_name) \
        --service-name $(terraform output -raw ecs_service_name) \
        --query 'taskArns[0]' --output text
    ) \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
    --output text
) \
--query 'NetworkInterfaces[0].Association.PublicIp' \
--output text
```

Send some requests:
```
curl http://<PUBLIC-IP-ADDRESS>:8080/albums
```

## Clean Up
```
terraform destroy -auto-approve
```

# Product API Documentation

This document demonstrates how to interact with the Product API using `curl`. Each request includes the expected HTTP response code.

---

## API Endpoints Overview

| # | Endpoint | Method | Description | Expected Response |
|---|----------|--------|-------------|-----------------|
| 1 | `/products` | GET | Get all products | 200 OK |
| 2 | `/products/1` | GET | Get a specific product | 200 OK |
| 3 | `/products/999` | GET | Get a non-existent product | 404 Not Found |
| 4 | `/products` | POST | Create a valid product | 201 Created |
| 5 | `/products` | POST | Create product with missing fields | 400 Bad Request |
| 6 | `/products` | POST | Create product with invalid price | 400 Bad Request |
| 7 | `/products` | POST | Create duplicate product | 409 Conflict |

---

## CURL Examples 

( Refer in Screenshots/API-Requests folder for sample response )

```bash
# Get all products (200 OK)
curl http://localhost:8080/products

# Get a specific product (200 OK)
curl http://localhost:8080/products/1

# Get a non-existent product (404 Not Found)
curl http://localhost:8080/products/999

# Create a valid product (201 Created)
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
    "id": "4",
    "name": "Monitor",
    "description": "4K Ultra HD Monitor",
    "price": 399.99,
    "stock": 15
  }'

# Try to create a product with missing fields (400 Bad Request)
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
    "id": "5",
    "description": "Missing name and price"
  }'

# Try to create a product with invalid price (400 Bad Request)
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
    "id": "5",
    "name": "Free Product",
    "price": 0
  }'

# Try to create a duplicate product (409 Conflict)
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "name": "Another Laptop",
    "price": 799.99
  }'
```

# HttpUser vs FastHttpUser Performance Comparison

Here’s a clear comparison between **`HttpUser`** and **`FastHttpUser`** based on the performance data provided.

---

## 1. Single User Performance

| Scenario/User    | Request Type      | Median (ms) | 95th Percentile (ms) | 99th Percentile (ms) |
|------------------|------------------|-------------|----------------------|----------------------|
| HttpUser         | GET /products     | 2.27        | 4                    | 4                    |
| HttpUser         | GET /products/id  | 2.22–2.43   | 4                    | 4                    |
| HttpUser         | POST /products    | 3           | 3                    | 3                    |
| FastHttpUser     | GET /products     | 1.25        | 2                    | 2                    |
| FastHttpUser     | GET /products/id  | 1.26–1.29   | 2–3                  | 2–3                  |
| FastHttpUser     | POST /products    | 1.28        | 2                    | 2                    |

**Observation:**  
Even with 1 user, `FastHttpUser` has lower latency than `HttpUser` 
---

## 2. 50 Users Performance

| Scenario/User    | Request Type       | Median (ms) | 95th Percentile (ms) | 99th Percentile (ms) |
|------------------|-------------------|-------------|----------------------|----------------------|
| FastHttpUser         | GET /products     | 1.01        | 2                    | 6                    |
|  FastHttpUser        | POST /products    | 1           | 2                    | 6                    |
| FastHttpUser         | GET /products/id  | 1.07–1.09   | 2                    | 5                    |
| HttpUser     | GET /products     | 2           | 4                    | 10                   |
| HttpUser     | POST /products    | 2           | 4                    | 8                    |
| HttpUser     | GET /products/id  | 2           | 3–4                  | 7–8                  |

**Observation:**
Even with 50 user, `FastHttpUser` has lower latency than `HttpUser`

---

---

## Key Takeaways

1. **FastHttpUser** is faster and more efficient than **HttpUser**, especially under load.
2. HttpUser is simpler and mimics standard Python HTTP requests, which may be more realistic for some use cases.

---

