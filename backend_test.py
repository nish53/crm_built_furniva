#!/usr/bin/env python3
"""
Backend Testing for Furniva CRM - New Features
Testing:
1. Return/Replacement Request order_id filter
2. Smart Duplicate Check for CSV Import
"""

import requests
import json
import csv
import io
import tempfile
import os
import urllib.parse
from datetime import datetime, timezone

# Backend URL from environment
BACKEND_URL = "https://furniture-flow-pro.preview.emergentagent.com/api"

# Test credentials - will create a test user
TEST_EMAIL = "test@furniva.com"
TEST_PASSWORD = "testpass123"

class FurnivaBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_order_id = None
        self.test_return_id = None
        self.test_replacement_id = None
        
    def authenticate(self):
        """Authenticate and get access token"""
        print("🔐 Authenticating...")
        
        # Try to register first (in case user doesn't exist)
        register_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Test User",
            "role": "admin"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                print("✅ User registered successfully")
        except:
            pass  # User might already exist
        
        # Login
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def create_test_order(self):
        """Create a test order for testing filters"""
        print("\n📦 Creating test order...")
        
        order_data = {
            "order_number": f"TEST-ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_date": datetime.now().isoformat(),
            "customer_id": f"CUST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_name": "John Doe",
            "phone": "9876543210",
            "email": "john@example.com",
            "pincode": "560001",
            "sku": "CHAIR-001",
            "product_name": "Ergonomic Office Chair",
            "quantity": 1,
            "price": 15000.0,
            "status": "delivered",  # Delivered status for post-delivery returns
            "channel": "website"
        }
        
        response = self.session.post(f"{BACKEND_URL}/orders/", json=order_data)
        if response.status_code == 200:
            result = response.json()
            self.test_order_id = result["id"]
            print(f"✅ Test order created: {self.test_order_id}")
            return True
        else:
            print(f"❌ Failed to create test order: {response.status_code} - {response.text}")
            return False
    
    def create_test_return_request(self):
        """Create a test return request"""
        print("\n🔄 Creating test return request...")
        
        return_data = {
            "order_id": self.test_order_id,
            "return_reason": "damaged",
            "damage_description": "Product arrived with scratches",
            "damage_images": ["https://example.com/damage1.jpg"]
        }
        
        # Add cancellation_reason as query parameter
        response = self.session.post(
            f"{BACKEND_URL}/return-requests/?cancellation_reason=Product damaged during shipping",
            json=return_data
        )
        
        if response.status_code == 200:
            result = response.json()
            self.test_return_id = result["id"]
            print(f"✅ Test return request created: {self.test_return_id}")
            return True
        else:
            print(f"❌ Failed to create return request: {response.status_code} - {response.text}")
            return False
    
    def create_test_replacement_request(self):
        """Create a test replacement request"""
        print("\n🔄 Creating test replacement request...")
        
        replacement_data = {
            "order_id": self.test_order_id,
            "replacement_reason": "damaged",
            "replacement_type": "full_replacement",
            "damage_description": "Product has manufacturing defect",
            "damage_images": ["https://example.com/defect1.jpg"],
            "notes": "Customer reported defective product"
        }
        
        response = self.session.post(f"{BACKEND_URL}/replacement-requests/", json=replacement_data)
        
        if response.status_code == 200:
            result = response.json()
            self.test_replacement_id = result["id"]
            print(f"✅ Test replacement request created: {self.test_replacement_id}")
            return True
        else:
            print(f"❌ Failed to create replacement request: {response.status_code} - {response.text}")
            return False
    
    def test_return_request_order_filter(self):
        """Test 1: Return request order_id filter"""
        print("\n🧪 TEST 1: Return Request order_id Filter")
        print("=" * 50)
        
        # Test filtering by order_id
        response = self.session.get(f"{BACKEND_URL}/return-requests/?order_id={self.test_order_id}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ GET /api/return-requests/?order_id={self.test_order_id}")
            print(f"   Found {len(results)} return requests for this order")
            
            # Verify the returned request matches our test order
            if len(results) > 0 and results[0]["order_id"] == self.test_order_id:
                print(f"   ✅ Correct order_id filter: {results[0]['order_id']}")
                return True
            else:
                print(f"   ❌ Filter not working correctly")
                return False
        else:
            print(f"❌ Failed to filter return requests: {response.status_code} - {response.text}")
            return False
    
    def test_replacement_request_order_filter(self):
        """Test 2: Replacement request order_id filter"""
        print("\n🧪 TEST 2: Replacement Request order_id Filter")
        print("=" * 50)
        
        # Test filtering by order_id
        response = self.session.get(f"{BACKEND_URL}/replacement-requests/?order_id={self.test_order_id}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ GET /api/replacement-requests/?order_id={self.test_order_id}")
            print(f"   Found {len(results)} replacement requests for this order")
            
            # Verify the returned request matches our test order
            if len(results) > 0 and results[0]["order_id"] == self.test_order_id:
                print(f"   ✅ Correct order_id filter: {results[0]['order_id']}")
                return True
            else:
                print(f"   ❌ Filter not working correctly")
                return False
        else:
            print(f"❌ Failed to filter replacement requests: {response.status_code} - {response.text}")
            return False
    
    def create_test_csv_multi_item(self):
        """Create test CSV with multi-item orders"""
        csv_content = """order_number,customer_name,phone,sku,product_name,quantity,price,order_date
TEST-MULTI-001,Alice Johnson,9876543210,CHAIR-RED,Red Office Chair,1,12000,2024-01-15
TEST-MULTI-001,Alice Johnson,9876543210,TABLE-WOOD,Wooden Desk,1,25000,2024-01-15
TEST-MULTI-001,Alice Johnson,9876543210,CUSHION-BLUE,Blue Cushion,2,1500,2024-01-15
TEST-SINGLE-002,Bob Smith,9876543211,LAMP-LED,LED Table Lamp,1,3500,2024-01-16"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        return temp_file.name
    
    def test_smart_duplicate_check_multi_item(self):
        """Test 3A: Smart duplicate check - Multi-item orders should import"""
        print("\n🧪 TEST 3A: Smart Duplicate Check - Multi-item Orders")
        print("=" * 50)
        
        csv_file = self.create_test_csv_multi_item()
        
        try:
            # Prepare the import request
            with open(csv_file, 'rb') as f:
                files = {'file': ('test_multi_item.csv', f, 'text/csv')}
                
                # Column mappings for the CSV
                mappings = {
                    "order_number": "order_number",
                    "customer_name": "customer_name", 
                    "phone": "phone",
                    "sku": "sku",
                    "product_name": "product_name",
                    "quantity": "quantity",
                    "price": "price",
                    "order_date": "order_date"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/import/with-mapping?channel=test&column_mappings={urllib.parse.quote(json.dumps(mappings))}&delimiter=,&has_header=true&auto_lookup_master_sku=false",
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Multi-item CSV import successful")
                    print(f"   Imported: {result['imported']} orders")
                    print(f"   Skipped: {result['skipped']} orders")
                    print(f"   Errors: {result['errors']} orders")
                    
                    # Should import all 4 items (3 for TEST-MULTI-001, 1 for TEST-SINGLE-002)
                    if result['imported'] == 4:
                        print("   ✅ All multi-item orders imported correctly")
                        return True
                    else:
                        print(f"   ❌ Expected 4 imports, got {result['imported']}")
                        return False
                else:
                    print(f"❌ Multi-item import failed: {response.status_code} - {response.text}")
                    return False
        
        finally:
            # Clean up temp file
            os.unlink(csv_file)
    
    def test_smart_duplicate_check_true_duplicates(self):
        """Test 3B: Smart duplicate check - True duplicates should be skipped"""
        print("\n🧪 TEST 3B: Smart Duplicate Check - True Duplicates")
        print("=" * 50)
        
        csv_file = self.create_test_csv_multi_item()
        
        try:
            # Import the same CSV again - should skip all as true duplicates
            with open(csv_file, 'rb') as f:
                files = {'file': ('test_duplicate.csv', f, 'text/csv')}
                
                mappings = {
                    "order_number": "order_number",
                    "customer_name": "customer_name", 
                    "phone": "phone",
                    "sku": "sku",
                    "product_name": "product_name",
                    "quantity": "quantity",
                    "price": "price",
                    "order_date": "order_date"
                }
                
                data = {
                    'channel': 'test',
                    'column_mappings': json.dumps(mappings),
                    'delimiter': ',',
                    'has_header': 'true',
                    'auto_lookup_master_sku': 'false'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/import/with-mapping?channel=test&column_mappings={urllib.parse.quote(json.dumps(mappings))}&delimiter=,&has_header=true&auto_lookup_master_sku=false",
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Duplicate CSV import completed")
                    print(f"   Imported: {result['imported']} orders")
                    print(f"   Skipped: {result['skipped']} orders")
                    print(f"   Errors: {result['errors']} orders")
                    
                    # Should skip all 4 items as true duplicates (same order_number + same SKU)
                    if result['skipped'] == 4 and result['imported'] == 0:
                        print("   ✅ All true duplicates correctly skipped")
                        return True
                    else:
                        print(f"   ❌ Expected 4 skipped, 0 imported. Got {result['skipped']} skipped, {result['imported']} imported")
                        return False
                else:
                    print(f"❌ Duplicate import test failed: {response.status_code} - {response.text}")
                    return False
        
        finally:
            # Clean up temp file
            os.unlink(csv_file)
    
    def test_smart_duplicate_check_new_sku(self):
        """Test 3C: Smart duplicate check - Same order_number with NEW SKU should import"""
        print("\n🧪 TEST 3C: Smart Duplicate Check - New SKU for Existing Order")
        print("=" * 50)
        
        # Create CSV with same order number but new SKU
        csv_content = """order_number,customer_name,phone,sku,product_name,quantity,price,order_date
