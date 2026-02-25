#!/usr/bin/env python3
"""
Quick database check to understand the dispatch_by data issue
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_orders():
    """Check what's in the orders collection for dispatch_by field"""
    
    # Connect to MongoDB 
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.test_database
    
    # Sample a few orders to see dispatch_by values
    orders = await db.orders.find({}, {"order_number": 1, "dispatch_by": 1, "_id": 0}).limit(10).to_list(10)
    
    print("Sample orders dispatch_by values:")
    for order in orders:
        dispatch_by = order.get("dispatch_by")
        print(f"Order {order.get('order_number', 'unknown')}: dispatch_by = '{dispatch_by}' (type: {type(dispatch_by)})")
    
    # Count different dispatch_by value types
    empty_strings = await db.orders.count_documents({"dispatch_by": ""})
    null_values = await db.orders.count_documents({"dispatch_by": None})
    missing_field = await db.orders.count_documents({"dispatch_by": {"$exists": False}})
    has_values = await db.orders.count_documents({"dispatch_by": {"$ne": "", "$ne": None, "$exists": True}})
    total_orders = await db.orders.count_documents({})
    
    print(f"\nDispatch_by field analysis (total orders: {total_orders}):")
    print(f"- Empty strings (''): {empty_strings}")
    print(f"- Null values: {null_values}")  
    print(f"- Missing field: {missing_field}")
    print(f"- Has valid values: {has_values}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_orders())