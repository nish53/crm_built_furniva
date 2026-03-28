#!/usr/bin/env python3
"""
Backend Testing Script for Furniva CRM
Testing two specific bug fixes:
1. Historical Order Auto-Confirmation Bug Fix
2. Replacement Original Shipment Details
"""

import requests
import json
import csv
import io
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://furniture-flow-pro.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@furniva.com",
    "password": "Admin123!"
}

class FurnivaAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def authenticate(self):
        """Authenticate with the API"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log_result(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {TEST_CREDENTIALS['email']}"
                )
                return True
            else:
                self.log_result(
                    "Authentication", 
                    False, 
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_historical_order_auto_confirmation(self):
        """
        TEST 1: Historical Order Auto-Confirmation Bug Fix
        Create a test CSV and import historical order with order confirmation call marked as done
        """
        print("🎯 TEST 1: Historical Order Auto-Confirmation Bug Fix")
        print("=" * 60)
        
        # Create test CSV content
        csv_content = """Order ID,Customer Name,Billing No.,Shipping No.,Place,State,Pincode,SKU,Qty,Price,Order Date,Live Status,Order Conf Calling,Dispatch Confirmation Sent,Assembly Type
TEST-ORD-CONF-001,Test Customer,9999999999,9999999999,Test Address,Test State,123456,TEST-PRODUCT,1,5000,01/01/2026,Pending,Yes,No,Self"""
        
        try:
            # Prepare CSV file for upload
            files = {
                'file': ('test_historical_orders.csv', csv_content, 'text/csv')
            }
            
            # Import historical orders
            response = self.session.post(
                f"{BASE_URL}/orders/import-historical",
                files=files,
                timeout=60
            )
            
            if response.status_code == 200:
                import_result = response.json()
                self.log_result(
                    "Historical Order Import", 
                    True, 
                    f"Import successful: {import_result.get('imported', 0)} orders imported",
                    import_result
                )
                
                # Now search for the imported order
                search_response = self.session.get(
                    f"{BASE_URL}/orders/",
                    params={"search": "TEST-ORD-CONF-001", "limit": 10},
                    timeout=30
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    orders = search_data.get("items", [])
                    
                    if orders:
                        order = orders[0]
                        
                        # Verify auto-confirmation logic
                        expected_status = "confirmed"  # Should be auto-confirmed
                        actual_status = order.get("status")
                        order_conf_calling = order.get("order_conf_calling", False)
                        internal_notes = order.get("internal_notes", "")
                        
                        # Check all conditions
                        status_correct = actual_status == expected_status
                        conf_calling_correct = order_conf_calling == True
                        notes_contain_auto_confirm = "Auto-confirmed: Order confirmation call marked as done" in internal_notes
                        
                        if status_correct and conf_calling_correct and notes_contain_auto_confirm:
                            self.log_result(
                                "Auto-Confirmation Logic", 
                                True, 
                                f"Order correctly auto-confirmed from 'pending' to 'confirmed'",
                                {
                                    "order_number": order.get("order_number"),
                                    "status": actual_status,
                                    "order_conf_calling": order_conf_calling,
                                    "auto_confirm_note_present": notes_contain_auto_confirm
                                }
                            )
                        else:
                            self.log_result(
                                "Auto-Confirmation Logic", 
                                False, 
                                f"Auto-confirmation failed. Status: {actual_status}, Conf Calling: {order_conf_calling}, Auto-confirm note: {notes_contain_auto_confirm}",
                                {
                                    "expected_status": expected_status,
                                    "actual_status": actual_status,
                                    "order_conf_calling": order_conf_calling,
                                    "internal_notes": internal_notes
                                }
                            )
                    else:
                        self.log_result(
                            "Order Search", 
                            False, 
                            "Imported order not found in search results"
                        )
                else:
                    self.log_result(
                        "Order Search", 
                        False, 
                        f"Failed to search for imported order: {search_response.status_code}"
                    )
            else:
                self.log_result(
                    "Historical Order Import", 
                    False, 
                    f"Import failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result("Historical Order Import", False, f"Import error: {str(e)}")
    
    def test_replacement_original_shipment_details(self):
        """
        TEST 2: Replacement Original Shipment Details
        Verify replacements have original_tracking_number and original_courier fields
        """
        print("🎯 TEST 2: Replacement Original Shipment Details")
        print("=" * 60)
        
        try:
            # Get replacement requests
            response = self.session.get(
                f"{BASE_URL}/replacement-requests/",
                params={"limit": 5},
                timeout=30
            )
            
            if response.status_code == 200:
                replacements = response.json()
                
                if not replacements:
                    self.log_result(
                        "Replacement Requests Retrieval", 
                        True, 
                        "No replacements to test - this is expected if no replacement data exists"
                    )
                    return
                
                self.log_result(
                    "Replacement Requests Retrieval", 
                    True, 
                    f"Retrieved {len(replacements)} replacement requests"
                )
                
                # Test each replacement for original shipment details
                replacements_with_details = 0
                replacements_without_details = 0
                
                for i, replacement in enumerate(replacements[:5]):  # Test first 5
                    replacement_id = replacement.get("id")
                    order_id = replacement.get("order_id")
                    
                    # Check if replacement has original tracking and courier details
                    original_tracking = replacement.get("original_tracking_number")
                    original_courier = replacement.get("original_courier")
                    
                    if original_tracking or original_courier:
                        replacements_with_details += 1
                        self.log_result(
                            f"Replacement {i+1} Original Details", 
                            True, 
                            f"Has original shipment details",
                            {
                                "replacement_id": replacement_id,
                                "order_id": order_id,
                                "original_tracking_number": original_tracking or "Not set",
                                "original_courier": original_courier or "Not set"
                            }
                        )
                        
                        # Verify these match the linked order's details
                        if order_id:
                            order_response = self.session.get(
                                f"{BASE_URL}/orders/{order_id}",
                                timeout=30
                            )
                            
                            if order_response.status_code == 200:
                                order = order_response.json()
                                order_tracking = order.get("tracking_number", "")
                                order_courier = order.get("courier_name", "") or order.get("courier_partner", "")
                                
                                # Check if replacement details match order details
                                tracking_matches = (original_tracking == order_tracking) if original_tracking else True
                                courier_matches = (original_courier == order_courier) if original_courier else True
                                
                                if tracking_matches and courier_matches:
                                    self.log_result(
                                        f"Replacement {i+1} Order Match", 
                                        True, 
                                        "Original details match linked order",
                                        {
                                            "order_tracking": order_tracking,
                                            "order_courier": order_courier,
                                            "replacement_tracking": original_tracking,
                                            "replacement_courier": original_courier
                                        }
                                    )
                                else:
                                    self.log_result(
                                        f"Replacement {i+1} Order Match", 
                                        False, 
                                        "Original details don't match linked order",
                                        {
                                            "order_tracking": order_tracking,
                                            "order_courier": order_courier,
                                            "replacement_tracking": original_tracking,
                                            "replacement_courier": original_courier
                                        }
                                    )
                    else:
                        replacements_without_details += 1
                        self.log_result(
                            f"Replacement {i+1} Original Details", 
                            False, 
                            f"Missing original shipment details",
                            {
                                "replacement_id": replacement_id,
                                "order_id": order_id,
                                "original_tracking_number": original_tracking,
                                "original_courier": original_courier
                            }
                        )
                
                # Summary
                if replacements_with_details > 0:
                    self.log_result(
                        "Original Shipment Details Summary", 
                        True, 
                        f"{replacements_with_details}/{len(replacements)} replacements have original shipment details"
                    )
                else:
                    self.log_result(
                        "Original Shipment Details Summary", 
                        False, 
                        f"None of the {len(replacements)} replacements have original shipment details"
                    )
                    
            else:
                self.log_result(
                    "Replacement Requests Retrieval", 
                    False, 
                    f"Failed to retrieve replacements: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result("Replacement Original Details", False, f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Furniva CRM Backend Testing")
        print("Testing two specific bug fixes:")
        print("1. Historical Order Auto-Confirmation Bug Fix")
        print("2. Replacement Original Shipment Details")
        print("=" * 80)
        print()
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run tests
        self.test_historical_order_auto_confirmation()
        self.test_replacement_original_shipment_details()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
            print()
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = FurnivaAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)