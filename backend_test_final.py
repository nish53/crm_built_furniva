#!/usr/bin/env python3
"""
Furniva CRM Backend Testing Suite - Final Validation
Test Priority: Critical Bug Fixes from 2025-03-07

This version uses unique identifiers to avoid test interference
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
BACKEND_URL = "https://returns-hub-9.preview.emergentagent.com/api"

class FurnivaBackendTesterFinal:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.user_id = None
        self.test_id = str(uuid.uuid4())[:8]  # Unique test session ID
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def register_and_login(self):
        """Register test user and login to get auth token"""
        print("🔐 Setting up test user authentication...")
        
        # Generate unique test user
        test_email = f"test_final_{self.test_id}@example.com"
        test_password = "TestPass123!"
        
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": f"Final Test User {self.test_id}",
            "role": "admin"
        }
        
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print(f"✅ User registered: {test_email}")
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
                print(f"✅ Authentication successful")
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
    
    async def test_order_pagination_system(self):
        """Test the new paginated orders endpoint"""
        print("\n🔍 TEST 1: ORDER PAGINATION SYSTEM (CRITICAL)")
        print("=" * 60)
        
        try:
            # Test basic pagination structure
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
            
            # Test filters
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?status=delivered&skip=0&limit=100", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Status filter failed: {response.status_code}")
                return False
            
            filtered_data = response.json()
            print(f"✅ Status filter working: {len(filtered_data['items'])} delivered orders")
            
            print("\n🎉 ORDER PAGINATION SYSTEM: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Order pagination test error: {e}")
            return False
    
    async def test_multi_item_orders_import(self):
        """Test importing CSV with multiple rows having same Order ID"""
        print("\n🔍 TEST 2: MULTI-ITEM ORDERS IMPORT (CRITICAL)")
        print("=" * 60)
        
        try:
            # Create test CSV with unique order IDs
            csv_content = f"""Order ID,Order Date,Customer Name,Billing No.,SKU,Qty,Price,Place,State,Pincode,Live Status,Pickup Status
MULTI-{self.test_id}-001,15/03/2024,John Multi {self.test_id},9876543210,SKU-CHAIR-{self.test_id},1,2500,Mumbai,Maharashtra,400001,delivered,
MULTI-{self.test_id}-001,15/03/2024,John Multi {self.test_id},9876543210,SKU-TABLE-{self.test_id},1,5000,Mumbai,Maharashtra,400001,delivered,
MULTI-{self.test_id}-001,15/03/2024,John Multi {self.test_id},9876543210,SKU-CUSHION-{self.test_id},2,500,Mumbai,Maharashtra,400001,delivered,
SINGLE-{self.test_id}-001,16/03/2024,Jane Single {self.test_id},9876543211,SKU-SOFA-{self.test_id},1,15000,Delhi,Delhi,110001,delivered,"""
            
            csv_bytes = csv_content.encode('utf-8')
            
            print("1. Importing multi-item CSV with unique identifiers...")
            
            files = {'file': ('test_multi_items.csv', csv_bytes, 'text/csv')}
            
            response = await self.client.post(
                f"{BACKEND_URL}/orders/import-historical",
                files=files,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Multi-item import failed: {response.status_code} - {response.text}")
                return False
            
            import_result = response.json()
            print(f"✅ Import response: imported={import_result['imported']}, errors={import_result['errors']}")
            
            # Verify all items were imported
            if import_result['imported'] != 4:
                print(f"❌ Expected 4 items imported, got {import_result['imported']}")
                return False
            
            # Search for the multi-item order
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=MULTI-{self.test_id}-001", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Database verification failed: {response.status_code}")
                return False
            
            search_result = response.json()
            multi_items = search_result['items']
            
            if len(multi_items) != 3:
                print(f"❌ Expected 3 multi-items, found {len(multi_items)}")
                return False
            
            # Verify structure
            order_numbers = set()
            order_ids = set()
            skus = set()
            
            for item in multi_items:
                order_numbers.add(item['order_number'])
                order_ids.add(item['id'])
                skus.add(item['sku'])
            
            if len(order_numbers) != 1 or len(order_ids) != 3 or len(skus) != 3:
                print(f"❌ Multi-item structure incorrect")
                return False
            
            print("✅ Multi-item structure correct: same order_number, unique IDs and SKUs")
            
            print("\n🎉 MULTI-ITEM ORDERS IMPORT: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Multi-item orders import error: {e}")
            return False
    
    async def test_master_sku_sync_endpoints(self):
        """Test Master SKU sync functionality"""
        print("\n🔍 TEST 3: MASTER SKU SYNC ENDPOINTS (HIGH)")
        print("=" * 60)
        
        try:
            # Create unique master SKU mapping
            master_sku_data = {
                "master_sku": f"MASTER-{self.test_id}",
                "product_name": f"Test Chair {self.test_id}",
                "category": "Furniture",
                "amazon_sku": f"AMZ-{self.test_id}",
                "amazon_asin": f"B08{self.test_id}",
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
            
            # Create test order with matching SKU
            order_data = {
                "channel": "amazon",
                "order_number": f"AMZ-{self.test_id}-001",
                "order_date": datetime.now(timezone.utc).isoformat(),
                "customer_id": str(uuid.uuid4()),
                "customer_name": f"Test Customer {self.test_id}",
                "phone": "9876543210",
                "city": "Mumbai",
                "state": "Maharashtra", 
                "pincode": "400001",
                "sku": f"AMZ-{self.test_id}",  # Matches amazon_sku
                "product_name": f"Amazon Chair {self.test_id}",
                "price": 4000.0
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/orders/",
                json=order_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Test order creation failed: {response.status_code}")
                return False
            
            created_order = response.json()
            order_id = created_order['id']
            print(f"✅ Test order created: {order_data['order_number']}")
            
            # Test specific SKU sync endpoint
            response = await self.client.post(
                f"{BACKEND_URL}/master-sku/sync-orders/{master_sku_data['master_sku']}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Specific SKU sync failed: {response.status_code} - {response.text}")
                return False
            
            sync_result = response.json()
            print(f"✅ Specific sync successful: {sync_result['orders_updated']} orders updated")
            
            # Test sync-all-orders endpoint  
            response = await self.client.post(
                f"{BACKEND_URL}/master-sku/sync-all-orders",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Sync all orders failed: {response.status_code}")
                return False
            
            sync_all_result = response.json()
            print(f"✅ Sync all successful: {sync_all_result['total_orders_updated']} orders updated")
            
            # Verify order was updated with master_sku field
            response = await self.client.get(
                f"{BACKEND_URL}/orders/{order_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Order retrieval failed: {response.status_code}")
                return False
            
            order = response.json()
            if order.get('master_sku') != master_sku_data['master_sku']:
                print(f"❌ Order missing master_sku field")
                return False
            
            print(f"✅ Order updated with master_sku: {order['master_sku']}")
            
            print("\n🎉 MASTER SKU SYNC ENDPOINTS: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Master SKU sync test error: {e}")
            return False
    
    async def test_order_date_validation(self):
        """Test order date validation during import"""
        print("\n🔍 TEST 4: ORDER DATE VALIDATION (MEDIUM)")
        print("=" * 60)
        
        try:
            # Create CSV with invalid/missing order dates and unique IDs
            csv_content = f"""Order ID,Order Date,Customer Name,Billing No.,SKU,Qty,Price,Place,State,Pincode,Live Status
