import sys
import json
import pytest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app import create_app
except ImportError:
    from backend.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health check returns operational status"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["service"] == "Srinivasa Textiles REST Engine"
    assert "databaseStatus" in data

def test_get_products(client):
    """Test catalog retrieval returns list of products"""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert isinstance(data["products"], list)

def test_product_filter_by_department(client):
    """Test department filtering returns only Women items"""
    response = client.get("/api/products?department=Women")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    for p in data["products"]:
        assert p["department"].lower() == "women"

def test_coupon_validation(client):
    """Test coupon validation gives correct percentage and amount"""
    payload = {"code": "HERITAGE10", "subtotal": 5000}
    response = client.post("/api/coupons/validate", json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["coupon"]["code"] == "HERITAGE10"
    assert data["coupon"]["discountPercent"] == 10.0
    assert data["coupon"]["discountAmount"] == 500.0

def test_create_order(client):
    """Test full order placement lifecycle"""
    payload = {
        "items": [
            {
                "id": "ST-KAN-001",
                "name": "Kanchipuram Pure Zari Crimson Bridal Silk Saree",
                "price": 28500,
                "quantity": 1,
                "color": "Crimson Red"
            }
        ],
        "customer": {
            "name": "Ananya Krishnan",
            "email": "ananya@example.com",
            "phone": "+91 98401 99887",
            "address": "12 Gandhi Road",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600004"
        },
        "subtotal": 28500,
        "discount": 0,
        "shippingFee": 0,
        "paymentMethod": "UPI"
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["success"] is True
    assert "trackingNumber" in data["order"]
    assert data["order"]["paymentStatus"] == "Paid"

def test_get_reviews(client):
    """Test reviews retrieval endpoint"""
    response = client.get("/api/reviews")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert isinstance(data["reviews"], list)
    assert len(data["reviews"]) > 0

def test_add_subscriber(client):
    """Test newsletter subscription endpoint"""
    response = client.post("/api/subscribers", json={"email": "tester@srinivasatextiles.com", "phone": "9876543210"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True

def test_security_headers(client):
    """Test that HTTP security headers are present on API responses"""
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"

def test_orders_endpoint_requires_auth(client):
    """Test that unauthenticated requests to orders endpoint are blocked"""
    response = client.get("/api/orders")
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data["success"] is False

def test_admin_login_and_protected_access(client):
    """Test legitimate admin login and authenticated access to orders"""
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "1978"})
    assert login_res.status_code == 200
    login_data = json.loads(login_res.data)
    assert login_data["success"] is True
    assert "token" in login_data

    token = login_data["token"]
    orders_res = client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
    assert orders_res.status_code == 200
    orders_data = json.loads(orders_res.data)
    assert orders_data["success"] is True
    assert "orders" in orders_data

def test_backdoor_password_rejected(client):
    """Test that default weak backdoor passwords (admin123) are rejected"""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 401
    data = json.loads(res.data)
    assert data["success"] is False

def test_unauthorized_coupon_creation_blocked(client):
    """Test that creating coupons without admin auth is blocked with 401"""
    res = client.post("/api/coupons", json={"code": "HACK99", "discount_percent": 99.0})
    assert res.status_code == 401
    data = json.loads(res.data)
    assert data["success"] is False

def test_unauthorized_webhook_blocked(client):
    """Test that payment webhook without valid secret is rejected"""
    res = client.post("/api/orders/webhook/payment", json={"order_id": "ST-ORD-TEST", "status": "paid"})
    assert res.status_code == 401
    data = json.loads(res.data)
    assert data["success"] is False
