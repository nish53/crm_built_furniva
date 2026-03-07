#!/usr/bin/env python3
"""
Furniva CRM Backend Testing Suite
Test Priority: Critical Bug Fixes from 2025-03-07

Test Areas (in order of priority):
1. Order Pagination System (CRITICAL)
2. Multi-Item Orders Import (CRITICAL)  
3. Master SKU Sync Endpoints (HIGH)
4. Order Date Validation (MEDIUM)
"""

import asyncio
import httpx
import json
import csv
import io
import uuid
from datetime import datetime, timezone
import os

# Backend URL from environment
BACKEND_URL = "https://order-hub-175.preview.emergentagent.com/api"

class FurnivaBackendTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.user_id = None
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def register_and_login(self):
        """Register test user and login to get auth token"""
        print("🔐 Setting up test user authentication...")
        
        # Generate unique test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_furniva_{unique_id}@example.com"
        test_password = "TestPass123!"
        
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Test User Furniva",
            "role": "admin"
        }
        
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print(f"✅ User registered: {test_email}")
            else:
                print(f"⚠️ Register response: {response.status_code} - {response.text}")
                # Try to login with existing user
        except Exception as e:
            print(f"⚠️ Register error: {e}")
        
        # Login
        login_data = {"email": test_email, "password": test_password}
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                self.token = result["access_token"]
                self.user_id = result["user"]["id"]
                print(f"✅ Authentication successful - Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    # =====================================
    # TEST 1: ORDER PAGINATION SYSTEM (CRITICAL)
    # =====================================
    
    async def test_order_pagination_system(self):
        """Test the new paginated orders endpoint"""
        print("\n🔍 TEST 1: ORDER PAGINATION SYSTEM (CRITICAL)")
        print("=" * 60)
        
        try:
            # Test basic pagination structure
            print("1. Testing basic pagination response structure...")
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?skip=0&limit=10", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Basic pagination failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            
            # Verify pagination structure
            required_fields = ['items', 'total', 'page', 'page_size', 'total_pages']
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing pagination field: {field}")
                    return False
            
            print(f"✅ Pagination structure correct: {len(data['items'])} items, total: {data['total']}")
            print(f"   📄 Page: {data['page']}, Page Size: {data['page_size']}, Total Pages: {data['total_pages']}")
            
            # Test pagination with skip/limit
            print("2. Testing pagination with skip=0&limit=100...")
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?skip=0&limit=100", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Pagination test 1 failed: {response.status_code}")
                return False
            
            page1_data = response.json()
            print(f"✅ Page 1: {len(page1_data['items'])} items")
            
            # Test second page if there are enough items
            if page1_data['total'] > 100:
                print("3. Testing pagination with skip=100&limit=100...")
                response = await self.client.get(
                    f"{BACKEND_URL}/orders/?skip=100&limit=100", 
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    print(f"❌ Pagination test 2 failed: {response.status_code}")
                    return False
                
                page2_data = response.json()
                print(f"✅ Page 2: {len(page2_data['items'])} items")
                
                # Verify total count is consistent
                if page1_data['total'] != page2_data['total']:
                    print(f"❌ Total count inconsistent: page1={page1_data['total']}, page2={page2_data['total']}")
                    return False
                
                print(f"✅ Total count consistent: {page1_data['total']}")
            
            # Test filtering across ALL records
            print("4. Testing filters work across all records...")
            
            # Test status filter
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?status=delivered&skip=0&limit=100", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Status filter failed: {response.status_code}")
                return False
            
            filtered_data = response.json()
            print(f"✅ Status filter (delivered): {len(filtered_data['items'])} items, total: {filtered_data['total']}")
            
            # Test channel filter
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?channel=amazon&skip=0&limit=100", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Channel filter failed: {response.status_code}")
                return False
            
            channel_data = response.json()
            print(f"✅ Channel filter (amazon): {len(channel_data['items'])} items, total: {channel_data['total']}")
            
            # Verify pagination metadata calculation
            total = data['total']
            page_size = data['page_size']
            expected_total_pages = (total + page_size - 1) // page_size  # Ceiling division
            
            if data['total_pages'] != expected_total_pages:
                print(f"❌ Total pages calculation wrong: got {data['total_pages']}, expected {expected_total_pages}")
                return False
            
            print(f"✅ Total pages calculation correct: {data['total_pages']}")
            
            print("\n🎉 ORDER PAGINATION SYSTEM: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Order pagination test error: {e}")
            return False
    
    # =====================================
    # TEST 2: MULTI-ITEM ORDERS IMPORT (CRITICAL)
    # =====================================
    
    async def test_multi_item_orders_import(self):
        """Test importing CSV with multiple rows having same Order ID"""
        print("\n🔍 TEST 2: MULTI-ITEM ORDERS IMPORT (CRITICAL)")
        print("=" * 60)
        
        try:
            # Create test CSV with multi-item order
            csv_content = """Order ID,Order Date,Customer Name,Billing No.,SKU,Qty,Price,Place,State,Pincode,Live Status,Pickup Status
TEST-MULTI-001,15/03/2024,John Smith Multi,9876543210,SKU-CHAIR-001,1,2500,Mumbai,Maharashtra,400001,delivered,
TEST-MULTI-001,15/03/2024,John Smith Multi,9876543210,SKU-TABLE-002,1,5000,Mumbai,Maharashtra,400001,delivered,
TEST-MULTI-001,15/03/2024,John Smith Multi,9876543210,SKU-CUSHION-003,2,500,Mumbai,Maharashtra,400001,delivered,
TEST-SINGLE-001,16/03/2024,Jane Doe Single,9876543211,SKU-SOFA-004,1,15000,Delhi,Delhi,110001,delivered,"""
            
            # Create file-like object
            csv_file = io.StringIO(csv_content)
            csv_bytes = csv_content.encode('utf-8')
            
            print("1. Creating test CSV with multi-item orders...")
            print("   - Order TEST-MULTI-001: 3 items (chair, table, 2x cushions)")
            print("   - Order TEST-SINGLE-001: 1 item (sofa)")
            
            # Import the CSV
            files = {
                'file': ('test_multi_items.csv', csv_bytes, 'text/csv')
            }
            
            print("2. Importing multi-item CSV...")
            response = await self.client.post(
                f"{BACKEND_URL}/orders/import-historical",
                files=files,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Multi-item import failed: {response.status_code} - {response.text}")
                return False
            
            import_result = response.json()
            print(f"✅ Import response: {import_result}")
            
            # Verify all items were imported (no skipping)
            expected_imported = 4  # All 4 rows should be imported
            if import_result['imported'] != expected_imported:
                print(f"❌ Expected {expected_imported} items imported, got {import_result['imported']}")
                print(f"   Skipped: {import_result['skipped']}, Errors: {import_result['errors']}")
                return False
            
            print(f"✅ All {expected_imported} items imported successfully (no skipping)")
            
            # Verify in database - check that all items exist
            print("3. Verifying database contains all imported items...")
            
            # Search for TEST-MULTI-001 orders
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=TEST-MULTI-001", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Database verification failed: {response.status_code}")
                return False
            
            search_result = response.json()
            multi_items = search_result['items']
            
            # Should have 3 orders with same order_number but different ids
            if len(multi_items) != 3:
                print(f"❌ Expected 3 multi-items, found {len(multi_items)}")
                return False
            
            print(f"✅ Found {len(multi_items)} items for order TEST-MULTI-001")
            
            # Verify each has unique ID but same order_number
            order_numbers = set()
            order_ids = set()
            skus = set()
            
            for item in multi_items:
                order_numbers.add(item['order_number'])
                order_ids.add(item['id'])
                skus.add(item['sku'])
                print(f"   📦 ID: {item['id'][:12]}..., Order#: {item['order_number']}, SKU: {item['sku']}")
            
            if len(order_numbers) != 1:
                print(f"❌ Expected 1 unique order_number, got {len(order_numbers)}")
                return False
            
            if len(order_ids) != 3:
                print(f"❌ Expected 3 unique IDs, got {len(order_ids)}")
                return False
            
            if len(skus) != 3:
                print(f"❌ Expected 3 unique SKUs, got {len(skus)}")
                return False
            
            print("✅ Multi-item structure correct: same order_number, unique IDs, unique SKUs")
            
            # Verify single item order also imported
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=TEST-SINGLE-001", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Single item verification failed: {response.status_code}")
                return False
            
            single_result = response.json()
            if len(single_result['items']) != 1:
                print(f"❌ Expected 1 single item, found {len(single_result['items'])}")
                return False
            
            print("✅ Single item order also imported correctly")
            
            print("\n🎉 MULTI-ITEM ORDERS IMPORT: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Multi-item orders import error: {e}")
            return False
    
    # =====================================
    # TEST 3: MASTER SKU SYNC ENDPOINTS (HIGH)
    # =====================================
    
    async def test_master_sku_sync_endpoints(self):
        """Test Master SKU sync functionality"""
        print("\n🔍 TEST 3: MASTER SKU SYNC ENDPOINTS (HIGH)")
        print("=" * 60)
        
        try:
            # First create a master SKU mapping
            print("1. Creating test master SKU mapping...")
            
            master_sku_data = {
                "master_sku": "MASTER-TEST-CHAIR-001",
                "product_name": "Test Premium Chair",
                "category": "Furniture",
                "amazon_sku": "AMZ-CHAIR-001",
                "amazon_asin": "B08TEST001",
                "flipkart_sku": "FLP-CHAIR-001",
                "cost_price": 2000.0,
                "selling_price": 4000.0
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/master-sku/",
                json=master_sku_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Master SKU creation failed: {response.status_code} - {response.text}")
                return False
            
            master_sku_result = response.json()
            print(f"✅ Master SKU created: {master_sku_result['master_sku']}")
            print(f"   Auto-sync result: {master_sku_result.get('orders_updated', 0)} orders updated")
            
            # Create test orders with matching SKUs
            print("2. Creating test orders with matching SKUs...")
            
            test_orders = [
                {
                    "channel": "amazon",
                    "order_number": "AMZ-TEST-001",
                    "order_date": datetime.now(timezone.utc).isoformat(),
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": "Test Customer 1",
                    "phone": "9876543210",
                    "city": "Mumbai",
                    "state": "Maharashtra", 
                    "pincode": "400001",
                    "sku": "AMZ-CHAIR-001",  # Matches amazon_sku
                    "product_name": "Amazon Chair",
                    "price": 4000.0
                },
                {
                    "channel": "flipkart",
                    "order_number": "FLP-TEST-001", 
                    "order_date": datetime.now(timezone.utc).isoformat(),
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": "Test Customer 2",
                    "phone": "9876543211",
                    "city": "Delhi",
                    "state": "Delhi",
                    "pincode": "110001", 
                    "sku": "FLP-CHAIR-001",  # Matches flipkart_sku
                    "product_name": "Flipkart Chair",
                    "price": 3800.0
                },
                {
                    "channel": "amazon",
                    "order_number": "AMZ-TEST-002",
                    "order_date": datetime.now(timezone.utc).isoformat(),
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": "Test Customer 3", 
                    "phone": "9876543212",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "pincode": "560001",
                    "sku": "DIFFERENT-SKU",  # Different SKU - should not be updated
                    "product_name": "Different Product",
                    "price": 2000.0
                }
            ]
            
            created_order_ids = []
            for order_data in test_orders:
                response = await self.client.post(
                    f"{BACKEND_URL}/orders/",
                    json=order_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code not in [200, 201]:
                    print(f"❌ Test order creation failed: {response.status_code}")
                    return False
                
                created_order = response.json()
                created_order_ids.append(created_order['id'])
                print(f"   📦 Created order: {order_data['order_number']} (SKU: {order_data['sku']})")
            
            # Test specific SKU sync endpoint
            print("3. Testing sync-orders/{master_sku} endpoint...")
            
            response = await self.client.post(
                f"{BACKEND_URL}/master-sku/sync-orders/{master_sku_data['master_sku']}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Specific SKU sync failed: {response.status_code} - {response.text}")
                return False
            
            sync_result = response.json()
            print(f"✅ Specific sync result: {sync_result}")
            
            # Should update 2 orders (Amazon and Flipkart with matching SKUs)
            if sync_result['orders_updated'] != 2:
                print(f"❌ Expected 2 orders updated, got {sync_result['orders_updated']}")
                return False
            
            print("✅ Specific SKU sync updated correct number of orders")
            
            # Test sync-all-orders endpoint
            print("4. Testing sync-all-orders endpoint...")
            
            response = await self.client.post(
                f"{BACKEND_URL}/master-sku/sync-all-orders",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Sync all orders failed: {response.status_code} - {response.text}")
                return False
            
            sync_all_result = response.json()
            print(f"✅ Sync all result: {sync_all_result}")
            
            # Verify orders were updated with master_sku field
            print("5. Verifying orders have master_sku field populated...")
            
            for order_id in created_order_ids[:2]:  # First 2 should be updated
                response = await self.client.get(
                    f"{BACKEND_URL}/orders/{order_id}",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    print(f"❌ Order retrieval failed: {response.status_code}")
                    return False
                
                order = response.json()
                if order.get('master_sku') != master_sku_data['master_sku']:
                    print(f"❌ Order {order_id} missing master_sku field")
                    return False
                
                print(f"   ✅ Order {order['order_number']}: master_sku = {order['master_sku']}")
            
            # Verify third order was NOT updated (different SKU)
            response = await self.client.get(
                f"{BACKEND_URL}/orders/{created_order_ids[2]}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Order retrieval failed: {response.status_code}")
                return False
            
            order = response.json()
            if order.get('master_sku') == master_sku_data['master_sku']:
                print(f"❌ Order with different SKU should not have master_sku")
                return False
            
            print("   ✅ Order with different SKU correctly not updated")
            
            print("\n🎉 MASTER SKU SYNC ENDPOINTS: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Master SKU sync test error: {e}")
            return False
    
    # =====================================
    # TEST 4: ORDER DATE VALIDATION (MEDIUM)
    # =====================================
    
    async def test_order_date_validation(self):
        """Test order date validation during import"""
        print("\n🔍 TEST 4: ORDER DATE VALIDATION (MEDIUM)")
        print("=" * 60)
        
        try:
            # Create CSV with invalid/missing order dates
            csv_content = """Order ID,Order Date,Customer Name,Billing No.,SKU,Qty,Price,Place,State,Pincode,Live Status
VALID-DATE-001,15/03/2024,Valid Customer,9876543210,SKU-001,1,2500,Mumbai,Maharashtra,400001,delivered
INVALID-DATE-001,,Missing Date Customer,9876543211,SKU-002,1,3000,Delhi,Delhi,110001,delivered
INVALID-DATE-002,invalid-date,Invalid Format Customer,9876543212,SKU-003,1,3500,Bangalore,Karnataka,560001,delivered
INVALID-DATE-003,32/15/2024,Invalid Day Customer,9876543213,SKU-004,1,4000,Chennai,Tamil Nadu,600001,delivered
VALID-DATE-002,16/03/2024,Another Valid Customer,9876543214,SKU-005,1,2000,Pune,Maharashtra,411001,delivered"""
            
            csv_bytes = csv_content.encode('utf-8')
            
            print("1. Creating test CSV with invalid/missing order dates...")
            print("   - 2 valid dates (15/03/2024, 16/03/2024)")
            print("   - 1 missing date (empty)")
            print("   - 1 invalid format (invalid-date)")  
            print("   - 1 invalid date (32/15/2024)")
            
            files = {
                'file': ('test_date_validation.csv', csv_bytes, 'text/csv')
            }
            
            print("2. Importing CSV with invalid dates...")
            response = await self.client.post(
                f"{BACKEND_URL}/orders/import-historical",
                files=files,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Date validation import failed: {response.status_code} - {response.text}")
                return False
            
            import_result = response.json()
            print(f"✅ Import response: {import_result}")
            
            # Verify only valid dates were imported
            expected_imported = 2  # Only 2 valid dates
            expected_errors = 3    # 3 invalid/missing dates
            
            if import_result['imported'] != expected_imported:
                print(f"❌ Expected {expected_imported} imported, got {import_result['imported']}")
                return False
            
            if import_result['errors'] != expected_errors:
                print(f"❌ Expected {expected_errors} errors, got {import_result['errors']}")
                return False
            
            print(f"✅ Correct validation: {expected_imported} imported, {expected_errors} errors")
            
            # Verify error details contain date validation messages
            if 'error_details' in import_result:
                print("3. Checking error details...")
                for error in import_result['error_details']:
                    print(f"   📝 Error: {error}")
                    if 'Order Date' not in error:
                        print(f"❌ Error should mention Order Date: {error}")
                        return False
                
                print("✅ Error messages correctly mention Order Date validation")
            
            # Verify imported orders have valid dates
            print("4. Verifying imported orders have valid dates...")
            
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=VALID-DATE", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Valid date verification failed: {response.status_code}")
                return False
            
            search_result = response.json()
            valid_orders = search_result['items']
            
            if len(valid_orders) != 2:
                print(f"❌ Expected 2 valid orders, found {len(valid_orders)}")
                return False
            
            for order in valid_orders:
                if not order.get('order_date'):
                    print(f"❌ Order missing order_date: {order['order_number']}")
                    return False
                
                try:
                    # Verify date is valid ISO format
                    parsed_date = datetime.fromisoformat(order['order_date'].replace('Z', '+00:00'))
                    print(f"   ✅ Order {order['order_number']}: valid date {parsed_date.strftime('%d/%m/%Y')}")
                except ValueError:
                    print(f"❌ Order {order['order_number']}: invalid date format {order['order_date']}")
                    return False
            
            # Verify invalid date orders were NOT imported
            print("5. Verifying invalid date orders were not imported...")
            
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=INVALID-DATE", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Invalid date verification failed: {response.status_code}")
                return False
            
            invalid_search = response.json()
            if len(invalid_search['items']) > 0:
                print(f"❌ Found {len(invalid_search['items'])} orders with invalid dates - should be 0")
                return False
            
            print("✅ Invalid date orders correctly skipped")
            
            print("\n🎉 ORDER DATE VALIDATION: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Order date validation test error: {e}")
            return False
    
    # =====================================
    # MAIN TEST RUNNER
    # =====================================
    
    async def run_all_tests(self):
        """Run all critical backend tests"""
        print("🚀 FURNIVA CRM BACKEND CRITICAL TESTING")
        print("=" * 80)
        print("Testing 4 critical bug fixes from 2025-03-07")
        print("=" * 80)
        
        # Setup authentication
        if not await self.register_and_login():
            print("❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Test results
        test_results = {}
        
        # Test 1: Order Pagination System (CRITICAL)
        test_results['pagination'] = await self.test_order_pagination_system()
        
        # Test 2: Multi-Item Orders Import (CRITICAL)
        test_results['multi_item_import'] = await self.test_multi_item_orders_import()
        
        # Test 3: Master SKU Sync Endpoints (HIGH)
        test_results['master_sku_sync'] = await self.test_master_sku_sync_endpoints()
        
        # Test 4: Order Date Validation (MEDIUM)
        test_results['date_validation'] = await self.test_order_date_validation()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🏆 FINAL TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        print("-" * 80)
        print(f"OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL CRITICAL TESTS PASSED - BACKEND IS READY!")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - ISSUES NEED ATTENTION")
            return False

# =====================================
# RUN TESTS
# =====================================

async def main():
    """Main test execution"""
    async with FurnivaBackendTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)