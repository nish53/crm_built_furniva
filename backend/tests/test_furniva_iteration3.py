"""
Furniva Iteration 3 Tests - Testing new features:
1. Master SKU form (simplified - no FNSKU, dims, weight, costs)
2. Procurement batch with box details (num_boxes, box_weights, box_dimensions, total_weight)
3. Returns workflow with mandatory fields and undo
4. Navigation order verification
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

class TestMasterSKU:
    """Master SKU tests - verifying simplified form"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_master_sku_simplified(self, auth_headers):
        """Test creating Master SKU with simplified fields (no FNSKU, dims, weight, costs)"""
        sku_data = {
            "master_sku": f"TEST-SIMPLE-{datetime.now().strftime('%H%M%S')}",
            "product_name": "Test Simple Product",
            "description": "Test description",
            "category": "Furniture",
            "amazon_sku": "AMZ-SIMPLE",
            "amazon_asin": "B0TESTSIMPLE",
            "flipkart_sku": "FK-SIMPLE",
            "flipkart_fsn": "FK-FSN-SIMPLE",
            "website_sku": "WEB-SIMPLE"
        }
        
        response = requests.post(f"{BASE_URL}/api/master-sku/", json=sku_data, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify response has expected fields
        assert data["master_sku"] == sku_data["master_sku"]
        assert data["product_name"] == sku_data["product_name"]
        assert data["amazon_sku"] == sku_data["amazon_sku"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/master-sku/{sku_data['master_sku']}", headers=auth_headers)

class TestProcurementBatch:
    """Procurement batch tests - verifying box details"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_batch_with_box_details(self, auth_headers):
        """Test creating procurement batch with num_boxes, box_weights, box_dimensions"""
        batch_data = {
            "master_sku": "TEST-001",
            "batch_number": f"TEST-BATCH-{datetime.now().strftime('%H%M%S')}",
            "procurement_date": datetime.now().isoformat(),
            "quantity": 10,
            "unit_cost": 1500,
            "num_boxes": 3,
            "box_weights": [15.5, 12.3, 8.2],
            "box_dimensions": [
                {"length": 100, "width": 50, "height": 40},
                {"length": 90, "width": 45, "height": 35},
                {"length": 80, "width": 40, "height": 30}
            ],
            "supplier": "Test Supplier"
        }
        
        response = requests.post(f"{BASE_URL}/api/procurement-batches/", json=batch_data, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify box fields
        assert data["num_boxes"] == 3, "num_boxes should be 3"
        assert data["box_weights"] == [15.5, 12.3, 8.2], "box_weights should match"
        assert data["total_weight"] == 36.0, f"total_weight should be 36.0 (sum of box_weights), got {data['total_weight']}"
        assert len(data["box_dimensions"]) == 3, "Should have 3 box dimensions"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/procurement-batches/{data['id']}", headers=auth_headers)
    
    def test_total_weight_auto_calculation(self, auth_headers):
        """Test that total_weight is auto-calculated from box_weights"""
        batch_data = {
            "master_sku": "TEST-001",
            "batch_number": f"TEST-CALC-{datetime.now().strftime('%H%M%S')}",
            "procurement_date": datetime.now().isoformat(),
            "quantity": 5,
            "unit_cost": 1000,
            "num_boxes": 2,
            "box_weights": [25.5, 30.0],
            "box_dimensions": [
                {"length": 100, "width": 50, "height": 40},
                {"length": 100, "width": 50, "height": 40}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/procurement-batches/", json=batch_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_weight = 25.5 + 30.0  # 55.5
        assert data["total_weight"] == expected_weight, f"Expected total_weight={expected_weight}, got {data['total_weight']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/procurement-batches/{data['id']}", headers=auth_headers)

class TestReturnsWorkflow:
    """Returns workflow tests - mandatory fields and undo"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_pickup_scheduled_requires_date(self, auth_headers):
        """Test that pickup_scheduled status requires pickup_date"""
        # Get first return in requested status
        response = requests.get(f"{BASE_URL}/api/returns/?status=requested", headers=auth_headers)
        returns = response.json()
        
        if len(returns) == 0:
            pytest.skip("No returns in requested status to test")
        
        return_id = returns[0]["id"]
        
        # Try to change to pickup_scheduled WITHOUT pickup_date
        response = requests.patch(
            f"{BASE_URL}/api/returns/{return_id}/status?status=pickup_scheduled",
            headers=auth_headers
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "pickup date" in response.json()["detail"].lower() or "mandatory" in response.json()["detail"].lower()
    
    def test_in_transit_requires_tracking(self, auth_headers):
        """Test that in_transit status requires tracking_number"""
        # Get first return in pickup_scheduled or approved status
        response = requests.get(f"{BASE_URL}/api/returns/?status=pickup_scheduled", headers=auth_headers)
        returns = response.json()
        
        if len(returns) == 0:
            # Try approved status
            response = requests.get(f"{BASE_URL}/api/returns/?status=approved", headers=auth_headers)
            returns = response.json()
            
            if len(returns) == 0:
                pytest.skip("No returns in suitable status to test")
            
            # First move to pickup_scheduled
            return_id = returns[0]["id"]
            response = requests.patch(
                f"{BASE_URL}/api/returns/{return_id}/status?status=pickup_scheduled&pickup_date=2026-03-15",
                headers=auth_headers
            )
            if response.status_code != 200:
                pytest.skip("Cannot transition return to pickup_scheduled")
        else:
            return_id = returns[0]["id"]
        
        # Try to change to in_transit WITHOUT tracking_number
        response = requests.patch(
            f"{BASE_URL}/api/returns/{return_id}/status?status=in_transit",
            headers=auth_headers
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "tracking" in response.json()["detail"].lower() or "mandatory" in response.json()["detail"].lower()
    
    def test_status_history_tracking(self, auth_headers):
        """Test that status changes are tracked in status_history"""
        # Get a return with status history
        response = requests.get(f"{BASE_URL}/api/returns/", headers=auth_headers)
        returns = response.json()
        
        if len(returns) == 0:
            pytest.skip("No returns to test")
        
        # Find return with status_history
        return_with_history = None
        for ret in returns:
            if ret.get("status_history") and len(ret["status_history"]) > 0:
                return_with_history = ret
                break
        
        if not return_with_history:
            pytest.skip("No returns with status history")
        
        # Verify history structure
        for history_entry in return_with_history["status_history"]:
            assert "from_status" in history_entry
            assert "to_status" in history_entry
            assert "changed_at" in history_entry
    
    def test_undo_endpoint_exists(self, auth_headers):
        """Test that undo endpoint exists and validates"""
        response = requests.get(f"{BASE_URL}/api/returns/", headers=auth_headers)
        returns = response.json()
        
        if len(returns) == 0:
            pytest.skip("No returns to test")
        
        # Get first return
        return_id = returns[0]["id"]
        
        # Try undo - may fail if no previous_status, but endpoint should exist
        response = requests.patch(f"{BASE_URL}/api/returns/{return_id}/undo", headers=auth_headers)
        
        # Should return either 200 (success) or 400 (no previous status)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

class TestOrderDetail:
    """Order detail tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@furniva.com",
            "password": "Test123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_order_has_communication_fields(self, auth_headers):
        """Test that order has communication checklist fields"""
        response = requests.get(f"{BASE_URL}/api/orders/", headers=auth_headers, params={"limit": 1})
        orders = response.json()
        
        if len(orders) == 0:
            pytest.skip("No orders to test")
        
        order = orders[0]
        
        # Verify communication fields exist
        comm_fields = ['dc1_called', 'cp_sent', 'dnp1_conf', 'dnp2_conf', 'dnp3_conf', 
                       'dp_conf', 'deliver_conf', 'install_conf', 'review_conf']
        
        for field in comm_fields:
            assert field in order, f"Order should have {field} field"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
