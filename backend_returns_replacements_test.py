#!/usr/bin/env python3
"""
Backend Testing Script for Returns and Replacements Endpoints
Testing the Furniva CRM application backend APIs for Returns and Replacements functionality
"""

import requests
import json
import sys
from datetime import datetime, timezone
import uuid

# Configuration
BACKEND_URL = "https://returns-hub-9.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@furniva.com"
TEST_USER_PASSWORD = "test123"

class ReturnsReplacementsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.test_order_id = None
        self.test_replacement_id = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self):
        """Authenticate and get access token"""
        self.log("🔐 Authenticating user...")
        
        # Try to register first (in case user doesn't exist)
        register_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User",
            "role": "admin"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 201:
                self.log("✅ User registered successfully")
            elif response.status_code == 400 and "already exists" in response.text:
                self.log("ℹ️ User already exists, proceeding to login")
            else:
                self.log(f"⚠️ Registration response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log(f"⚠️ Registration failed: {e}")
        
        # Login
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log("✅ Authentication successful")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Authentication error: {e}")
            return False
    
    def create_test_order(self):
        """Create a test order for testing purposes"""
        self.log("📦 Creating test order...")
        
        order_data = {
            "channel": "website",
            "order_number": f"TEST-RETURNS-{uuid.uuid4().hex[:8].upper()}",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "customer_id": str(uuid.uuid4()),
            "customer_name": "John Smith",
            "phone": "9876543210",
            "email": "john@example.com",
            "shipping_address": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "sku": "CHAIR-001",
            "product_name": "Test Chair",
            "quantity": 1,
            "price": 5000.0,
            "total_amount": 5000.0,
            "status": "delivered"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/orders/", json=order_data)
            if response.status_code in [200, 201]:
                order = response.json()
                self.test_order_id = order["id"]
                self.log(f"✅ Test order created: {order['order_number']} (ID: {self.test_order_id})")
                return True
            else:
                self.log(f"❌ Order creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Order creation error: {e}")
            return False
    
    def test_1_returns_dashboard_analytics(self):
        """
        TEST 1: Returns Dashboard Analytics
        GET /api/return-requests/analytics/dashboard
        Should return: total_open, total_closed, pending_action, by_reason array, by_type array
        """
        self.log("\n📊 TEST 1: Returns Dashboard Analytics")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/return-requests/analytics/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Returns dashboard analytics endpoint working")
                
                # Verify response structure
                required_fields = ["total_open", "total_closed", "pending_action", "by_reason", "by_type"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log(f"✅ Response structure correct: {list(data.keys())}")
                    self.log(f"   - total_open: {data.get('total_open', 'N/A')}")
                    self.log(f"   - total_closed: {data.get('total_closed', 'N/A')}")
                    self.log(f"   - pending_action: {data.get('pending_action', 'N/A')}")
                    self.log(f"   - by_reason entries: {len(data.get('by_reason', []))}")
                    self.log(f"   - by_type entries: {len(data.get('by_type', []))}")
                    return True
                else:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                self.log(f"❌ Returns dashboard analytics failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing returns dashboard analytics: {e}")
            return False
    
    def test_2_replacement_counter_counts(self):
        """
        TEST 2: Replacement Counter Counts
        GET /api/replacement-requests/analytics/counts
        Should return: open_replacement_requests, replacements_to_be_shipped, replacements_in_transit, pickups_pending
        """
        self.log("\n🔢 TEST 2: Replacement Counter Counts")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/replacement-requests/analytics/counts")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Replacement counter counts endpoint working")
                
                # Verify response structure and numeric values
                required_fields = ["open_replacement_requests", "replacements_to_be_shipped", 
                                 "replacements_in_transit", "pickups_pending"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log(f"✅ Response structure correct: {list(data.keys())}")
                    
                    # Verify all values are numeric and >= 0
                    all_numeric = True
                    for field in required_fields:
                        value = data.get(field)
                        if not isinstance(value, (int, float)) or value < 0:
                            self.log(f"❌ Field {field} is not a valid numeric value >= 0: {value}")
                            all_numeric = False
                        else:
                            self.log(f"   - {field}: {value}")
                    
                    return all_numeric
                else:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                self.log(f"❌ Replacement counter counts failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing replacement counter counts: {e}")
            return False
    
    def test_3_replacement_undo_functionality(self):
        """
        TEST 3: Replacement Undo Functionality
        - Create a replacement request
        - Advance to "approved" status
        - Verify previous_status is saved
        - Call undo endpoint
        - Verify status reverts and previous_status is null
        """
        self.log("\n↩️ TEST 3: Replacement Undo Functionality")
        
        if not self.test_order_id:
            self.log("❌ No test order available for testing")
            return False
        
        try:
            # Step 1: Create a replacement request
            replacement_data = {
                "order_id": self.test_order_id,
                "replacement_reason": "quality",
                "replacement_type": "full_replacement",
                "notes": "Test replacement for undo functionality"
            }
            
            response = self.session.post(f"{BACKEND_URL}/replacement-requests/", json=replacement_data)
            if response.status_code not in [200, 201]:
                self.log(f"❌ Failed to create replacement: {response.status_code} - {response.text}")
                return False
            
            replacement = response.json()
            replacement_id = replacement["id"]
            self.test_replacement_id = replacement_id
            self.log(f"✅ Created replacement request: {replacement_id}")
            
            # Step 2: Advance to "approved" status
            advance_response = self.session.patch(
                f"{BACKEND_URL}/replacement-requests/{replacement_id}/advance",
                params={"next_status": "approved"}
            )
            
            if advance_response.status_code != 200:
                self.log(f"❌ Failed to advance to approved: {advance_response.status_code} - {advance_response.text}")
                return False
            
            advanced_replacement = advance_response.json()
            self.log(f"✅ Advanced replacement to approved status")
            
            # Step 3: Verify previous_status is saved
            if advanced_replacement.get("previous_status") is None:
                self.log("❌ previous_status was not saved during status advance")
                return False
            
            self.log(f"✅ previous_status saved: {advanced_replacement.get('previous_status')}")
            
            # Step 4: Call undo endpoint
            undo_response = self.session.patch(f"{BACKEND_URL}/replacement-requests/{replacement_id}/undo")
            
            if undo_response.status_code != 200:
                self.log(f"❌ Undo operation failed: {undo_response.status_code} - {undo_response.text}")
                return False
            
            undone_replacement = undo_response.json()
            self.log(f"✅ Undo operation successful")
            
            # Step 5: Verify status reverted and previous_status is null
            if undone_replacement.get("replacement_status") != advanced_replacement.get("previous_status"):
                self.log(f"❌ Status did not revert correctly. Expected: {advanced_replacement.get('previous_status')}, Got: {undone_replacement.get('replacement_status')}")
                return False
            
            if undone_replacement.get("previous_status") is not None:
                self.log(f"❌ previous_status was not cleared after undo: {undone_replacement.get('previous_status')}")
                return False
            
            self.log(f"✅ Status reverted to: {undone_replacement.get('replacement_status')}")
            self.log(f"✅ previous_status cleared: {undone_replacement.get('previous_status')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing replacement undo functionality: {e}")
            return False
    
    def test_4_dual_approval_pickup(self):
        """
        TEST 4: Dual Approval - Approve Pickup
        PATCH /api/replacement-requests/{id}/approve-pickup
        Verify pickup_approved = true, pickup_approved_by is set, pickup_approved_date is set
        """
        self.log("\n✅ TEST 4: Dual Approval - Approve Pickup")
        
        if not self.test_replacement_id:
            self.log("❌ No test replacement available for testing")
            return False
        
        try:
            response = self.session.patch(f"{BACKEND_URL}/replacement-requests/{self.test_replacement_id}/approve-pickup")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log(f"✅ Pickup approval endpoint working")
                
                # Extract replacement data from nested response
                data = response_data.get("replacement", {})
                
                # Verify pickup approval fields
                if data.get("pickup_approved") is True:
                    self.log(f"✅ pickup_approved set to: {data.get('pickup_approved')}")
                else:
                    self.log(f"❌ pickup_approved not set correctly: {data.get('pickup_approved')}")
                    return False
                
                if data.get("pickup_approved_by"):
                    self.log(f"✅ pickup_approved_by set to: {data.get('pickup_approved_by')}")
                else:
                    self.log(f"❌ pickup_approved_by not set: {data.get('pickup_approved_by')}")
                    return False
                
                if data.get("pickup_approved_date"):
                    self.log(f"✅ pickup_approved_date set to: {data.get('pickup_approved_date')}")
                else:
                    self.log(f"❌ pickup_approved_date not set: {data.get('pickup_approved_date')}")
                    return False
                
                return True
            else:
                self.log(f"❌ Pickup approval failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing pickup approval: {e}")
            return False
    
    def test_5_dual_approval_replacement(self):
        """
        TEST 5: Dual Approval - Approve Replacement
        PATCH /api/replacement-requests/{id}/approve-replacement
        Verify replacement_approved = true, replacement_approved_by is set, replacement_approved_date is set
        """
        self.log("\n✅ TEST 5: Dual Approval - Approve Replacement")
        
        if not self.test_replacement_id:
            self.log("❌ No test replacement available for testing")
            return False
        
        try:
            response = self.session.patch(f"{BACKEND_URL}/replacement-requests/{self.test_replacement_id}/approve-replacement")
            
            if response.status_code == 200:
                response_data = response.json()
                self.log(f"✅ Replacement approval endpoint working")
                
                # Extract replacement data from nested response
                data = response_data.get("replacement", {})
                
                # Verify replacement approval fields
                if data.get("replacement_approved") is True:
                    self.log(f"✅ replacement_approved set to: {data.get('replacement_approved')}")
                else:
                    self.log(f"❌ replacement_approved not set correctly: {data.get('replacement_approved')}")
                    return False
                
                if data.get("replacement_approved_by"):
                    self.log(f"✅ replacement_approved_by set to: {data.get('replacement_approved_by')}")
                else:
                    self.log(f"❌ replacement_approved_by not set: {data.get('replacement_approved_by')}")
                    return False
                
                if data.get("replacement_approved_date"):
                    self.log(f"✅ replacement_approved_date set to: {data.get('replacement_approved_date')}")
                else:
                    self.log(f"❌ replacement_approved_date not set: {data.get('replacement_approved_date')}")
                    return False
                
                return True
            else:
                self.log(f"❌ Replacement approval failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing replacement approval: {e}")
            return False
    
    def test_6_status_transition_to_resolved(self):
        """
        TEST 6: Status Transition to Resolved
        Create new replacement and advance through workflow:
        requested -> approved -> new_shipment_dispatched -> delivered -> resolved
        """
        self.log("\n🔄 TEST 6: Status Transition to Resolved")
        
        if not self.test_order_id:
            self.log("❌ No test order available for testing")
            return False
        
        try:
            # Create a new replacement for this test
            replacement_data = {
                "order_id": self.test_order_id,
                "replacement_reason": "quality",
                "replacement_type": "full_replacement",
                "notes": "Test replacement for status transitions"
            }
            
            response = self.session.post(f"{BACKEND_URL}/replacement-requests/", json=replacement_data)
            if response.status_code not in [200, 201]:
                self.log(f"❌ Failed to create replacement: {response.status_code} - {response.text}")
                return False
            
            replacement = response.json()
            replacement_id = replacement["id"]
            self.log(f"✅ Created replacement for status transition test: {replacement_id}")
            
            # Define the workflow transitions
            transitions = [
                ("requested", "approved"),
                ("approved", "new_shipment_dispatched"),
                ("new_shipment_dispatched", "delivered"),
                ("delivered", "resolved")
            ]
            
            current_status = "requested"
            
            for from_status, to_status in transitions:
                self.log(f"   Transitioning from {from_status} to {to_status}...")
                
                # Special handling for new_shipment_dispatched (requires tracking_id)
                if to_status == "new_shipment_dispatched":
                    advance_response = self.session.patch(
                        f"{BACKEND_URL}/replacement-requests/{replacement_id}/advance",
                        params={"next_status": to_status, "new_tracking_id": "TEST123"}
                    )
                else:
                    advance_response = self.session.patch(
                        f"{BACKEND_URL}/replacement-requests/{replacement_id}/advance",
                        params={"next_status": to_status}
                    )
                
                if advance_response.status_code != 200:
                    self.log(f"❌ Failed to transition to {to_status}: {advance_response.status_code} - {advance_response.text}")
                    return False
                
                updated_replacement = advance_response.json()
                actual_status = updated_replacement.get("replacement_status")
                
                if actual_status != to_status:
                    self.log(f"❌ Status transition failed. Expected: {to_status}, Got: {actual_status}")
                    return False
                
                self.log(f"   ✅ Successfully transitioned to: {actual_status}")
                current_status = actual_status
            
            # Verify final status is "resolved"
            if current_status == "resolved":
                self.log(f"✅ Final status is resolved: {current_status}")
                return True
            else:
                self.log(f"❌ Final status is not resolved: {current_status}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing status transitions: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        self.log("\n🧹 Cleaning up test data...")
        
        if self.test_order_id:
            try:
                # Delete test order
                response = self.session.delete(f"{BACKEND_URL}/orders/{self.test_order_id}")
                if response.status_code in [200, 204, 404]:
                    self.log("✅ Test order cleaned up")
                else:
                    self.log(f"⚠️ Could not delete test order: {response.status_code}")
            except Exception as e:
                self.log(f"⚠️ Error cleaning up test order: {e}")
    
    def run_all_tests(self):
        """Run all Returns and Replacements tests"""
        self.log("🚀 Starting Returns and Replacements Backend Testing")
        self.log("=" * 70)
        
        # Authenticate
        if not self.authenticate():
            self.log("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Create test order
        if not self.create_test_order():
            self.log("❌ Test order creation failed. Cannot proceed with testing.")
            return False
        
        # Run all tests
        results = {
            "TEST 1 - Returns Dashboard Analytics": self.test_1_returns_dashboard_analytics(),
            "TEST 2 - Replacement Counter Counts": self.test_2_replacement_counter_counts(),
            "TEST 3 - Replacement Undo Functionality": self.test_3_replacement_undo_functionality(),
            "TEST 4 - Dual Approval Pickup": self.test_4_dual_approval_pickup(),
            "TEST 5 - Dual Approval Replacement": self.test_5_dual_approval_replacement(),
            "TEST 6 - Status Transition to Resolved": self.test_6_status_transition_to_resolved()
        }
        
        # Clean up
        self.cleanup_test_data()
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("🎯 FINAL TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")
            if result:
                passed_tests += 1
        
        self.log("=" * 70)
        self.log(f"🏆 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL RETURNS & REPLACEMENTS TESTS PASSED!")
            return True
        else:
            self.log("⚠️ Some tests failed - see details above")
            return False

def main():
    """Main function to run the tests"""
    tester = ReturnsReplacementsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()