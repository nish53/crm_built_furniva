#!/usr/bin/env python3
"""
Quick test for Master SKU sync functionality
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone

BACKEND_URL = "https://migration-reapply.preview.emergentagent.com/api"

async def test_master_sku_fix():
    """Test Master SKU sync after model fix"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔧 Testing Master SKU fix...")
        
        # Generate unique test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_furniva_fix_{unique_id}@example.com"
        test_password = "TestPass123!"
        
        # Register and login
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": "Test User Fix",
            "role": "admin"
        }
        
        await client.post(f"{BACKEND_URL}/auth/register", json=register_data)
        
        login_response = await client.post(f"{BACKEND_URL}/auth/login", json={
            "email": test_email, 
            "password": test_password
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Master SKU creation
        master_sku_data = {
            "master_sku": "MASTER-FIX-TEST-001",
            "product_name": "Fix Test Chair",
            "amazon_sku": "AMZ-FIX-001",
            "amazon_asin": "B08FIX001",
            "cost_price": 1000.0,
            "selling_price": 2000.0
        }
        
        response = await client.post(
            f"{BACKEND_URL}/master-sku/",
            json=master_sku_data,
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Master SKU creation still failed: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        print(f"✅ Master SKU created successfully: {result['master_sku']}")
        print(f"   📦 Listings created: {result.get('listings_created', [])}")
        print(f"   🔄 Orders updated: {result.get('orders_updated', 0)}")
        
        # Test sync-all-orders endpoint
        response = await client.post(f"{BACKEND_URL}/master-sku/sync-all-orders", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Sync all orders failed: {response.status_code} - {response.text}")
            return False
        
        sync_result = response.json()
        print(f"✅ Sync all orders successful: {sync_result}")
        
        print("🎉 Master SKU fix confirmed working!")
        return True

if __name__ == "__main__":
    result = asyncio.run(test_master_sku_fix())