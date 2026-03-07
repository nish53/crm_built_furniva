#!/usr/bin/env python3
"""
Check for pagination in orders endpoint
"""

import requests
import json

BASE_URL = "https://order-hub-175.preview.emergentagent.com/api"
TEST_EMAIL = "furniva.test@example.com" 
TEST_PASSWORD = "FurnivaTest2024!"

def get_auth_token():
    credentials = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    response = requests.post(f"{BASE_URL}/auth/login", json=credentials)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def check_orders_pagination():
    token = get_auth_token()
    if not token:
        print("❌ Auth failed")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try with different limits
    print("🔍 Checking orders endpoint pagination...")
    
    # Default
    response = requests.get(f"{BASE_URL}/orders/", headers=headers)
    if response.status_code == 200:
        orders = response.json()
        print(f"Default: {len(orders)} orders")
        
    # Try with larger limit
    response = requests.get(f"{BASE_URL}/orders/?limit=200", headers=headers)
    if response.status_code == 200:
        orders = response.json()
        print(f"Limit=200: {len(orders)} orders")
        
        # Count dispatch_by values
        null_count = sum(1 for o in orders if o.get("dispatch_by") is None)
        valid_count = sum(1 for o in orders if o.get("dispatch_by") is not None and o.get("dispatch_by"))
        empty_count = sum(1 for o in orders if o.get("dispatch_by") == "")
        
        print(f"   📊 Null dispatch_by: {null_count}")
        print(f"   📊 Valid dispatch_by: {valid_count}")
        print(f"   📊 Empty string dispatch_by: {empty_count}")
        
        if empty_count > 0:
            print("⚠️  Still found empty strings - fix may be incomplete")
        else:
            print("✅ No empty strings found - dispatch_by fix successful")

if __name__ == "__main__":
    check_orders_pagination()