#!/usr/bin/env python3

"""
Furniva CRM Backend Test Suite - Bulk Operations Focus
Testing newly implemented bulk operations and enhanced order creation features.
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://order-workflow-hub-1.preview.emergentagent.com/api"
headers = {"Content-Type": "application/json"}

# Test data storage
test_data = {
    "access_token": None,
    "test_orders": [],
    "test_tasks": []
}

def log_test(test_name, success, details="", response_data=None):
    """Log test results with detailed information"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} {test_name}")
    if details:
        print(f"   Details: {details}")
    if response_data and not success:
        print(f"   Response: {json.dumps(response_data, indent=2)[:500]}")

def test_login():
    """Test user authentication"""
    print("\n" + "="*60)
    print("TESTING: User Authentication")
    print("="*60)
    
    # Try to login with existing test user
    login_data = {
        "email": "testuser@furniva.com", 
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            test_data["access_token"] = result["access_token"]
            headers["Authorization"] = f"Bearer {test_data['access_token']}"
            log_test("User Login", True, "Successfully logged in with existing user")
            return True
        elif response.status_code == 401:
            # User doesn't exist, create new user
            register_data = {
                "email": "testuser@furniva.com",
                "password": "testpass123", 
                "name": "Test User",
                "role": "admin"
            }
            
            reg_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
            if reg_response.status_code == 200:
                # Now login
                login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
                if login_response.status_code == 200:
                    result = login_response.json()
                    test_data["access_token"] = result["access_token"]
                    headers["Authorization"] = f"Bearer {test_data['access_token']}"
                    log_test("User Registration & Login", True, "Created new user and logged in")
                    return True
            
            log_test("User Authentication", False, "Failed to create user or login", reg_response.json() if reg_response.text else None)
            return False
        else:
            log_test("User Login", False, f"Login failed with status {response.status_code}", response.json() if response.text else None)
            return False
            
    except Exception as e:
        log_test("User Authentication", False, f"Connection error: {str(e)}")
        return False

def test_create_orders_for_bulk_testing():
    """Create test orders for bulk operations testing"""
    print("\n" + "="*60)
    print("TESTING: Creating Test Orders for Bulk Operations")
    print("="*60)
    
    success_count = 0
    
    # Create 4 test orders with enhanced fields
    orders_to_create = [
        {
            "order_number": f"TEST-BULK-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Amit Kumar",
            "phone": "9876543210",
            "phone_secondary": "8765432109",  # New field
            "shipping_address": "123 MG Road, Bangalore",
            "city": "Bangalore",
            "state": "Karnataka", 
            "pincode": "560001",
            "sku": "SOFA-001",
            "product_name": "Premium Leather Sofa",
            "quantity": 1,
            "price": 45000.00,
            "channel": "website",
            "status": "pending",
            "order_date": datetime.now().isoformat(),
            "delivery_by": (datetime.now() + timedelta(days=7)).isoformat()  # New field
        },
        {
            "order_number": f"TEST-BULK-{uuid.uuid4().hex[:8].upper()}", 
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Priya Sharma",
            "phone": "9123456789",
            "phone_secondary": "8123456789",  # New field
            "shipping_address": "456 Park Street, Kolkata",
            "city": "Kolkata",
            "state": "West Bengal",
            "pincode": "700001", 
            "sku": "TABLE-002",
            "product_name": "Wooden Dining Table",
            "quantity": 1,
            "price": 25000.00,
            "channel": "amazon",
            "status": "pending",
            "order_date": datetime.now().isoformat(),
            "delivery_by": (datetime.now() + timedelta(days=10)).isoformat()  # New field
        },
        {
            "order_number": f"TEST-BULK-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Rajesh Patel", 
            "phone": "9876543211",
            "shipping_address": "789 Commercial Street, Mumbai",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "sku": "CHAIR-003", 
            "product_name": "Ergonomic Office Chair",
            "quantity": 2,
            "price": 15000.00,
            "channel": "flipkart",
            "status": "confirmed",
            "order_date": datetime.now().isoformat()
        },
        {
            "order_number": f"TEST-BULK-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Sneha Gupta",
            "phone": "9765432108", 
            "phone_secondary": "8765432108",  # New field
            "shipping_address": "321 Anna Salai, Chennai",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600001",
            "sku": "BED-004",
            "product_name": "Queen Size Bed with Storage",
            "quantity": 1,
            "price": 35000.00,
            "channel": "website", 
            "status": "confirmed",
            "order_date": datetime.now().isoformat(),
            "delivery_by": (datetime.now() + timedelta(days=14)).isoformat()  # New field
        }
    ]
    
    for i, order_data in enumerate(orders_to_create, 1):
        try:
            response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                test_data["test_orders"].append(result["id"])
                success_count += 1
                log_test(f"Create Order {i}", True, f"Order {result['order_number']} created with ID: {result['id'][:8]}...")
                
                # Verify new fields were stored
                has_phone_secondary = bool(result.get("phone_secondary"))
                has_delivery_by = bool(result.get("delivery_by"))
                extra_details = []
                if has_phone_secondary:
                    extra_details.append("phone_secondary stored")
                if has_delivery_by:
                    extra_details.append("delivery_by stored")
                if extra_details:
                    print(f"   New Fields: {', '.join(extra_details)}")
                    
            else:
                log_test(f"Create Order {i}", False, f"Failed with status {response.status_code}", response.json() if response.text else None)
                
        except Exception as e:
            log_test(f"Create Order {i}", False, f"Error: {str(e)}")
    
    log_test("Order Creation Summary", success_count == 4, f"Created {success_count}/4 test orders")
    return success_count >= 2  # Need at least 2 orders for bulk operations

def test_create_tasks_for_bulk_testing():
    """Create test tasks for bulk operations testing"""
    print("\n" + "="*60)
    print("TESTING: Creating Test Tasks for Bulk Operations")  
    print("="*60)
    
    success_count = 0
    
    # Create 4 test tasks
    tasks_to_create = [
        {
            "title": "Follow up with Amit Kumar for sofa delivery",
            "description": "Customer needs delivery confirmation for premium sofa order",
            "status": "pending",
            "priority": "high", 
            "assigned_to": "sales_team",
            "due_date": (datetime.now() + timedelta(days=2)).isoformat()
        },
        {
            "title": "Quality check for dining table order",
            "description": "Inspect wooden dining table before dispatch to Kolkata",
            "status": "pending",
            "priority": "medium",
            "assigned_to": "quality_team",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat()
        },
        {
            "title": "Inventory check for office chairs",
            "description": "Verify stock availability for 2 ergonomic chairs",
            "status": "in_progress", 
            "priority": "medium",
            "assigned_to": "inventory_team"
        },
        {
            "title": "Installation scheduling for queen bed",
            "description": "Schedule installation team for bed with storage in Chennai",
            "status": "pending",
            "priority": "low",
            "assigned_to": "installation_team", 
            "due_date": (datetime.now() + timedelta(days=5)).isoformat()
        }
    ]
    
    for i, task_data in enumerate(tasks_to_create, 1):
        try:
            response = requests.post(f"{BASE_URL}/tasks/", json=task_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json() 
                test_data["test_tasks"].append(result["id"])
                success_count += 1
                log_test(f"Create Task {i}", True, f"Task '{result['title'][:50]}...' created with ID: {result['id'][:8]}...")
            else:
                log_test(f"Create Task {i}", False, f"Failed with status {response.status_code}", response.json() if response.text else None)
                
        except Exception as e:
            log_test(f"Create Task {i}", False, f"Error: {str(e)}")
    
    log_test("Task Creation Summary", success_count == 4, f"Created {success_count}/4 test tasks")
    return success_count >= 2  # Need at least 2 tasks for bulk operations

def test_bulk_operations_orders():
    """Test bulk operations for orders"""
    print("\n" + "="*60)
    print("TESTING: Bulk Operations - Orders")
    print("="*60)
    
    if len(test_data["test_orders"]) < 2:
        log_test("Bulk Orders Test", False, "Not enough test orders created")
        return False
        
    # Test 1: Bulk Update Orders Status
    print("\n--- Testing Bulk Update Orders ---")
    
    orders_to_update = test_data["test_orders"][:2]  # Update first 2 orders
    update_data = {
        "order_ids": orders_to_update,
        "update_fields": {
            "status": "dispatched"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/orders/bulk-update", json=update_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            expected_modified = min(2, len(orders_to_update))
            
            if result.get("modified_count") == expected_modified:
                log_test("Bulk Update Orders", True, f"Successfully updated {result['modified_count']} orders to 'dispatched' status")
                print(f"   Modified Count: {result['modified_count']}")
                print(f"   Matched Count: {result['matched_count']}")
            else:
                log_test("Bulk Update Orders", False, f"Expected {expected_modified} updates, got {result.get('modified_count')}", result)
        else:
            log_test("Bulk Update Orders", False, f"HTTP {response.status_code}", response.json() if response.text else None)
            
    except Exception as e:
        log_test("Bulk Update Orders", False, f"Error: {str(e)}")
    
    # Test 2: Bulk Delete Orders
    print("\n--- Testing Bulk Delete Orders ---")
    
    orders_to_delete = test_data["test_orders"][2:]  # Delete remaining orders
    delete_data = orders_to_delete
    
    try:
        response = requests.post(f"{BASE_URL}/orders/bulk-delete", json=delete_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            expected_deleted = len(orders_to_delete)
            
            if result.get("deleted_count") == expected_deleted:
                log_test("Bulk Delete Orders", True, f"Successfully deleted {result['deleted_count']} orders") 
                print(f"   Deleted Count: {result['deleted_count']}")
            else:
                log_test("Bulk Delete Orders", False, f"Expected {expected_deleted} deletions, got {result.get('deleted_count')}", result)
        else:
            log_test("Bulk Delete Orders", False, f"HTTP {response.status_code}", response.json() if response.text else None)
            
    except Exception as e:
        log_test("Bulk Delete Orders", False, f"Error: {str(e)}")
    
    return True

def test_bulk_operations_tasks():
    """Test bulk operations for tasks"""
    print("\n" + "="*60)
    print("TESTING: Bulk Operations - Tasks")
    print("="*60)
    
    if len(test_data["test_tasks"]) < 2:
        log_test("Bulk Tasks Test", False, "Not enough test tasks created")
        return False
        
    # Test 1: Bulk Update Tasks Status  
    print("\n--- Testing Bulk Update Tasks ---")
    
    tasks_to_update = test_data["test_tasks"][:2]  # Update first 2 tasks
    update_data = {
        "task_ids": tasks_to_update,
        "update_fields": {
            "status": "completed"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks/bulk-update", json=update_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            expected_modified = min(2, len(tasks_to_update))
            
            if result.get("modified_count") == expected_modified:
                log_test("Bulk Update Tasks", True, f"Successfully updated {result['modified_count']} tasks to 'completed' status")
                print(f"   Modified Count: {result['modified_count']}")  
                print(f"   Matched Count: {result['matched_count']}")
                print("   Note: Completion timestamp should be automatically set")
            else:
                log_test("Bulk Update Tasks", False, f"Expected {expected_modified} updates, got {result.get('modified_count')}", result)
        else:
            log_test("Bulk Update Tasks", False, f"HTTP {response.status_code}", response.json() if response.text else None)
            
    except Exception as e:
        log_test("Bulk Update Tasks", False, f"Error: {str(e)}")
    
    # Test 2: Bulk Delete Tasks
    print("\n--- Testing Bulk Delete Tasks ---")
    
    tasks_to_delete = test_data["test_tasks"][2:]  # Delete remaining tasks
    delete_data = tasks_to_delete
    
    try:
        response = requests.post(f"{BASE_URL}/tasks/bulk-delete", json=delete_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            expected_deleted = len(tasks_to_delete)
            
            if result.get("deleted_count") == expected_deleted:
                log_test("Bulk Delete Tasks", True, f"Successfully deleted {result['deleted_count']} tasks")
                print(f"   Deleted Count: {result['deleted_count']}")
            else:
                log_test("Bulk Delete Tasks", False, f"Expected {expected_deleted} deletions, got {result.get('deleted_count')}", result)
        else:
            log_test("Bulk Delete Tasks", False, f"HTTP {response.status_code}", response.json() if response.text else None)
            
    except Exception as e:
        log_test("Bulk Delete Tasks", False, f"Error: {str(e)}")
    
    return True

def test_enhanced_order_creation():
    """Test order creation with new fields (delivery_by and phone_secondary)"""
    print("\n" + "="*60)
    print("TESTING: Enhanced Order Creation with New Fields")
    print("="*60)
    
    # Create order with both new fields
    order_data = {
        "order_number": f"TEST-ENHANCED-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Vikram Singh",
        "phone": "9988776655",
        "phone_secondary": "8899776655",  # New field
        "shipping_address": "567 Brigade Road, Bangalore",
        "city": "Bangalore", 
        "state": "Karnataka",
        "pincode": "560025",
        "sku": "WARDROBE-005",
        "product_name": "Modular Wardrobe with Mirror",
        "quantity": 1,
        "price": 55000.00,
        "channel": "website",
        "status": "pending",
        "order_date": datetime.now().isoformat(),
        "delivery_by": (datetime.now() + timedelta(days=21)).isoformat()  # New field
    }
    
    try:
        response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Verify new fields are properly stored
            phone_secondary_stored = result.get("phone_secondary") == order_data["phone_secondary"]
            delivery_by_stored = bool(result.get("delivery_by"))
            
            success = phone_secondary_stored and delivery_by_stored
            
            details = []
            if phone_secondary_stored:
                details.append(f"phone_secondary: {result.get('phone_secondary')}")
            else:
                details.append("phone_secondary: MISSING")
                
            if delivery_by_stored:
                details.append(f"delivery_by: {result.get('delivery_by')[:10]}...")
            else:
                details.append("delivery_by: MISSING")
            
            log_test("Enhanced Order Creation", success, f"Order created with new fields: {', '.join(details)}")
            
            if success:
                print(f"   Order ID: {result['id'][:8]}...")
                print(f"   Order Number: {result['order_number']}")
                print(f"   Phone Secondary: {result.get('phone_secondary', 'Not stored')}")
                print(f"   Delivery By: {result.get('delivery_by', 'Not stored')}")
            
            return success
        else:
            log_test("Enhanced Order Creation", False, f"HTTP {response.status_code}", response.json() if response.text else None)
            return False
            
    except Exception as e:
        log_test("Enhanced Order Creation", False, f"Error: {str(e)}")
        return False

def run_comprehensive_tests():
    """Run all tests in sequence"""
    print("\n" + "🔥"*20 + " FURNIVA CRM BACKEND TESTING " + "🔥"*20)
    print(f"Testing Backend URL: {BASE_URL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)
    
    # Track test results
    test_results = {
        "login": False,
        "create_orders": False, 
        "create_tasks": False,
        "bulk_orders": False,
        "bulk_tasks": False,
        "enhanced_order": False
    }
    
    # Test sequence
    test_results["login"] = test_login()
    
    if test_results["login"]:
        test_results["create_orders"] = test_create_orders_for_bulk_testing()
        test_results["create_tasks"] = test_create_tasks_for_bulk_testing()
        
        if test_results["create_orders"]:
            test_results["bulk_orders"] = test_bulk_operations_orders()
            
        if test_results["create_tasks"]:
            test_results["bulk_tasks"] = test_bulk_operations_tasks()
            
        test_results["enhanced_order"] = test_enhanced_order_creation()
    
    # Final Summary
    print("\n" + "🎯"*20 + " FINAL TEST SUMMARY " + "🎯"*20)
    print("="*80)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Bulk operations are working correctly.")
    else:
        print("⚠️  Some tests failed. Review the detailed logs above.")
        
    return test_results

if __name__ == "__main__":
    results = run_comprehensive_tests()