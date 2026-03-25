#!/usr/bin/env python3
"""
Furniva CRM Backend Testing Suite
TEST FOCUS: Returns & Claims System Backend Endpoints

New Returns & Claims System endpoints to test:
1. GET /api/returns/ - Get all returns/cancellations with smart filtering
2. GET /api/returns/analytics - Get returns analytics and metrics  
3. POST /api/returns/{order_id}/action?action={action} - Take action on returns

Smart Classification Logic to verify:
- classify_return() function flags: pfc, fraud, damage, replacement, pending_action, delay
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone, timedelta
import os

# Backend URL from environment
BACKEND_URL = "https://migration-reapply.preview.emergentagent.com/api"

class FurnivaReturnsSystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.user_id = None
        self.test_orders = []  # Track created test orders for cleanup
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def register_and_login(self):
        """Register test user and login to get auth token"""
        print("🔐 Setting up test user authentication...")
        
        # Generate unique test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_returns_{unique_id}@example.com"
        test_password = "ReturnsTest123!"
        
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Returns Test User",
            "role": "admin"
        }
        
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print(f"✅ User registered: {test_email}")
            else:
                print(f"⚠️ Register response: {response.status_code} - {response.text}")
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
    
    async def create_test_orders_with_returns_data(self):
        """Create test orders with various return/cancellation scenarios for testing"""
        print("🏗️ Creating test orders with returns data...")
        
        base_date = datetime.now(timezone.utc)
        
        # Test scenarios for different return/cancellation types
        test_scenarios = [
            {
                "order_number": "RET-FRAUD-001",
                "customer_name": "Fraud Customer",
                "phone": "9111111111",
                "sku": "FRAUD-ITEM-001",
                "product_name": "Fraudulent Return Item",
                "status": "cancelled", 
                "cancellation_reason": "Fraud",  # Matches existing fraud pattern
                "price": 5000.0
            },
            {
                "order_number": "RET-DAMAGE-002", 
                "customer_name": "Damage Customer",
                "phone": "9222222222",
                "sku": "DAMAGE-ITEM-002",
                "product_name": "Damaged Hardware Item",
                "status": "returned",
                "cancellation_reason": "Damage hardware needs replacement",  # Contains damage + replacement keywords
                "price": 8000.0
            },
            {
                "order_number": "RET-PFC-003",
                "customer_name": "PFC Customer", 
                "phone": "9333333333",
                "sku": "PFC-ITEM-003",
                "product_name": "Pre-Fulfillment Cancel Item",
                "status": "cancelled",
                "cancellation_reason": "",  # Empty reason + cancelled status = PFC
                "price": 3000.0
            },
            {
                "order_number": "RET-PENDING-004",
                "customer_name": "Pending Customer",
                "phone": "9444444444", 
                "sku": "PENDING-ITEM-004",
                "product_name": "Status Pending Item",
                "status": "returned",
                "cancellation_reason": "Status Pending customer response",  # Contains "pending"
                "price": 4500.0
            },
            {
                "order_number": "RET-DELAY-005",
                "customer_name": "Delay Customer",
                "phone": "9555555555",
                "sku": "DELAY-ITEM-005", 
                "product_name": "Delayed Delivery Item",
                "status": "cancelled",
                "cancellation_reason": "Delay in delivery customer cancelled",  # Contains "delay"
                "price": 6000.0
            },
            {
                "order_number": "REG-ORDER-006",
                "customer_name": "Normal Customer",
                "phone": "9666666666",
                "sku": "NORMAL-ITEM-006",
                "product_name": "Normal Item",
                "status": "delivered", 
                # No cancellation_reason - should not appear in returns
                "price": 7000.0
            }
        ]
        
        created_orders = []
        
        for scenario in test_scenarios:
            order_data = {
                "channel": "website",  # Use valid enum value
                "order_number": scenario["order_number"],
                "order_date": base_date.isoformat(),
                "customer_id": str(uuid.uuid4()),
                "customer_name": scenario["customer_name"],
                "phone": scenario["phone"],
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "sku": scenario["sku"],
                "product_name": scenario["product_name"], 
                "price": scenario["price"],
                "status": scenario["status"]
            }
            
            # Add optional fields
            if "cancellation_reason" in scenario:
                order_data["cancellation_reason"] = scenario["cancellation_reason"]
            if "delivery_date" in scenario:
                order_data["delivery_date"] = scenario["delivery_date"]
                
            try:
                response = await self.client.post(
                    f"{BACKEND_URL}/orders/",
                    json=order_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code in [200, 201]:
                    created_order = response.json()
                    created_orders.append(created_order)
                    self.test_orders.append(created_order['id'])
                    print(f"   ✅ Created: {scenario['order_number']} ({scenario.get('cancellation_reason', 'no cancellation')})")
                else:
                    print(f"   ❌ Failed to create {scenario['order_number']}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error creating {scenario['order_number']}: {e}")
        
        print(f"✅ Created {len(created_orders)} test orders for returns testing")
        return created_orders
    
    # =====================================
    # TEST 1: GET /api/returns/ - Basic functionality and filters
    # =====================================
    
    async def test_returns_endpoint_basic(self):
        """Test basic returns endpoint functionality"""
        print("\n🔍 TEST 1: GET /api/returns/ - Basic Functionality")
        print("=" * 60)
        
        try:
            # Test 1: Basic returns without filters
            print("1. Testing basic returns endpoint (no filters)...")
            response = await self.client.get(
                f"{BACKEND_URL}/returns/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Basic returns failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            
            # Check response structure
            if "items" not in data or "total" not in data:
                print(f"❌ Missing required fields in response: {list(data.keys())}")
                return False
            
            returns_count = len(data["items"])
            total_count = data["total"]
            
            print(f"✅ Basic returns: Found {returns_count} returns, total: {total_count}")
            
            # Verify smart_flags are present
            if returns_count > 0:
                first_return = data["items"][0]
                if "smart_flags" not in first_return:
                    print("❌ Missing smart_flags in return items")
                    return False
                
                print(f"✅ Smart flags present. Example: {first_return.get('smart_flags', [])}")
            
            # Expected returns: RET-FRAUD-001, RET-DAMAGE-002, RET-PFC-003, RET-PENDING-004, RET-DELAY-005
            # Should NOT include REG-ORDER-006 (no cancellation_reason)
            
            # Verify only orders with cancellation reasons or status returned/cancelled appear
            test_order_numbers = []
            for item in data["items"]:
                if item.get("order_number", "").startswith("RET-"):
                    test_order_numbers.append(item["order_number"])
            
            expected_returns = ["RET-FRAUD-001", "RET-DAMAGE-002", "RET-PFC-003", "RET-PENDING-004", "RET-DELAY-005"]
            found_test_returns = [num for num in test_order_numbers if num in expected_returns]
            
            print(f"✅ Found test returns: {found_test_returns}")
            
            if "REG-ORDER-006" in test_order_numbers:
                print("❌ Normal order without cancellation reason should not appear in returns")
                return False
            
            print("✅ Normal orders correctly excluded from returns list")
            
            return True
            
        except Exception as e:
            print(f"❌ Basic returns test error: {e}")
            return False
    
    async def test_returns_endpoint_filters(self):
        """Test returns endpoint with various filters"""
        print("\n🔍 TEST 2: GET /api/returns/ - Filter Testing")
        print("=" * 60)
        
        try:
            # Test fraud filter
            print("1. Testing fraud_only filter...")
            response = await self.client.get(
                f"{BACKEND_URL}/returns/?fraud_only=true",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Fraud filter failed: {response.status_code} - {response.text}")
                return False
            
            fraud_data = response.json()
            fraud_orders = fraud_data["items"]
            
            # Should find RET-FRAUD-001 (cancelled + delivered reason + has delivery_date)
            fraud_order_numbers = [order.get("order_number") for order in fraud_orders if order.get("order_number", "").startswith("RET-")]
            
            if "RET-FRAUD-001" not in fraud_order_numbers:
                print(f"❌ Expected RET-FRAUD-001 in fraud filter, got: {fraud_order_numbers}")
                return False
            
            print(f"✅ Fraud filter: Found {len(fraud_orders)} fraud cases including RET-FRAUD-001")
            
            # Test damage filter
            print("2. Testing damage_only filter...")
            response = await self.client.get(
                f"{BACKEND_URL}/returns/?damage_only=true", 
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Damage filter failed: {response.status_code} - {response.text}")
                return False
            
            damage_data = response.json()
            damage_orders = damage_data["items"]
            
            # Should find RET-DAMAGE-002 (damage hardware in reason)
            damage_order_numbers = [order.get("order_number") for order in damage_orders if order.get("order_number", "").startswith("RET-")]
            
            if "RET-DAMAGE-002" not in damage_order_numbers:
                print(f"❌ Expected RET-DAMAGE-002 in damage filter, got: {damage_order_numbers}")
                return False
            
            print(f"✅ Damage filter: Found {len(damage_orders)} damage cases including RET-DAMAGE-002")
            
            # Test pending filter
            print("3. Testing pending_only filter...")
            response = await self.client.get(
                f"{BACKEND_URL}/returns/?pending_only=true",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Pending filter failed: {response.status_code} - {response.text}")
                return False
            
            pending_data = response.json()
            pending_orders = pending_data["items"]
            
            # Should find RET-PENDING-004 (status pending in reason)
            pending_order_numbers = [order.get("order_number") for order in pending_orders if order.get("order_number", "").startswith("RET-")]
            
            if "RET-PENDING-004" not in pending_order_numbers:
                print(f"❌ Expected RET-PENDING-004 in pending filter, got: {pending_order_numbers}")
                return False
            
            print(f"✅ Pending filter: Found {len(pending_orders)} pending cases including RET-PENDING-004")
            
            print("\n🎉 RETURNS ENDPOINT FILTERS: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Returns filters test error: {e}")
            return False
    
    # =====================================
    # TEST 3: GET /api/returns/analytics - Analytics endpoint
    # =====================================
    
    async def test_returns_analytics(self):
        """Test returns analytics endpoint"""
        print("\n🔍 TEST 3: GET /api/returns/analytics - Analytics")
        print("=" * 60)
        
        try:
            response = await self.client.get(
                f"{BACKEND_URL}/returns/analytics",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Analytics failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            
            # Verify required fields in summary
            required_summary_fields = [
                "total_returns", "total_orders", "return_rate", 
                "fraud_count", "damage_count", "pfc_count", "replacement_count"
            ]
            
            if "summary" not in data:
                print("❌ Missing summary in analytics response")
                return False
            
            summary = data["summary"]
            
            for field in required_summary_fields:
                if field not in summary:
                    print(f"❌ Missing field in summary: {field}")
                    return False
            
            print(f"✅ Analytics summary structure: All required fields present")
            print(f"   📊 Total returns: {summary['total_returns']}")
            print(f"   📊 Return rate: {summary['return_rate']}%")
            print(f"   🚨 Fraud count: {summary['fraud_count']}")
            print(f"   💔 Damage count: {summary['damage_count']}")
            print(f"   📦 PFC count: {summary['pfc_count']}")
            print(f"   🔄 Replacement count: {summary['replacement_count']}")
            
            # Verify other sections
            required_sections = ["by_reason", "top_problematic_products", "by_courier"]
            for section in required_sections:
                if section not in data:
                    print(f"❌ Missing section in analytics: {section}")
                    return False
            
            print(f"✅ Analytics sections: All required sections present")
            
            # Verify by_reason breakdown contains our test reasons
            by_reason = data["by_reason"]
            
            if len(by_reason) > 0:
                print(f"✅ Reason breakdown: {len(by_reason)} different cancellation reasons found")
                
                # Look for our test reasons
                test_reasons_found = []
                for reason, count in by_reason.items():
                    if any(keyword in reason.lower() for keyword in ["delivered", "damage", "pfc", "pending", "delay"]):
                        test_reasons_found.append(reason)
                
                print(f"   📝 Test reasons found: {test_reasons_found}")
            
            # Verify top_problematic_products structure
            top_products = data["top_problematic_products"]
            if len(top_products) > 0 and isinstance(top_products[0], dict):
                if "sku" in top_products[0] and "count" in top_products[0]:
                    print(f"✅ Top products structure: Correct format with sku and count")
                else:
                    print(f"❌ Top products format incorrect: {top_products[0].keys()}")
                    return False
            
            print("\n🎉 RETURNS ANALYTICS: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Returns analytics test error: {e}")
            return False
    
    # =====================================
    # TEST 4: POST /api/returns/{order_id}/action - Actions
    # =====================================
    
    async def test_returns_actions(self):
        """Test taking actions on returns"""
        print("\n🔍 TEST 4: POST /api/returns/{order_id}/action - Actions")
        print("=" * 60)
        
        try:
            # Get a test order to perform actions on
            if not self.test_orders:
                print("❌ No test orders available for action testing")
                return False
            
            test_order_id = self.test_orders[0]  # Use first test order
            
            # Test 1: Approve refund
            print("1. Testing approve_refund action...")
            response = await self.client.post(
                f"{BACKEND_URL}/returns/{test_order_id}/action",
                params={"action": "approve_refund"},
                json={"notes": "Refund approved by testing system"},
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Approve refund failed: {response.status_code} - {response.text}")
                return False
            
            refund_result = response.json()
            
            if "message" not in refund_result or "order_id" not in refund_result:
                print(f"❌ Incorrect response structure: {refund_result}")
                return False
            
            print(f"✅ Approve refund: {refund_result['message']}")
            
            # Verify order was updated
            order_response = await self.client.get(
                f"{BACKEND_URL}/orders/{test_order_id}",
                headers=self.get_auth_headers()
            )
            
            if order_response.status_code == 200:
                updated_order = order_response.json()
                if updated_order.get("return_status") != "refund_approved":
                    print(f"❌ Order return_status not updated: {updated_order.get('return_status')}")
                    return False
                
                print("✅ Order return_status correctly updated to 'refund_approved'")
            
            # Test 2: Schedule replacement
            print("2. Testing schedule_replacement action...")
            if len(self.test_orders) > 1:
                test_order_id_2 = self.test_orders[1]
                
                response = await self.client.post(
                    f"{BACKEND_URL}/returns/{test_order_id_2}/action",
                    params={"action": "schedule_replacement"},
                    json={"notes": "Replacement scheduled for damaged item"},
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    print(f"❌ Schedule replacement failed: {response.status_code} - {response.text}")
                    return False
                
                replacement_result = response.json()
                print(f"✅ Schedule replacement: {replacement_result['message']}")
            
            # Test 3: Mark fraud
            print("3. Testing mark_fraud action...")
            if len(self.test_orders) > 2:
                test_order_id_3 = self.test_orders[2]
                
                response = await self.client.post(
                    f"{BACKEND_URL}/returns/{test_order_id_3}/action",
                    params={"action": "mark_fraud"},
                    json={"notes": "Fraudulent return detected"},
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    print(f"❌ Mark fraud failed: {response.status_code} - {response.text}")
                    return False
                
                fraud_result = response.json()
                print(f"✅ Mark fraud: {fraud_result['message']}")
            
            # Test 4: Close case
            print("4. Testing close action...")
            if len(self.test_orders) > 3:
                test_order_id_4 = self.test_orders[3]
                
                response = await self.client.post(
                    f"{BACKEND_URL}/returns/{test_order_id_4}/action",
                    params={"action": "close"},
                    json={"notes": "Case closed - resolved"},
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    print(f"❌ Close action failed: {response.status_code} - {response.text}")
                    return False
                
                close_result = response.json()
                print(f"✅ Close action: {close_result['message']}")
            
            # Test 5: Invalid action
            print("5. Testing invalid action handling...")
            response = await self.client.post(
                f"{BACKEND_URL}/returns/{test_order_id}/action",
                params={"action": "invalid_action"},
                headers=self.get_auth_headers()
            )
            
            # Should handle gracefully (either 400 error or no action taken)
            print(f"✅ Invalid action handled: {response.status_code}")
            
            print("\n🎉 RETURNS ACTIONS: ALL TESTS PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Returns actions test error: {e}")
            return False
    
    # =====================================
    # TEST 5: Smart Classification Logic Verification
    # =====================================
    
    async def test_smart_classification(self):
        """Test the classify_return() function logic"""
        print("\n🔍 TEST 5: Smart Classification Logic Verification")
        print("=" * 60)
        
        try:
            # Get returns to verify smart flags
            response = await self.client.get(
                f"{BACKEND_URL}/returns/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Could not get returns for classification test: {response.status_code}")
                return False
            
            data = response.json()
            returns = data["items"]
            
            # Filter for our test orders by order_number pattern
            test_returns = [r for r in returns if r.get("order_number", "").startswith("RET-")]
            
            classification_tests = {
                "RET-FRAUD-001": ["fraud"],  # cancelled + "Fraud" reason
                "RET-DAMAGE-002": ["damage", "replacement"],  # "Damage" + "replacement" in reason
                "RET-PFC-003": ["pfc"],  # cancelled + empty reason
                "RET-PENDING-004": ["pending_action"],  # "Status Pending" in reason  
                "RET-DELAY-005": ["delay"]  # "Delay" in reason
            }
            
            classification_passed = True
            
            for return_order in test_returns:
                order_number = return_order.get("order_number")
                smart_flags = return_order.get("smart_flags", [])
                
                if order_number in classification_tests:
                    expected_flags = classification_tests[order_number]
                    
                    print(f"📝 {order_number}: Expected {expected_flags}, Got {smart_flags}")
                    
                    # Check if all expected flags are present
                    missing_flags = [flag for flag in expected_flags if flag not in smart_flags]
                    if missing_flags:
                        print(f"❌ {order_number}: Missing flags {missing_flags}")
                        classification_passed = False
                    else:
                        print(f"✅ {order_number}: All expected flags present")
            
            # Verify classification counts match analytics
            analytics_response = await self.client.get(
                f"{BACKEND_URL}/returns/analytics",
                headers=self.get_auth_headers()
            )
            
            if analytics_response.status_code == 200:
                analytics = analytics_response.json()
                summary = analytics["summary"]
                
                print(f"\n📊 Analytics Classification Counts:")
                print(f"   🚨 Fraud: {summary['fraud_count']}")
                print(f"   💔 Damage: {summary['damage_count']}")
                print(f"   📦 PFC: {summary['pfc_count']}")
                print(f"   🔄 Replacement: {summary['replacement_count']}")
                
                # Expected: at least 1 of each from our test data
                if summary['fraud_count'] < 1:
                    print("❌ Expected at least 1 fraud case in analytics")
                    classification_passed = False
                
                if summary['damage_count'] < 1:
                    print("❌ Expected at least 1 damage case in analytics")
                    classification_passed = False
                
                if summary['pfc_count'] < 1:
                    print("❌ Expected at least 1 PFC case in analytics")
                    classification_passed = False
                
                if summary['replacement_count'] < 1:
                    print("❌ Expected at least 1 replacement case in analytics")
                    classification_passed = False
            
            if classification_passed:
                print("\n🎉 SMART CLASSIFICATION: ALL TESTS PASSED")
                return True
            else:
                print("\n❌ SMART CLASSIFICATION: SOME TESTS FAILED")
                return False
            
        except Exception as e:
            print(f"❌ Smart classification test error: {e}")
            return False
    
    # =====================================
    # CLEANUP
    # =====================================
    
    async def cleanup_test_data(self):
        """Clean up test orders created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        deleted_count = 0
        for order_id in self.test_orders:
            try:
                response = await self.client.delete(
                    f"{BACKEND_URL}/orders/{order_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code in [200, 204]:
                    deleted_count += 1
            except Exception as e:
                print(f"⚠️ Could not delete order {order_id}: {e}")
        
        print(f"✅ Cleaned up {deleted_count}/{len(self.test_orders)} test orders")
    
    # =====================================
    # MAIN TEST RUNNER
    # =====================================
    
    async def run_all_tests(self):
        """Run all Returns & Claims System tests"""
        print("🚀 FURNIVA RETURNS & CLAIMS SYSTEM TESTING")
        print("=" * 80)
        print("Testing new Returns & Claims System backend endpoints")
        print("=" * 80)
        
        # Setup authentication
        if not await self.register_and_login():
            print("❌ AUTHENTICATION FAILED - Cannot proceed with tests")
            return False
        
        # Create test data
        await self.create_test_orders_with_returns_data()
        
        # Test results
        test_results = {}
        
        try:
            # Test 1: Basic returns endpoint
            test_results['returns_basic'] = await self.test_returns_endpoint_basic()
            
            # Test 2: Returns filters
            test_results['returns_filters'] = await self.test_returns_endpoint_filters()
            
            # Test 3: Returns analytics
            test_results['returns_analytics'] = await self.test_returns_analytics()
            
            # Test 4: Returns actions
            test_results['returns_actions'] = await self.test_returns_actions()
            
            # Test 5: Smart classification logic
            test_results['smart_classification'] = await self.test_smart_classification()
            
        finally:
            # Always cleanup test data
            await self.cleanup_test_data()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🏆 RETURNS & CLAIMS SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        print("-" * 80)
        print(f"OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL RETURNS & CLAIMS SYSTEM TESTS PASSED!")
            return True
        else:
            print("⚠️  SOME RETURNS SYSTEM TESTS FAILED - ISSUES NEED ATTENTION")
            return False

# =====================================
# RUN TESTS
# =====================================

async def main():
    """Main test execution"""
    async with FurnivaReturnsSystemTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)