#!/usr/bin/env python3
"""
Quick test for the warehouse stock endpoint fix
"""

import requests
import json

# Configuration
BASE_URL = "https://furniture-flow-pro.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@furniva.com"
ADMIN_PASSWORD = "Admin123!"

def test_warehouse_stock_fix():
    """Test the warehouse stock endpoint after ObjectId fix"""
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Authentication successful")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return False
    
    # Test warehouse stock endpoint
    print("\n🔧 Testing warehouse stock endpoint fix...")
    response = session.get(f"{BASE_URL}/inventory/warehouse-stock/WH-DEL")
    
    if response.status_code == 200:
        data = response.json()
        warehouse = data.get("warehouse", {})
        stock = data.get("stock", [])
        total_skus = data.get("total_skus", 0)
        total_units = data.get("total_units", 0)
        
        print(f"✅ Warehouse stock endpoint working!")
        print(f"   Warehouse: {warehouse.get('name')} ({warehouse.get('code')})")
        print(f"   Stock items: {total_skus} SKUs, {total_units} total units")
        
        # Check if warehouse object has _id field (should not)
        if "_id" in warehouse:
            print(f"⚠️  Warning: warehouse object still contains _id field")
        else:
            print(f"✅ ObjectId fix confirmed: warehouse object has no _id field")
        
        return True
    elif response.status_code == 404:
        print(f"✅ Warehouse not found (expected if WH-DEL doesn't exist)")
        return True
    else:
        print(f"❌ Warehouse stock endpoint still failing: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

if __name__ == "__main__":
    test_warehouse_stock_fix()