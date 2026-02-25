"""
FURNI e-commerce platform API tests
Tests: Auth, Orders CRUD, Dashboard, CSV Import
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test@furni.com"
TEST_USER_PASSWORD = "test123"
TEST_PREFIX = "TEST_"

class TestHealth:
    """Health check tests - run first"""
    
    def test_api_root_accessible(self):
        """Test that API root is accessible"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API Root: {data}")


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"Login successful for user: {data['user']['name']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("Invalid credentials properly rejected")
    
    def test_register_existing_email(self):
        """Test registration with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": "test123",
            "name": "Test User",
            "role": "admin"
        })
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()
        print("Duplicate email registration properly rejected")
    
    def test_get_me_authenticated(self):
        """Test /me endpoint with valid token"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Get user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        print(f"User info retrieved: {data['name']}, role: {data['role']}")


class TestDashboard:
    """Dashboard endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate stats structure
        assert "total_orders" in data
        assert "pending_orders" in data
        assert "dispatched_today" in data
        assert "pending_tasks" in data
        assert "pending_calls" in data
        assert "low_stock_items" in data
        assert "pending_claims" in data
        assert "revenue_today" in data
        
        # Validate data types
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["revenue_today"], (int, float))
        print(f"Dashboard stats: {data}")
    
    def test_get_recent_orders(self):
        """Test recent orders endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/recent-orders",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should be a list
        assert isinstance(data, list)
        print(f"Recent orders count: {len(data)}")
        
        # Validate order structure if any orders exist
        if len(data) > 0:
            order = data[0]
            assert "order_number" in order
            assert "status" in order
            assert "customer_name" in order
            print(f"First recent order: {order['order_number']}")


