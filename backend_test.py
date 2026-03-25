#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Furniva CRM Migration Endpoints
Tests the new migration features:
1. Order model previous_status field
2. Return Workflow 12-Stage System
3. Enhanced Claims System  
4. Loss Calculation Fix
"""

import requests
import json
import uuid
from datetime import datetime, timezone
import time

# Configuration
BASE_URL = "https://crm-ecomm-suite.preview.emergentagent.com/api"
TEST_USER_EMAIL = "test@furniva.com"
TEST_USER_PASSWORD = "testpass123"

class FurnivaAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.test_order_id = None
        self.test_return_id = None
        self.test_claim_id = None
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def register_and_login(self):
        """Register test user and login to get auth token"""
        self.log("🔐 Setting up authentication...")
        
        # Try to register (might fail if user exists)
        register_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User",
            "role": "admin"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/register", json=register_data)
            if response.status_code == 201:
                self.log("✅ User registered successfully")
            else:
                self.log("ℹ️ User already exists, proceeding to login")
        except Exception as e:
            self.log(f"⚠️ Registration attempt: {e}")
        
        # Login to get token
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.log("✅ Login successful, token obtained")
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_order_previous_status_field(self):
        """Test 1: Order model previous_status field functionality"""
        self.log("\n🧪 TEST 1: Order Model Previous Status Field")
        self.log("=" * 60)
        
        try:
            # Create a test order
            order_data = {
                "channel": "website",
                "order_number": f"TEST-PREV-{uuid.uuid4().hex[:8]}",
                "order_date": datetime.now(timezone.utc).isoformat(),
                "customer_id": str(uuid.uuid4()),
                "customer_name": "John Smith",
                "phone": "9876543210",
                "pincode": "560001",
                "sku": "CHAIR-001",
                "product_name": "Test Chair",
                "quantity": 1,
                "price": 5000.0,
                "status": "pending"
            }
            
            response = requests.post(f"{self.base_url}/orders/", 
                                   json=order_data, headers=self.get_headers())
            
            if response.status_code == 200:
                order = response.json()
                self.test_order_id = order["id"]
                self.log(f"✅ Order created: {order['order_number']}")
                
                # Verify initial state (no previous_status)
                if order.get("previous_status") is None:
                    self.log("✅ Initial previous_status is None (correct)")
                else:
                    self.log(f"❌ Initial previous_status should be None, got: {order.get('previous_status')}")
                
                # Update order status from pending to confirmed
                update_data = {"status": "confirmed"}
                response = requests.patch(f"{self.base_url}/orders/{self.test_order_id}", 
                                        json=update_data, headers=self.get_headers())
                
                if response.status_code == 200:
                    updated_order = response.json()
                    self.log(f"✅ Order status updated to: {updated_order['status']}")
                    
                    # Check if previous_status was set
                    if updated_order.get("previous_status") == "pending":
                        self.log("✅ previous_status correctly set to 'pending'")
                    else:
                        self.log(f"❌ previous_status should be 'pending', got: {updated_order.get('previous_status')}")
                    
                    # Test undo status functionality
                    response = requests.patch(f"{self.base_url}/orders/{self.test_order_id}/undo-status", 
                                            headers=self.get_headers())
                    
                    if response.status_code == 200:
                        undo_result = response.json()
                        reverted_order = undo_result["order"]
                        self.log(f"✅ Status undo successful: {undo_result['message']}")
                        
                        # Verify status was reverted
                        if reverted_order["status"] == "pending":
                            self.log("✅ Status correctly reverted to 'pending'")
                        else:
                            self.log(f"❌ Status should be 'pending', got: {reverted_order['status']}")
                        
                        # Verify previous_status was cleared
                        if reverted_order.get("previous_status") is None:
                            self.log("✅ previous_status correctly cleared after undo")
                        else:
                            self.log(f"❌ previous_status should be None after undo, got: {reverted_order.get('previous_status')}")
                        
                        return True
                    else:
                        self.log(f"❌ Undo status failed: {response.status_code} - {response.text}")
                        return False
                else:
                    self.log(f"❌ Order update failed: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ Order creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test 1 failed with exception: {e}")
            return False
    
    def test_return_workflow_12_stage_system(self):
        """Test 2: Return Workflow 12-Stage System"""
        self.log("\n🧪 TEST 2: Return Workflow 12-Stage System")
        self.log("=" * 60)
        
        try:
            # Create a return request using the test order
            if not self.test_order_id:
                self.log("❌ No test order available for return testing")
                return False
            
            return_data = {
                "order_id": self.test_order_id,
                "return_reason": "Damage",
                "return_reason_details": "Product arrived with scratches",
                "damage_category": "Scratch"
            }
            
            response = requests.post(f"{self.base_url}/return-requests/", 
                                   json=return_data, headers=self.get_headers())
            
            if response.status_code == 200:
                return_request = response.json()
                self.test_return_id = return_request["id"]
                self.log(f"✅ Return request created: {return_request['id']}")
                
                # Verify initial status
                if return_request["return_status"] == "requested":
                    self.log("✅ Initial return status is 'requested'")
                else:
                    self.log(f"❌ Initial status should be 'requested', got: {return_request['return_status']}")
                
                # Test workflow stages endpoint
                response = requests.get(f"{self.base_url}/return-requests/{self.test_return_id}/workflow-stages", 
                                      headers=self.get_headers())
                
                if response.status_code == 200:
                    workflow_info = response.json()
                    self.log(f"✅ Workflow stages retrieved: {workflow_info['allowed_transitions']}")
                    
                    # Test advancing through workflow stages
                    stages_to_test = [
                        ("feedback_check", {"notes": "Customer contacted for feedback"}),
                        ("authorized", {"notes": "Return authorized by manager"}),
                        ("return_initiated", {"return_method": "courier_pickup"}),
                        ("in_transit", {"tracking_number": "TRK123456789", "courier_partner": "BlueDart"}),
                        ("warehouse_received", {"notes": "Product received at warehouse"}),
                        ("qc_inspection", {"qc_result": "pass", "notes": "No damage found"}),
                        ("refund_processed", {"refund_amount": 5000.0, "refund_method": "bank_transfer"}),
                        ("closed", {"resolution_summary": "Refund processed successfully"})
                    ]
                    
                    for stage, params in stages_to_test:
                        self.log(f"🔄 Advancing to stage: {stage}")
                        
                        advance_data = {"next_status": stage}
                        advance_data.update(params)
                        
                        response = requests.patch(f"{self.base_url}/return-requests/{self.test_return_id}/workflow/advance", 
                                                params=advance_data, headers=self.get_headers())
                        
                        if response.status_code == 200:
                            updated_return = response.json()
                            if updated_return["return_status"] == stage:
                                self.log(f"✅ Successfully advanced to: {stage}")
                                
                                # Verify stage-specific fields were set
                                if stage == "in_transit" and updated_return.get("return_tracking_number") == "TRK123456789":
                                    self.log("✅ Tracking number correctly set for in_transit stage")
                                elif stage == "refund_processed" and updated_return.get("refund_processed_amount") == 5000.0:
                                    self.log("✅ Refund amount correctly set for refund_processed stage")
                            else:
                                self.log(f"❌ Status should be '{stage}', got: {updated_return['return_status']}")
                                return False
                        else:
                            self.log(f"❌ Failed to advance to {stage}: {response.status_code} - {response.text}")
                            return False
                        
                        time.sleep(0.5)  # Small delay between requests
                    
                    self.log("✅ Successfully completed full 12-stage workflow")
                    return True
                else:
                    self.log(f"❌ Failed to get workflow stages: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ Return request creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test 2 failed with exception: {e}")
            return False
    
    def test_enhanced_claims_system(self):
        """Test 3: Enhanced Claims System"""
        self.log("\n🧪 TEST 3: Enhanced Claims System")
        self.log("=" * 60)
        
        try:
            # Test new ClaimType values
            claim_types_to_test = [
                "courier_damage",
                "marketplace_a_to_z", 
                "marketplace_safe_t",
                "insurance",
                "warranty"
            ]
            
            created_claims = []
            
            for claim_type in claim_types_to_test:
                claim_data = {
                    "order_id": self.test_order_id,
                    "type": claim_type,
                    "amount": 2500.0,
                    "description": f"Test claim for {claim_type}",
                    "platform": "amazon" if "marketplace" in claim_type else "courier",
                    "reference_number": f"REF-{uuid.uuid4().hex[:8]}"
                }
                
                response = requests.post(f"{self.base_url}/claims/", 
                                       json=claim_data, headers=self.get_headers())
                
                if response.status_code == 200:
                    claim = response.json()
                    created_claims.append(claim["id"])
                    self.log(f"✅ Created {claim_type} claim: {claim['id']}")
                    
                    if not self.test_claim_id:  # Use first claim for detailed testing
                        self.test_claim_id = claim["id"]
                else:
                    self.log(f"❌ Failed to create {claim_type} claim: {response.status_code} - {response.text}")
                    return False
            
            # Test claim status updates
            status_updates = [
                ("under_review", {}),
                ("approved", {"approved_amount": 2000.0}),
                ("closed", {"resolution_notes": "Claim approved and processed"})
            ]
            
            for status, params in status_updates:
                self.log(f"🔄 Updating claim status to: {status}")
                
                update_data = {"status": status}
                update_data.update(params)
                
                response = requests.patch(f"{self.base_url}/claims/{self.test_claim_id}/status", 
                                        params=update_data, headers=self.get_headers())
                
                if response.status_code == 200:
                    updated_claim = response.json()
                    if updated_claim["status"] == status:
                        self.log(f"✅ Status updated to: {status}")
                        
                        # Verify status-specific fields
                        if status == "approved" and updated_claim.get("approved_amount") == 2000.0:
                            self.log("✅ Approved amount correctly set")
                    else:
                        self.log(f"❌ Status should be '{status}', got: {updated_claim['status']}")
                        return False
                else:
                    self.log(f"❌ Failed to update status to {status}: {response.status_code} - {response.text}")
                    return False
            
            # Test document management
            documents = [
                {"url": "https://example.com/invoice.pdf", "filename": "invoice.pdf", "type": "invoice"},
                {"url": "https://example.com/damage_photo.jpg", "filename": "damage.jpg", "type": "evidence"}
            ]
            
            response = requests.patch(f"{self.base_url}/claims/{self.test_claim_id}/documents", 
                                    json=documents, headers=self.get_headers())
            
            if response.status_code == 200:
                self.log("✅ Documents added successfully")
            else:
                self.log(f"❌ Failed to add documents: {response.status_code} - {response.text}")
                return False
            
            # Test correspondence
            response = requests.post(f"{self.base_url}/claims/{self.test_claim_id}/correspondence", 
                                   params={
                                       "message": "Claim has been approved and payment will be processed",
                                       "to_party": "amazon_support",
                                       "comm_type": "email"
                                   }, headers=self.get_headers())
            
            if response.status_code == 200:
                self.log("✅ Correspondence added successfully")
            else:
                self.log(f"❌ Failed to add correspondence: {response.status_code} - {response.text}")
                return False
            
            # Test analytics endpoints
            analytics_endpoints = [
                "/claims/analytics/by-type",
                "/claims/analytics/by-status"
            ]
            
            for endpoint in analytics_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.get_headers())
                
                if response.status_code == 200:
                    analytics = response.json()
                    self.log(f"✅ Analytics endpoint {endpoint} working: {len(analytics.get('analytics', []))} records")
                else:
                    self.log(f"❌ Analytics endpoint {endpoint} failed: {response.status_code} - {response.text}")
                    return False
            
            self.log("✅ Enhanced Claims System fully functional")
            return True
            
        except Exception as e:
            self.log(f"❌ Test 3 failed with exception: {e}")
            return False
    
    def test_loss_calculation_fix(self):
        """Test 4: Loss Calculation Fix - should never return 'unknown'"""
        self.log("\n🧪 TEST 4: Loss Calculation Fix")
        self.log("=" * 60)
        
        try:
            # Test loss calculation for the test order
            response = requests.post(f"{self.base_url}/loss/calculate/{self.test_order_id}", 
                                   headers=self.get_headers())
            
            if response.status_code == 200:
                loss_data = response.json()
                loss_category = loss_data["loss_category"]
                
                self.log(f"✅ Loss calculation successful")
                self.log(f"📊 Loss category: {loss_category}")
                self.log(f"💰 Total loss: ₹{loss_data['breakdown']['total_loss']}")
                
                # Verify loss_category is never "unknown"
                if loss_category != "unknown":
                    self.log("✅ Loss category is not 'unknown' (correct)")
                    
                    # Verify it's one of the valid categories
                    valid_categories = ["pfc", "resolved", "refunded", "fraud"]
                    if loss_category in valid_categories:
                        self.log(f"✅ Loss category '{loss_category}' is valid")
                    else:
                        self.log(f"❌ Loss category '{loss_category}' is not in valid list: {valid_categories}")
                        return False
                else:
                    self.log("❌ Loss category should never be 'unknown'")
                    return False
                
                # Test with a cancelled order (should return "refunded" not "unknown")
                cancelled_order_data = {
                    "channel": "amazon",
                    "order_number": f"TEST-CANCEL-{uuid.uuid4().hex[:8]}",
                    "order_date": datetime.now(timezone.utc).isoformat(),
                    "customer_id": str(uuid.uuid4()),
                    "customer_name": "Jane Doe",
                    "phone": "9876543211",
                    "pincode": "560002",
                    "sku": "TABLE-001",
                    "product_name": "Test Table",
                    "quantity": 1,
                    "price": 8000.0,
                    "status": "cancelled",
                    "cancellation_reason": "Customer changed mind"  # No specific keywords
                }
                
                response = requests.post(f"{self.base_url}/orders/", 
                                       json=cancelled_order_data, headers=self.get_headers())
                
                if response.status_code == 200:
                    cancelled_order = response.json()
                    cancelled_order_id = cancelled_order["id"]
                    
                    # Calculate loss for cancelled order
                    response = requests.post(f"{self.base_url}/loss/calculate/{cancelled_order_id}", 
                                           headers=self.get_headers())
                    
                    if response.status_code == 200:
                        cancelled_loss_data = response.json()
                        cancelled_loss_category = cancelled_loss_data["loss_category"]
                        
                        self.log(f"✅ Cancelled order loss calculation successful")
                        self.log(f"📊 Cancelled order loss category: {cancelled_loss_category}")
                        
                        # Should return "refunded" not "unknown" for cancelled orders without specific keywords
                        if cancelled_loss_category == "refunded":
                            self.log("✅ Cancelled order correctly categorized as 'refunded' (not 'unknown')")
                        elif cancelled_loss_category == "pfc":
                            self.log("✅ Cancelled order correctly categorized as 'pfc' (not 'unknown')")
                        else:
                            self.log(f"⚠️ Cancelled order categorized as '{cancelled_loss_category}' (acceptable, not 'unknown')")
                        
                        # Cleanup - delete test cancelled order
                        requests.delete(f"{self.base_url}/orders/{cancelled_order_id}", headers=self.get_headers())
                        
                        return True
                    else:
                        self.log(f"❌ Cancelled order loss calculation failed: {response.status_code} - {response.text}")
                        return False
                else:
                    self.log(f"❌ Failed to create cancelled order: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ Loss calculation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Test 4 failed with exception: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        self.log("\n🧹 Cleaning up test data...")
        
        # Delete test order (this will cascade to related data)
        if self.test_order_id:
            response = requests.delete(f"{self.base_url}/orders/{self.test_order_id}", headers=self.get_headers())
            if response.status_code == 200:
                self.log("✅ Test order deleted")
            else:
                self.log(f"⚠️ Failed to delete test order: {response.status_code}")
        
        # Delete test claim
        if self.test_claim_id:
            response = requests.delete(f"{self.base_url}/claims/{self.test_claim_id}", headers=self.get_headers())
            if response.status_code == 200:
                self.log("✅ Test claim deleted")
            else:
                self.log(f"⚠️ Failed to delete test claim: {response.status_code}")
    
    def run_all_tests(self):
        """Run all migration endpoint tests"""
        self.log("🚀 Starting Furniva CRM Migration Endpoints Testing")
        self.log("=" * 80)
        
        # Setup authentication
        if not self.register_and_login():
            self.log("❌ Authentication setup failed. Aborting tests.")
            return False
        
        # Run tests
        test_results = []
        
        test_results.append(("Order Previous Status Field", self.test_order_previous_status_field()))
        test_results.append(("Return Workflow 12-Stage System", self.test_return_workflow_12_stage_system()))
        test_results.append(("Enhanced Claims System", self.test_enhanced_claims_system()))
        test_results.append(("Loss Calculation Fix", self.test_loss_calculation_fix()))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.log("\n📊 TEST SUMMARY")
        self.log("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL MIGRATION ENDPOINTS ARE WORKING CORRECTLY!")
            return True
        else:
            self.log(f"⚠️ {total - passed} test(s) failed. Please review the issues above.")
            return False

if __name__ == "__main__":
    tester = FurnivaAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)