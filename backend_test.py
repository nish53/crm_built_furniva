#!/usr/bin/env python3
"""
Furniva CRM Backend API Test Suite - NEW FEATURES
Testing the newly implemented features:
1. Priority Dashboard Endpoints
2. Fake Shipping functionality
3. Historical Orders Import
4. Task Enhancement (photo upload, order linkage)
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import io
import csv

BASE_URL = "https://crm-bug-tracker-2.preview.emergentagent.com/api"

class FurnivaAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user = {
            "email": "furniva.test.user@example.com",
            "password": "TestPass123!",
            "name": "Furniva Test User",
            "role": "admin"
        }
        self.created_orders = []
        self.created_tasks = []
    
    def register_and_login(self):
        """Register test user and login"""
        print("🔐 Testing User Authentication...")
        
        # Try to register (may fail if user exists, which is fine)
        register_data = self.test_user.copy()
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print("✅ User registration successful")
            else:
                print("ℹ️ User registration skipped (user may already exist)")
        except Exception as e:
            print(f"ℹ️ Registration attempt: {e}")
        
        # Login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def create_test_data(self):
        """Create test orders and tasks for testing new features"""
        print("\n📦 Creating Test Data for New Features...")
        
        # Create orders for today dispatch (for priority dashboard)
        today = datetime.now(timezone.utc).date().isoformat()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        
        test_orders = [
            {
                "order_number": f"TEST-DISPATCH-{uuid.uuid4().hex[:8]}",
                "customer_id": str(uuid.uuid4()),
                "customer_name": "John Smith",
                "phone": "9876543210",
                "city": "Mumbai",
                "state": "Maharashtra", 
                "pincode": "400001",
                "sku": "SOFA-001",
                "product_name": "Modern Sofa Set",
                "quantity": 1,
                "price": 25000.0,
                "channel": "website",
                "status": "confirmed",
                "order_date": today + "T10:00:00Z",
                "dispatch_by": today + "T18:00:00Z",  # Needs dispatch today
                "delivery_by": tomorrow + "T18:00:00Z"
            },
            {
                "order_number": f"TEST-DELAYED-{uuid.uuid4().hex[:8]}",
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Jane Doe",
                "phone": "8765432109",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001", 
                "sku": "TABLE-001",
                "product_name": "Dining Table",
                "quantity": 1,
                "price": 15000.0,
                "channel": "amazon",
                "status": "dispatched",
                "order_date": yesterday + "T10:00:00Z",
                "dispatch_by": yesterday + "T18:00:00Z",
                "delivery_by": yesterday + "T18:00:00Z"  # Delayed order (past delivery date)
            },
            {
                "order_number": f"TEST-UNMAPPED-{uuid.uuid4().hex[:8]}",
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Bob Wilson",
                "phone": "7654321098",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "sku": "UNMAPPED-SKU-123",  # This should be unmapped
                "product_name": "Unmapped Product",
                "quantity": 1,
                "price": 10000.0,
                "channel": "flipkart",
                "status": "pending",
                "order_date": today + "T10:00:00Z"
            }
        ]
        
        # Create the orders
        for order_data in test_orders:
            try:
                response = self.session.post(f"{BASE_URL}/orders/", json=order_data)
                if response.status_code in [200, 201]:
                    order = response.json()
                    self.created_orders.append(order["id"])
                    print(f"✅ Created test order: {order_data['order_number']}")
                else:
                    print(f"❌ Failed to create order: {response.status_code}")
            except Exception as e:
                print(f"❌ Error creating order: {e}")
        
        # Create test task with order_details for task enhancement testing
        task_data = {
            "title": "Quality Check Installation",
            "description": "Check furniture quality after installation",
            "priority": "high",
            "status": "in_progress",
            "order_details": f"Order: {test_orders[0]['order_number']}",
            "order_id": self.created_orders[0] if self.created_orders else None
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/tasks/", json=task_data)
            if response.status_code in [200, 201]:
                task = response.json()
                self.created_tasks.append(task["id"])
                print(f"✅ Created test task: {task['title']}")
            else:
                print(f"❌ Failed to create task: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating task: {e}")
    
    def test_priority_dashboard_endpoints(self):
        """Test the three new priority dashboard endpoints"""
        print("\n🎯 Testing Priority Dashboard Endpoints...")
        
        endpoints = [
            ("/dashboard/priority/dispatch-pending-today", "Dispatch Pending Today"),
            ("/dashboard/priority/delayed-orders", "Delayed Orders"),  
            ("/dashboard/priority/unmapped-skus", "Unmapped SKUs")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("count", 0)
                    message = data.get("message", "No message")
                    print(f"✅ {name}: {count} items - {message}")
                    
                    # Validate response structure
                    if "count" in data and isinstance(data["count"], int):
                        if endpoint.endswith("unmapped-skus"):
                            if "unmapped_skus" in data:
                                print(f"   📊 Found {len(data['unmapped_skus'])} unmapped SKUs")
                        else:
                            if "orders" in data:
                                print(f"   📦 Retrieved {len(data['orders'])} orders")
                    else:
                        print(f"⚠️ Response missing expected 'count' field")
                else:
                    print(f"❌ {name} failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error testing {name}: {e}")
    
    def test_fake_shipping(self):
        """Test fake shipping functionality"""
        print("\n🚚 Testing Fake Shipping Functionality...")
        
        if not self.created_orders:
            print("❌ No test orders available for fake shipping test")
            return
        
        order_id = self.created_orders[0]  # Use first created order
        tracking_id = f"FAKE-{uuid.uuid4().hex[:8]}"
        
        try:
            # Test fake ship endpoint
            response = self.session.post(
                f"{BASE_URL}/dashboard/orders/{order_id}/fake-ship",
                params={"tracking_id": tracking_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Fake shipping successful: {result.get('message')}")
                
                # Verify the order was updated correctly
                order_response = self.session.get(f"{BASE_URL}/orders/{order_id}")
                if order_response.status_code == 200:
                    order = order_response.json()
                    if order.get("fake_shipped") == True:
                        print("✅ Order correctly marked with fake_shipped: true")
                        if order.get("tracking_number") == tracking_id:
                            print(f"✅ Tracking ID correctly set: {tracking_id}")
                        else:
                            print(f"⚠️ Tracking ID mismatch: expected {tracking_id}, got {order.get('tracking_number')}")
                    else:
                        print("❌ Order not marked as fake_shipped")
                else:
                    print("❌ Could not verify order update")
            else:
                print(f"❌ Fake shipping failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error testing fake shipping: {e}")
    
    def test_historical_orders_import(self):
        """Test historical orders import functionality"""
        print("\n📊 Testing Historical Orders Import...")
        
        # Create test CSV content with historical order data
        csv_data = [
            ["Order ID", "Order Date", "Dispatch By", "Delivery By", "Actual Dispatch Date", 
             "Order Conf Calling", "Assembly Type", "Dispatch Confirmation Sent",
             "Did Not Pick Day 1", "Confirmed on Day 1?", "Did Not Pick Day 2", "Confirmed on Day 2?",
             "Did Not Pick Day 3", "Confirmed on Day 3?", "Deliver Conf", "Review Conf",
             "Delivery Date", "Customer Name", "Billing No.", "Shipping No.", "Place", "State",
             "Pincode", "SKU", "Qty", "Tracking", "Actual Shipping Company", "Instructions",
             "Live Status", "Price", "Pickup Status", "Reason for Cancellation/Replacement"],
            [f"HIST-{uuid.uuid4().hex[:8]}", "2024-01-15", "2024-01-18", "2024-01-25", "2024-01-18",
             "Yes", "Full Assembly", "Yes", "No", "Yes", "No", "Yes", "No", "Yes", "Yes", "Yes",
             "2024-01-24", "Historical Customer 1", "9999888877", "9999888877", "Chennai", "Tamil Nadu",
             "600001", "HIST-SOFA-001", "1", "TRACK123", "BlueDart", "Handle with care",
             "delivered", "20000", "Completed", ""],
            [f"HIST-{uuid.uuid4().hex[:8]}", "2024-02-10", "2024-02-13", "2024-02-20", "2024-02-13",
             "Yes", "DIY", "Yes", "No", "Yes", "No", "Yes", "No", "Yes", "Yes", "Yes",
             "2024-02-19", "Historical Customer 2", "8888777766", "8888777766", "Pune", "Maharashtra",
             "411001", "HIST-TABLE-001", "1", "TRACK456", "Delhivery", "Fragile item",
             "delivered", "15000", "Completed", ""]
        ]
        
        # Create CSV file content
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(csv_data)
        csv_content = csv_buffer.getvalue()
        
        try:
            # Prepare file for upload
            files = {
                'file': ('historical_orders.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
            }
            
            response = self.session.post(f"{BASE_URL}/orders/import-historical", files=files)
            
            if response.status_code == 200:
                result = response.json()
                imported = result.get("imported", 0)
                skipped = result.get("skipped", 0)
                errors = result.get("errors", 0)
                
                print(f"✅ Historical import successful:")
                print(f"   📦 Imported: {imported} orders")
                print(f"   ⏭️ Skipped: {skipped} orders")
                print(f"   ❌ Errors: {errors} orders")
                
                if imported > 0:
                    # Verify orders were marked as historical
                    orders_response = self.session.get(f"{BASE_URL}/orders/?limit=10")
                    if orders_response.status_code == 200:
                        orders = orders_response.json()
                        historical_orders = [o for o in orders if o.get("is_historical") == True]
                        if historical_orders:
                            print(f"✅ Found {len(historical_orders)} historical orders in database")
                            print(f"   📋 Example: {historical_orders[0].get('order_number')} - {historical_orders[0].get('channel')}")
                        else:
                            print("⚠️ No historical orders found in recent orders")
            else:
                print(f"❌ Historical import failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error testing historical import: {e}")
    
    def test_task_enhancements(self):
        """Test task photo upload and order linkage features"""
        print("\n📋 Testing Task Enhancement Features...")
        
        if not self.created_tasks:
            print("❌ No test tasks available for enhancement testing")
            return
        
        task_id = self.created_tasks[0]
        
        # Test photo upload
        photo_url = f"https://example.com/task-photo-{uuid.uuid4().hex[:8]}.jpg"
        try:
            response = self.session.post(
                f"{BASE_URL}/tasks/{task_id}/upload-photo",
                params={"photo_url": photo_url}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Photo upload successful: {result.get('message')}")
                print(f"   📸 Photo URL: {photo_url}")
            else:
                print(f"❌ Photo upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error testing photo upload: {e}")
        
        # Test task with order linkage
        try:
            response = self.session.get(f"{BASE_URL}/tasks/{task_id}/with-order")
            
            if response.status_code == 200:
                task_with_order = response.json()
                print(f"✅ Task with order retrieval successful")
                
                # Check if order details are included
                if "order" in task_with_order and task_with_order["order"]:
                    order = task_with_order["order"]
                    print(f"   🔗 Linked order: {order.get('order_number')} - {order.get('customer_name')}")
                else:
                    print("   ℹ️ No linked order found (may be expected)")
                
                # Check if photos array exists and contains our uploaded photo
                if "photos" in task_with_order:
                    photos = task_with_order["photos"]
                    if photos and photo_url in photos:
                        print(f"✅ Photos array contains uploaded photo")
                    else:
                        print(f"⚠️ Photo not found in photos array: {photos}")
                
                # Check if order_details field exists
                if "order_details" in task_with_order:
                    order_details = task_with_order["order_details"]
                    print(f"✅ Order details field present: {order_details}")
                else:
                    print("⚠️ Order details field missing")
                    
            else:
                print(f"❌ Task with order retrieval failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error testing task with order: {e}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created orders
        for order_id in self.created_orders:
            try:
                response = self.session.delete(f"{BASE_URL}/orders/{order_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted test order: {order_id}")
                else:
                    print(f"⚠️ Could not delete order {order_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting order {order_id}: {e}")
        
        # Delete created tasks
        for task_id in self.created_tasks:
            try:
                response = self.session.delete(f"{BASE_URL}/tasks/{task_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted test task: {task_id}")
                else:
                    print(f"⚠️ Could not delete task {task_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting task {task_id}: {e}")
    
    def run_all_tests(self):
        """Run all new feature tests"""
        print("🚀 Starting Furniva CRM NEW FEATURES Backend Testing")
        print("=" * 60)
        
        if not self.register_and_login():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Create test data
        self.create_test_data()
        
        # Run all new feature tests
        self.test_priority_dashboard_endpoints()
        self.test_fake_shipping()
        self.test_historical_orders_import()
        self.test_task_enhancements()
        
        # Cleanup
        self.cleanup_test_data()
        
        print("\n" + "=" * 60)
        print("🏁 New Features Testing Complete!")
        return True

if __name__ == "__main__":
    tester = FurnivaAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)