VALID-{self.test_id}-001,15/03/2024,Valid Customer {self.test_id},9876543210,SKU-{self.test_id}-001,1,2500,Mumbai,Maharashtra,400001,delivered
INVALID-{self.test_id}-001,,Missing Date {self.test_id},9876543211,SKU-{self.test_id}-002,1,3000,Delhi,Delhi,110001,delivered
INVALID-{self.test_id}-002,invalid-date,Invalid Format {self.test_id},9876543212,SKU-{self.test_id}-003,1,3500,Bangalore,Karnataka,560001,delivered
INVALID-{self.test_id}-003,32/15/2024,Invalid Day {self.test_id},9876543213,SKU-{self.test_id}-004,1,4000,Chennai,Tamil Nadu,600001,delivered
VALID-{self.test_id}-002,16/03/2024,Another Valid {self.test_id},9876543214,SKU-{self.test_id}-005,1,2000,Pune,Maharashtra,411001,delivered"""
            
            csv_bytes = csv_content.encode('utf-8')
            
            print("1. Importing CSV with invalid dates...")
            
            files = {'file': ('test_date_validation.csv', csv_bytes, 'text/csv')}
            
            response = await self.client.post(
                f"{BACKEND_URL}/orders/import-historical",
                files=files,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Date validation import failed: {response.status_code}")
                return False
            
            import_result = response.json()
            print(f"✅ Import response: imported={import_result['imported']}, errors={import_result['errors']}")
            
            # Verify only valid dates were imported
            if import_result['imported'] != 2 or import_result['errors'] != 3:
                print(f"❌ Expected 2 imported, 3 errors. Got imported={import_result['imported']}, errors={import_result['errors']}")
                return False
            
            # Verify error details
            if len(import_result.get('error_details', [])) != 3:
                print(f"❌ Expected 3 error details, got {len(import_result.get('error_details', []))}")
                return False
            
            print("✅ Date validation working: only valid dates imported, invalid dates skipped")
            
            # Verify valid orders were imported
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=VALID-{self.test_id}", 
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
            
            print("✅ Valid date orders correctly imported")
            
            # Verify invalid orders were NOT imported
            response = await self.client.get(
                f"{BACKEND_URL}/orders/?search=INVALID-{self.test_id}", 
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
            
            print("\n🎉 ORDER DATE VALIDATION: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Order date validation test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all critical backend tests"""
        print("🚀 FURNIVA CRM BACKEND FINAL TESTING")
        print("=" * 80)
        print("Testing 4 critical bug fixes from 2025-03-07")
        print("=" * 80)
        
        # Setup authentication
        if not await self.register_and_login():
            print("❌ AUTHENTICATION FAILED")
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

async def main():
    """Main test execution"""
    async with FurnivaBackendTesterFinal() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)