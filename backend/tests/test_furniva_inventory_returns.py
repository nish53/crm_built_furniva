"""
Furniva Platform API Tests - Inventory, Returns, Costing, Order Detail
Tests: Master SKU CRUD, Platform Listings, Procurement Batches, Returns CRUD, Financials
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - updated for Furniva
TEST_USER_EMAIL = "test@furniva.com"
TEST_USER_PASSWORD = "Test123!"
TEST_PREFIX = "TEST_"


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
        print(f"PASS: Login successful for user: {data['user']['name']}")


class TestMasterSKU:
    """Master SKU CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_master_skus(self):
        """Test getting all Master SKUs"""
        response = requests.get(
            f"{BASE_URL}/api/master-sku/",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Retrieved {len(data)} Master SKUs")
    
    def test_get_existing_master_sku(self):
        """Test getting the existing TEST-001 Master SKU"""
        response = requests.get(
            f"{BASE_URL}/api/master-sku/TEST-001",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["master_sku"] == "TEST-001"
        assert data["product_name"] == "Test Wooden Chair"
        print(f"PASS: Retrieved Master SKU: {data['master_sku']}")
    
    def test_create_and_delete_master_sku(self):
        """Test creating a new Master SKU and then deleting it"""
        sku_id = f"{TEST_PREFIX}SKU-{datetime.now().strftime('%H%M%S')}"
        sku_data = {
            "master_sku": sku_id,
            "product_name": f"{TEST_PREFIX}Wooden Dining Table",
            "category": "Furniture",
            "amazon_sku": f"AMZ-{sku_id}",
            "amazon_asin": "B0TESTCREATE"
        }
        
        # Create
        create_resp = requests.post(
            f"{BASE_URL}/api/master-sku/",
            headers=self.headers,
            json=sku_data
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        created = create_resp.json()
        assert created["master_sku"] == sku_id
        print(f"PASS: Created Master SKU: {sku_id}")
        
        # Update
        update_data = {**sku_data, "product_name": f"{TEST_PREFIX}Updated Dining Table"}
        update_resp = requests.put(
            f"{BASE_URL}/api/master-sku/{sku_id}",
            headers=self.headers,
            json=update_data
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert "Updated" in updated["product_name"]
        print(f"PASS: Updated Master SKU: {sku_id}")
        
        # Delete
        delete_resp = requests.delete(
            f"{BASE_URL}/api/master-sku/{sku_id}",
            headers=self.headers
        )
        assert delete_resp.status_code == 200
        
        # Verify deleted
        get_resp = requests.get(
            f"{BASE_URL}/api/master-sku/{sku_id}",
            headers=self.headers
        )
        assert get_resp.status_code == 404
        print(f"PASS: Deleted Master SKU: {sku_id}")


class TestPlatformListings:
    """Platform Listings CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_listings_by_master_sku(self):
        """Test getting listings for TEST-001"""
        response = requests.get(
            f"{BASE_URL}/api/platform-listings/by-master-sku/TEST-001",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have at least 1 listing per test context
        print(f"PASS: Retrieved {len(data)} listings for TEST-001")
    
    def test_create_and_delete_listing(self):
        """Test creating and deleting a platform listing"""
        listing_data = {
            "master_sku": "TEST-001",
            "platform": "flipkart",
            "platform_sku": f"FK-{TEST_PREFIX}{datetime.now().strftime('%H%M%S')}",
            "platform_product_id": "FSN12345TEST",
            "is_active": True
        }
        
        # Create
        create_resp = requests.post(
            f"{BASE_URL}/api/platform-listings/",
            headers=self.headers,
            json=listing_data
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        created = create_resp.json()
        listing_id = created["id"]
        assert created["platform"] == "flipkart"
        print(f"PASS: Created platform listing: {listing_id}")
        
        # Delete
        delete_resp = requests.delete(
            f"{BASE_URL}/api/platform-listings/{listing_id}",
            headers=self.headers
        )
        assert delete_resp.status_code == 200
        print(f"PASS: Deleted platform listing: {listing_id}")


class TestProcurementBatches:
    """Procurement Batches CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_batches_by_master_sku(self):
        """Test getting procurement batches for TEST-001"""
        response = requests.get(
            f"{BASE_URL}/api/procurement-batches/by-master-sku/TEST-001",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have at least 1 batch
        print(f"PASS: Retrieved {len(data)} procurement batches for TEST-001")
    
    def test_get_average_cost(self):
        """Test average cost calculation"""
        response = requests.get(
            f"{BASE_URL}/api/procurement-batches/average-cost/TEST-001?method=weighted",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "average_cost" in data
        assert "method" in data
        assert data["method"] == "weighted_average"
        print(f"PASS: Average cost for TEST-001: {data['average_cost']}")
    
    def test_create_and_delete_batch(self):
        """Test creating and deleting a procurement batch"""
        batch_data = {
            "master_sku": "TEST-001",
            "batch_number": f"{TEST_PREFIX}BATCH-{datetime.now().strftime('%H%M%S')}",
            "procurement_date": datetime.now().isoformat(),
            "quantity": 25,
            "unit_cost": 2000.0,
            "supplier": f"{TEST_PREFIX}Supplier"
        }
        
        # Create
        create_resp = requests.post(
            f"{BASE_URL}/api/procurement-batches/",
            headers=self.headers,
            json=batch_data
        )
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        created = create_resp.json()
        batch_id = created["id"]
        assert created["quantity"] == 25
        assert created["total_cost"] == 50000.0  # 25 * 2000
        print(f"PASS: Created procurement batch: {batch_id}")
        
        # Delete
        delete_resp = requests.delete(
            f"{BASE_URL}/api/procurement-batches/{batch_id}",
            headers=self.headers
        )
        assert delete_resp.status_code == 200
        print(f"PASS: Deleted procurement batch: {batch_id}")


class TestReturns:
    """Returns CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_returns(self):
        """Test getting all returns"""
        response = requests.get(
            f"{BASE_URL}/api/returns/",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Retrieved {len(data)} returns")
    
    def test_get_returns_filter_by_status(self):
        """Test filtering returns by status"""
        response = requests.get(
            f"{BASE_URL}/api/returns/?status=requested",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # All returned should have 'requested' status
        for ret in data:
            assert ret["return_status"] == "requested"
        print(f"PASS: Filtered returns by status, got {len(data)} requested returns")


class TestFinancials:
    """Financial calculation and analysis tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profit_analysis(self):
        """Test profit analysis endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/financials/profit-analysis",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should have aggregated data
        assert "total_revenue" in data or data == {}
        print(f"PASS: Profit analysis retrieved: {data}")
    
    def test_leakage_report(self):
        """Test leakage report endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/financials/leakage-report",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Leakage report has {len(data)} items")


class TestOrders:
    """Orders API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_orders(self):
        """Test getting all orders (after sku fix)"""
        response = requests.get(
            f"{BASE_URL}/api/orders/",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Retrieved {len(data)} orders")
    
    def test_get_order_by_id(self):
        """Test getting a specific order"""
        # First get an order from the list
        list_resp = requests.get(
            f"{BASE_URL}/api/orders/?limit=1",
            headers=self.headers
        )
        assert list_resp.status_code == 200
        orders = list_resp.json()
        
        if len(orders) > 0:
            order_id = orders[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/orders/{order_id}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == order_id
            print(f"PASS: Retrieved order: {data.get('order_number')}")
        else:
            print("SKIP: No orders to test with")


class TestOrderFinancials:
    """Order-level financial calculation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create test order for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_calculate_financials(self):
        """Test calculating financials for an order"""
        # First create an order
        order_date = datetime.now().isoformat()
        dispatch_by = (datetime.now() + timedelta(days=3)).isoformat()
        
        order_data = {
            "channel": "amazon",
            "order_number": f"{TEST_PREFIX}FIN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": order_date,
            "dispatch_by": dispatch_by,
            "customer_id": "test-customer-fin",
            "customer_name": f"{TEST_PREFIX}Fin Customer",
            "phone": "9876543210",
            "pincode": "400001",
            "sku": "TEST-SKU-FIN",
            "product_name": f"{TEST_PREFIX}Test Product",
            "quantity": 1,
            "price": 10000.00
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/orders/",
            headers=self.headers,
            json=order_data
        )
        assert create_resp.status_code == 200, f"Order create failed: {create_resp.text}"
        order_id = create_resp.json()["id"]
        
        # Calculate financials
        params = "product_cost=5000&shipping_cost=500&packaging_cost=100&installation_cost=200&marketplace_commission_rate=15"
        fin_resp = requests.post(
            f"{BASE_URL}/api/financials/calculate/{order_id}?{params}",
            headers=self.headers
        )
        assert fin_resp.status_code == 200, f"Financials failed: {fin_resp.text}"
        financials = fin_resp.json()
        
        # Validate calculations
        assert financials["selling_price"] == 10000.0
        assert financials["marketplace_commission"] == 1500.0  # 15%
        assert financials["total_cost"] == 5800.0  # 5000 + 500 + 100 + 200
        assert "gross_profit" in financials
        print(f"PASS: Calculated financials - Profit: {financials['gross_profit']}, Margin: {financials['profit_margin']}%")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=self.headers)


class TestReturnCreation:
    """Return creation from order tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_return_for_order(self):
        """Test creating a return request for an order"""
        # First create an order
        order_date = datetime.now().isoformat()
        
        order_data = {
            "channel": "amazon",
            "order_number": f"{TEST_PREFIX}RET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": order_date,
            "customer_id": "test-customer-ret",
            "customer_name": f"{TEST_PREFIX}Return Customer",
            "phone": "9876543211",
            "pincode": "400002",
            "sku": "TEST-SKU-RET",
            "product_name": f"{TEST_PREFIX}Return Test Product",
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
        
        # Create return
        return_data = {
            "order_id": order_id,
            "return_reason": "defective",
            "return_reason_details": "Product has scratches",
            "damage_category": "scratch",
            "is_installation_related": False
        }
        
        return_resp = requests.post(
            f"{BASE_URL}/api/returns/",
            headers=self.headers,
            json=return_data
        )
        assert return_resp.status_code == 200, f"Return create failed: {return_resp.text}"
        return_req = return_resp.json()
        return_id = return_req["id"]
        
        assert return_req["return_reason"] == "defective"
        assert return_req["return_status"] == "requested"
        print(f"PASS: Created return request: {return_id}")
        
        # Update status
        update_resp = requests.patch(
            f"{BASE_URL}/api/returns/{return_id}/status?status=approved",
            headers=self.headers
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["return_status"] == "approved"
        print(f"PASS: Updated return status to: approved")
        
        # Cleanup - delete order (return will remain for testing)
        # Note: Return records are kept for history
        requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=self.headers)


class TestChannels:
    """Channels API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_channels(self):
        """Test getting all channels"""
        response = requests.get(
            f"{BASE_URL}/api/channels/",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Retrieved {len(data)} channels")


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
            print(f"PASS: Cleaned up {deleted_count} test orders")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
