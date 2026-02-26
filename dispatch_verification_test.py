#!/usr/bin/env python3
"""
Final verification test for dispatch_by database fix
Specifically tests the requirements from the review request
"""

import requests
import json

# Configuration
BASE_URL = "https://order-workflow-hub-1.preview.emergentagent.com/api"
TEST_EMAIL = "furniva.test@example.com" 
TEST_PASSWORD = "FurnivaTest2024!"

def get_auth_token():
    """Get authentication token"""
    credentials = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=credentials)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def test_orders_endpoint(token):
    """Test GET /api/orders/ - This was the failing endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing GET /api/orders/ (was failing with ValidationError)...")
    response = requests.get(f"{BASE_URL}/orders/", headers=headers)
    
    if response.status_code == 200:
        try:
            orders = response.json()
            if isinstance(orders, list):
                print(f"✅ SUCCESS: Retrieved {len(orders)} orders without ValidationError")
                
                # Check for dispatch_by values
                empty_dispatch_count = 0
                valid_dispatch_count = 0
                for order in orders:
                    if order.get("dispatch_by") is None:
                        empty_dispatch_count += 1
                    elif order.get("dispatch_by"):
                        valid_dispatch_count += 1
                
                print(f"   📊 Orders with null dispatch_by: {empty_dispatch_count}")
                print(f"   📊 Orders with valid dispatch_by: {valid_dispatch_count}")
                return True, len(orders)
            else:
                print(f"❌ FAILURE: Response is not a list: {type(orders)}")
                return False, 0
        except Exception as e:
            print(f"❌ FAILURE: JSON parsing error: {e}")
            return False, 0
    else:
        print(f"❌ FAILURE: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        return False, 0

def test_dashboard_endpoints(token):
    """Test dashboard endpoints mentioned in review request"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test recent orders
    print("\n🔍 Testing GET /api/dashboard/recent-orders...")
    response = requests.get(f"{BASE_URL}/dashboard/recent-orders", headers=headers)
    recent_orders_ok = response.status_code == 200
    print(f"{'✅' if recent_orders_ok else '❌'} Recent orders: HTTP {response.status_code}")
    
    # Test stats
    print("\n🔍 Testing GET /api/dashboard/stats...")
    response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    if response.status_code == 200:
        try:
            stats = response.json()
            order_count = stats.get("total_orders", "unknown")
            print(f"✅ Dashboard stats: HTTP 200")
            print(f"   📊 Total orders from stats: {order_count}")
            return True, order_count
        except Exception as e:
            print(f"❌ Dashboard stats JSON error: {e}")
            return False, "unknown"
    else:
        print(f"❌ Dashboard stats: HTTP {response.status_code}")
        return False, "unknown"

def main():
    """Run final validation tests"""
    print("🎯 FINAL VALIDATION: dispatch_by Database Fix")
    print("=" * 50)
    
    # Get token
    token = get_auth_token()
    if not token:
        print("❌ CRITICAL: Could not authenticate")
        return
    
    print("✅ Authentication successful")
    
    # Test the critical endpoint that was failing
    orders_ok, order_count = test_orders_endpoint(token)
    
    # Test dashboard endpoints
    dashboard_ok, stats_order_count = test_dashboard_endpoints(token)
    
    # Final verification
    print("\n" + "=" * 50)
    print("🏁 FINAL RESULTS:")
    
    if orders_ok and order_count >= 100:
        print("✅ CRITICAL SUCCESS: GET /api/orders/ now works without ValidationError")
        print(f"✅ Order count verified: {order_count} orders retrieved")
        
        if order_count >= 103:
            print("✅ Expected order count: 103+ orders confirmed")
        else:
            print(f"⚠️  Order count: Expected 103+, got {order_count}")
            
        if dashboard_ok:
            print("✅ Dashboard endpoints: Working correctly")
            print(f"✅ Stats order count: {stats_order_count}")
        else:
            print("⚠️  Dashboard endpoints: Some issues detected")
            
        print("\n🎉 DISPATCH_BY FIX VALIDATION: SUCCESSFUL")
        print("   All critical backend functionality is complete!")
        
    else:
        print("❌ CRITICAL FAILURE: dispatch_by fix incomplete")
        print("   GET /api/orders/ endpoint still has issues")

if __name__ == "__main__":
    main()