TEST-MULTI-001,Alice Johnson,9876543210,MIRROR-WALL,Wall Mirror,1,8000,2024-01-15"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_new_sku.csv', f, 'text/csv')}
                
                mappings = {
                    "order_number": "order_number",
                    "customer_name": "customer_name", 
                    "phone": "phone",
                    "sku": "sku",
                    "product_name": "product_name",
                    "quantity": "quantity",
                    "price": "price",
                    "order_date": "order_date"
                }
                
                data = {
                    'channel': 'test',
                    'column_mappings': json.dumps(mappings),
                    'delimiter': ',',
                    'has_header': 'true',
                    'auto_lookup_master_sku': 'false'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/import/with-mapping?channel=test&column_mappings={urllib.parse.quote(json.dumps(mappings))}&delimiter=,&has_header=true&auto_lookup_master_sku=false",
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ New SKU CSV import completed")
                    print(f"   Imported: {result['imported']} orders")
                    print(f"   Skipped: {result['skipped']} orders")
                    print(f"   Errors: {result['errors']} orders")
                    
                    # Should import 1 item (same order_number but NEW SKU)
                    if result['imported'] == 1 and result['skipped'] == 0:
                        print("   ✅ New SKU for existing order correctly imported")
                        return True
                    else:
                        print(f"   ❌ Expected 1 imported, 0 skipped. Got {result['imported']} imported, {result['skipped']} skipped")
                        return False
                else:
                    print(f"❌ New SKU import test failed: {response.status_code} - {response.text}")
                    return False
        
        finally:
            # Clean up temp file
            os.unlink(temp_file.name)
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Furniva CRM Backend Tests")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Create test data
        if not self.create_test_order():
            return False
        
        if not self.create_test_return_request():
            return False
        
        if not self.create_test_replacement_request():
            return False
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_return_request_order_filter())
        test_results.append(self.test_replacement_request_order_filter())
        test_results.append(self.test_smart_duplicate_check_multi_item())
        test_results.append(self.test_smart_duplicate_check_true_duplicates())
        test_results.append(self.test_smart_duplicate_check_new_sku())
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Both new features are working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        
        return passed == total

if __name__ == "__main__":
    tester = FurnivaBackendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)