class TestOrders:
    """Order CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_all_orders(self):
        """Test getting all orders"""
        response = requests.get(
            f"{BASE_URL}/api/orders/",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total orders: {len(data)}")
    
    def test_create_order_and_verify(self):
        """Test creating an order and verify it persists"""
        order_date = datetime.now().isoformat()
        dispatch_by = (datetime.now() + timedelta(days=3)).isoformat()
        
        order_data = {
            "channel": "whatsapp",
            "order_number": f"{TEST_PREFIX}ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": order_date,
            "dispatch_by": dispatch_by,
            "customer_id": "test-customer-123",
            "customer_name": f"{TEST_PREFIX}Customer",
            "phone": "9876543210",
            "pincode": "400001",
            "sku": "TEST-SKU-001",
            "product_name": f"{TEST_PREFIX}Test Sofa",
            "quantity": 1,
            "price": 15000.00
        }
        
        # Create order
        create_resp = requests.post(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            json=order_data
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        created = create_resp.json()
        
        # Validate response
        assert created["order_number"] == order_data["order_number"]
        assert created["customer_name"] == order_data["customer_name"]
        assert "id" in created
        order_id = created["id"]
        print(f"Created order: {order_id}")
        
        # GET to verify persistence
        get_resp = requests.get(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=self.headers
        )
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched["order_number"] == order_data["order_number"]
        print(f"Order persisted and fetched: {fetched['order_number']}")
        
        # Store for cleanup
        self.created_order_id = order_id
        return order_id
    
    def test_filter_orders_by_status(self):
        """Test filtering orders by status"""
        response = requests.get(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            params={"status": "pending"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned orders should have pending status
        for order in data:
            assert order["status"] == "pending"
        print(f"Filtered pending orders: {len(data)}")
    
    def test_filter_orders_by_channel(self):
        """Test filtering orders by channel"""
        response = requests.get(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            params={"channel": "amazon"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned orders should have amazon channel
        for order in data:
            assert order["channel"] == "amazon"
        print(f"Filtered Amazon orders: {len(data)}")
    
    def test_update_order_status(self):
        """Test updating order status"""
        # First create an order
        order_date = datetime.now().isoformat()
        dispatch_by = (datetime.now() + timedelta(days=3)).isoformat()
        
        order_data = {
            "channel": "phone",
            "order_number": f"{TEST_PREFIX}UPDATE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": order_date,
            "dispatch_by": dispatch_by,
            "customer_id": "test-customer-456",
            "customer_name": f"{TEST_PREFIX}Update Test",
            "phone": "9876543211",
            "pincode": "400002",
            "sku": "TEST-SKU-002",
            "product_name": f"{TEST_PREFIX}Test Chair",
            "quantity": 1,
            "price": 5000.00
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            json=order_data
        )
        assert create_resp.status_code == 200
        order_id = create_resp.json()["id"]
        
        # Update status
        update_resp = requests.patch(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=self.headers,
            json={"status": "confirmed"}
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["status"] == "confirmed"
        print(f"Order {order_id} status updated to: confirmed")
    
    def test_delete_order(self):
        """Test deleting an order"""
        # First create an order
        order_date = datetime.now().isoformat()
        dispatch_by = (datetime.now() + timedelta(days=3)).isoformat()
        
        order_data = {
            "channel": "website",
            "order_number": f"{TEST_PREFIX}DELETE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": order_date,
            "dispatch_by": dispatch_by,
            "customer_id": "test-customer-789",
            "customer_name": f"{TEST_PREFIX}Delete Test",
            "phone": "9876543212",
            "pincode": "400003",
            "sku": "TEST-SKU-003",
            "product_name": f"{TEST_PREFIX}Test Table",
            "quantity": 1,
            "price": 8000.00
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            json=order_data
        )
        assert create_resp.status_code == 200
        order_id = create_resp.json()["id"]
        
        # Delete order
        delete_resp = requests.delete(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=self.headers
        )
        assert delete_resp.status_code == 200
        
        # Verify deletion
        get_resp = requests.get(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=self.headers
        )
        assert get_resp.status_code == 404
        print(f"Order {order_id} successfully deleted")


class TestCSVImport:
    """CSV/TXT import tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_import_amazon_csv(self):
        """Test importing Amazon CSV file"""
        csv_content = """order-id,purchase-date,promise-date,buyer-name,buyer-phone-number,ship-address-1,ship-city,ship-state,ship-postal-code,sku,asin,product-name,quantity-purchased,item-price
AMZ-TEST-001,2025-01-15T10:00:00Z,2025-01-18T10:00:00Z,Test Buyer,9999888877,123 Test St,Mumbai,Maharashtra,400001,SKU-AMZ-001,B0TEST001,Test Product Amazon,1,12000"""
        
        files = {
            "file": ("amazon_orders.csv", csv_content, "text/csv")
        }
        
        # Remove Content-Type header for multipart
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/orders/import-csv?channel=amazon",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"Import failed: {response.text}"
        data = response.json()
        assert "imported" in data
        assert "skipped" in data
        print(f"Amazon CSV Import: {data}")
    
    def test_import_amazon_txt(self):
        """Test importing Amazon tab-separated TXT file"""
        txt_content = """order-id\tpurchase-date\tpromise-date\tbuyer-name\tbuyer-phone-number\tship-address-1\tship-city\tship-state\tship-postal-code\tsku\tasin\tproduct-name\tquantity-purchased\titem-price
AMZ-TEST-TXT-001\t2025-01-15T10:00:00Z\t2025-01-18T10:00:00Z\tTxt Test Buyer\t9999888866\t456 Test Ave\tDelhi\tDelhi\t110001\tSKU-AMZ-TXT\tB0TESTTXT\tTest Product TXT\t1\t15000"""
        
        files = {
            "file": ("amazon_orders.txt", txt_content, "text/plain")
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/orders/import-csv?channel=amazon",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 200, f"TXT Import failed: {response.text}"
        data = response.json()
        print(f"Amazon TXT Import: {data}")
    
    def test_import_invalid_file_type(self):
        """Test importing invalid file type fails"""
        files = {
            "file": ("orders.pdf", b"invalid content", "application/pdf")
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/orders/import-csv?channel=amazon",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 400
        print("Invalid file type properly rejected")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cleanup_test_orders(self):
        """Clean up TEST_ prefixed orders"""
        # Get all orders
        response = requests.get(
            f"{BASE_URL}/api/orders/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            orders = response.json()
            deleted_count = 0
            for order in orders:
                if order.get("customer_name", "").startswith(TEST_PREFIX) or \
                   order.get("order_number", "").startswith(TEST_PREFIX):
                    del_resp = requests.delete(
                        f"{BASE_URL}/api/orders/{order['id']}",
                        headers=self.headers
                    )
                    if del_resp.status_code == 200:
                        deleted_count += 1
            print(f"Cleaned up {deleted_count} test orders")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
