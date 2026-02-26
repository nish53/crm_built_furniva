#!/usr/bin/env python3
"""
Furniva Operations Hub Backend Testing Suite
Tests all critical backend functionality including Amazon TXT import
"""

import asyncio
import requests
import json
import tempfile
import os
from datetime import datetime, timezone
from typing import Dict, Optional
import uuid

# Configuration
BASE_URL = "https://order-workflow-hub-1.preview.emergentagent.com/api"
TEST_EMAIL = "furniva.test@example.com"
TEST_PASSWORD = "FurnivaTest2024!"
AMAZON_FILE_URL = "https://customer-assets.emergentagent.com/job_f2de6cc3-8aa1-4379-80d9-a437283f6fc0/artifacts/lry81d6f_136186573948020509.txt"

class BackendTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.test_results = {}
        
    def log_test(self, test_name: str, success: bool, message: str, details: dict = None):
        """Log test results"""
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def make_request(self, method: str, endpoint: str, data=None, files=None, headers=None):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if self.token:
            request_headers["Authorization"] = f"Bearer {self.token}"
        
        if headers:
            request_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            request_headers.pop("Content-Type", None)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == "POST":
                if files:
                    response = requests.post(url, files=files, data=data, headers=request_headers, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=request_headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            return type('Response', (), {
                'status_code': 0, 
                'text': str(e),
                'json': lambda: {"error": str(e)}
            })()
    
    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "name": "Furniva Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": "admin",
            "phone": "+91-9876543210"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        
        if response.status_code == 201 or response.status_code == 200:
            try:
                data = response.json()
                if data.get("access_token"):
                    self.token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.log_test("User Registration", True, "Successfully registered and got token")
                    return True
                else:
                    self.log_test("User Registration", False, "No access token in response", {"response": data})
            except:
                self.log_test("User Registration", False, "Invalid JSON response", {"text": response.text})
        elif response.status_code == 400 and "already registered" in response.text:
            # Try login instead
            return self.test_user_login()
        else:
            self.log_test("User Registration", False, f"HTTP {response.status_code}", {"text": response.text})
        
        return False
    
    def test_user_login(self):
        """Test user login"""
        credentials = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", credentials)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("access_token"):
                    self.token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.log_test("User Login", True, "Successfully logged in and got token")
                    return True
                else:
                    self.log_test("User Login", False, "No access token in response", {"response": data})
            except:
                self.log_test("User Login", False, "Invalid JSON response", {"text": response.text})
        else:
            self.log_test("User Login", False, f"HTTP {response.status_code}", {"text": response.text})
        
        return False
    
    def download_amazon_file(self):
        """Download Amazon TXT file for testing"""
        try:
            response = requests.get(AMAZON_FILE_URL, timeout=60)
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(response.text)
                    self.log_test("Amazon File Download", True, f"Downloaded file to {f.name}")
                    return f.name
            else:
                self.log_test("Amazon File Download", False, f"HTTP {response.status_code}", {"url": AMAZON_FILE_URL})
        except Exception as e:
            self.log_test("Amazon File Download", False, f"Download failed: {str(e)}")
        
        return None
    
    def test_amazon_txt_import(self):
        """Test Amazon TXT file import - MOST CRITICAL TEST"""
        if not self.token:
            self.log_test("Amazon TXT Import", False, "No authentication token")
            return False
        
        # Download the file
        file_path = self.download_amazon_file()
        if not file_path:
            return False
        
        try:
            # Prepare file for upload
            with open(file_path, 'rb') as f:
                files = {
                    'file': ('amazon_orders.txt', f, 'text/plain')
                }
                
                # Channel needs to be a query parameter, not form data
                response = self.make_request("POST", "/orders/import-csv?channel=amazon", files=files)
            
            # Clean up temp file
            os.unlink(file_path)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") and data.get("imported", 0) > 0:
                        self.log_test("Amazon TXT Import", True, 
                                    f"Imported {data.get('imported')} orders, skipped {data.get('skipped', 0)}", 
                                    data)
                        return True
                    elif data.get("success") and data.get("imported", 0) == 0:
                        self.log_test("Amazon TXT Import", False, 
                                    "No orders imported - check file format or duplicates", data)
                    else:
                        self.log_test("Amazon TXT Import", False, "Import failed", data)
                except:
                    self.log_test("Amazon TXT Import", False, "Invalid JSON response", {"text": response.text})
            else:
                self.log_test("Amazon TXT Import", False, f"HTTP {response.status_code}", {"text": response.text})
        
        except Exception as e:
            self.log_test("Amazon TXT Import", False, f"Exception: {str(e)}")
            # Clean up temp file if still exists
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        return False
    
    def test_order_management(self):
        """Test Order CRUD operations - FOCUS ON DISPATCH_BY DATE FIX"""
        if not self.token:
            self.log_test("Order Management", False, "No authentication token")
            return False
        
        # Test creating an order
        order_data = {
            "channel": "amazon",
            "order_number": f"TEST-{uuid.uuid4()}",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "dispatch_by": datetime.now(timezone.utc).isoformat(),
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Test Customer",
            "phone": "+91-9876543210",
            "shipping_address": "Test Address",
            "city": "Mumbai",
            "state": "Maharashtra", 
            "pincode": "400001",
            "sku": "TEST-SKU-001",
            "product_name": "Test Furniture",
            "quantity": 1,
            "price": 15000.0
        }
        
        # Create order
        response = self.make_request("POST", "/orders/", order_data)
        
        if response.status_code == 200:
            try:
                order = response.json()
                order_id = order.get("id")
                
                # CRITICAL TEST: Get orders list - should work after dispatch_by fix
                list_response = self.make_request("GET", "/orders/")
                if list_response.status_code == 200:
                    try:
                        orders = list_response.json()
                        if isinstance(orders, list):
                            # Verify we can retrieve all 97+ orders without validation errors
                            order_count = len(orders)
                            
                            # Test getting specific order
                            get_response = self.make_request("GET", f"/orders/{order_id}")
                            if get_response.status_code == 200:
                                
                                # Test updating order
                                update_data = {"status": "confirmed"}
                                update_response = self.make_request("PATCH", f"/orders/{order_id}", update_data)
                                if update_response.status_code == 200:
                                    self.log_test("Order Management", True, 
                                                f"✅ DISPATCH_BY FIX SUCCESSFUL - Retrieved {order_count} orders without validation errors", 
                                                {"order_id": order_id, "total_orders": order_count})
                                    return True
                                else:
                                    self.log_test("Order Management", False, 
                                                f"Update failed: HTTP {update_response.status_code}", 
                                                {"response": update_response.text})
                            else:
                                self.log_test("Order Management", False, 
                                            f"Get order failed: HTTP {get_response.status_code}", 
                                            {"response": get_response.text})
                        else:
                            self.log_test("Order Management", False, "Orders list is not an array", 
                                        {"response_type": type(orders)})
                    except Exception as parse_error:
                        self.log_test("Order Management", False, 
                                    f"❌ ORDER LIST PARSING FAILED: {str(parse_error)}", 
                                    {"raw_response": list_response.text[:500]})
                else:
                    self.log_test("Order Management", False, 
                                f"❌ GET ORDERS STILL FAILING: HTTP {list_response.status_code} - dispatch_by fix may not be complete", 
                                {"response": list_response.text[:500]})
            except Exception as e:
                self.log_test("Order Management", False, f"Exception: {str(e)}")
        else:
            self.log_test("Order Management", False, f"Create order failed: HTTP {response.status_code}")
        
        return False
    
    def test_dashboard_stats(self):
        """Test Dashboard stats API"""
        if not self.token:
            self.log_test("Dashboard Stats", False, "No authentication token")
            return False
        
        response = self.make_request("GET", "/dashboard/stats")
        
        if response.status_code == 200:
            try:
                stats = response.json()
                required_fields = ['total_orders', 'pending_orders', 'dispatched_today', 
                                 'pending_tasks', 'revenue_today']
                
                if all(field in stats for field in required_fields):
                    self.log_test("Dashboard Stats", True, "All required stats present", stats)
                    return True
                else:
                    missing = [f for f in required_fields if f not in stats]
                    self.log_test("Dashboard Stats", False, f"Missing fields: {missing}", stats)
            except:
                self.log_test("Dashboard Stats", False, "Invalid JSON response", {"text": response.text})
        else:
            self.log_test("Dashboard Stats", False, f"HTTP {response.status_code}", {"text": response.text})
        
        return False
    
    def test_recent_orders(self):
        """Test recent orders API - Should work without date errors after dispatch_by fix"""
        if not self.token:
            self.log_test("Recent Orders", False, "No authentication token")
            return False
        
        response = self.make_request("GET", "/dashboard/recent-orders")
        
        if response.status_code == 200:
            try:
                orders = response.json()
                if isinstance(orders, list):
                    # Verify dates are properly formatted for any orders with dispatch_by
                    date_errors = []
                    for order in orders:
                        if order.get("dispatch_by"):
                            try:
                                # Try to parse the date to verify it's valid
                                datetime.fromisoformat(order["dispatch_by"].replace('Z', '+00:00'))
                            except (ValueError, AttributeError) as e:
                                date_errors.append(f"Order {order.get('order_number', 'unknown')}: {str(e)}")
                    
                    if not date_errors:
                        self.log_test("Recent Orders", True, 
                                    f"✅ DISPATCH_BY DATE FIX VERIFIED - {len(orders)} recent orders with proper date formatting", 
                                    {"count": len(orders), "sample_order": orders[0] if orders else None})
                        return True
                    else:
                        self.log_test("Recent Orders", False, 
                                    f"❌ DATE VALIDATION ERRORS PERSIST: {len(date_errors)} orders with invalid dates", 
                                    {"errors": date_errors[:3]})  # Show first 3 errors
                else:
                    self.log_test("Recent Orders", False, "Response is not a list", {"response": orders})
            except Exception as e:
                self.log_test("Recent Orders", False, f"❌ DASHBOARD ENDPOINT FAILED: {str(e)}", {"text": response.text})
        else:
            self.log_test("Recent Orders", False, f"❌ DASHBOARD ENDPOINT HTTP ERROR: {response.status_code}", {"text": response.text})
        
        return False
    
    def test_financial_api(self):
        """Test Financial API - Medium Priority"""
        if not self.token:
            self.log_test("Financial API", False, "No authentication token")
            return False
        
        # First create an order to calculate financials for
        order_data = {
            "channel": "amazon",
            "order_number": f"FINANCE-TEST-{uuid.uuid4()}",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "dispatch_by": datetime.now(timezone.utc).isoformat(),
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Finance Test Customer",
            "phone": "+91-9876543210",
            "shipping_address": "Test Address",
            "city": "Mumbai",
            "state": "Maharashtra", 
            "pincode": "400001",
            "sku": "FINANCE-SKU-001",
            "product_name": "Test Financial Product",
            "quantity": 1,
            "price": 25000.0
        }
        
        order_response = self.make_request("POST", "/orders/", order_data)
        if order_response.status_code != 200:
            self.log_test("Financial API", False, "Could not create test order")
            return False
        
        order = order_response.json()
        order_id = order.get("id")
        
        # Test financial calculation
        financial_params = {
            "product_cost": 15000.0,
            "shipping_cost": 500.0,
            "packaging_cost": 100.0,
            "installation_cost": 200.0,
            "marketplace_commission_rate": 15.0
        }
        
        # Build query string for GET-style parameters
        param_str = "&".join([f"{k}={v}" for k, v in financial_params.items()])
        calc_url = f"/financials/calculate/{order_id}?{param_str}"
        calc_response = self.make_request("POST", calc_url)
        
        if calc_response.status_code == 200:
            try:
                financial_data = calc_response.json()
                required_fields = ['gross_profit', 'profit_margin', 'net_revenue']
                
                if all(field in financial_data for field in required_fields):
                    # Test profit analysis
                    analysis_response = self.make_request("GET", "/financials/profit-analysis")
                    if analysis_response.status_code == 200:
                        self.log_test("Financial API", True, "Financial calculations working", 
                                    {"profit": financial_data.get("gross_profit")})
                        return True
                    else:
                        self.log_test("Financial API", False, "Profit analysis failed")
                else:
                    self.log_test("Financial API", False, f"Missing fields in response: {required_fields}")
            except:
                self.log_test("Financial API", False, "Invalid JSON in financial response")
        else:
            self.log_test("Financial API", False, f"Financial calculation failed: HTTP {calc_response.status_code}")
        
        return False
    
    def test_task_management(self):
        """Test Task Management API - Medium Priority"""
        if not self.token:
            self.log_test("Task Management", False, "No authentication token")
            return False
        
        # Create a test task
        task_data = {
            "title": "Test Task",
            "description": "This is a test task for API verification",
            "priority": "high",
            "due_date": datetime.now(timezone.utc).isoformat()
        }
        
        # Create task
        response = self.make_request("POST", "/tasks/", task_data)
        
        if response.status_code == 200:
            try:
                task = response.json()
                task_id = task.get("id")
                
                # Test getting tasks list
                list_response = self.make_request("GET", "/tasks/")
                if list_response.status_code == 200:
                    tasks = list_response.json()
                    if isinstance(tasks, list):
                        
                        # Test updating task status
                        update_response = self.make_request("PATCH", f"/tasks/{task_id}", 
                                                          {"status": "completed"})
                        if update_response.status_code == 200:
                            self.log_test("Task Management", True, "Task CRUD operations successful", 
                                        {"task_id": task_id})
                            return True
                        else:
                            self.log_test("Task Management", False, "Task update failed")
                    else:
                        self.log_test("Task Management", False, "Tasks list not an array")
                else:
                    self.log_test("Task Management", False, "Get tasks failed")
            except Exception as e:
                self.log_test("Task Management", False, f"Exception: {str(e)}")
        else:
            self.log_test("Task Management", False, f"Create task failed: HTTP {response.status_code}")
        
        return False
    
    def run_all_tests(self):
        """Run all backend tests in priority order"""
        print("🔄 Starting Furniva Operations Hub Backend Tests...")
        print(f"🎯 Base URL: {BASE_URL}")
        print("=" * 60)
        
        # HIGH Priority Tests
        print("\n🔥 HIGH PRIORITY TESTS:")
        
        # Authentication first
        auth_success = self.test_user_registration()
        
        if auth_success:
            # Critical Amazon TXT import test
            self.test_amazon_txt_import()
            
            # Core order management
            self.test_order_management()
            
            # Dashboard functionality
            self.test_dashboard_stats()
            self.test_recent_orders()
        
        # MEDIUM Priority Tests  
        if auth_success:
            print("\n📊 MEDIUM PRIORITY TESTS:")
            self.test_financial_api()
            self.test_task_management()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY:")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"  - {test_name}: {result['message']}")
        
        print("\n" + "=" * 60)
        return successful_tests, failed_tests, self.test_results

if __name__ == "__main__":
    tester = BackendTester()
    success_count, failure_count, results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if failure_count == 0 else 1
    exit(exit_code)