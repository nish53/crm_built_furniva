"""
One-time script to fix empty dispatch_by dates in existing orders
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_dispatch_dates():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Find all orders with empty string dispatch_by
    orders = await db.orders.find({"dispatch_by": ""}).to_list(None)
    
    print(f"Found {len(orders)} orders with empty dispatch_by")
    
    # Update each order to set dispatch_by to null
    updated_count = 0
    for order in orders:
        result = await db.orders.update_one(
            {"id": order["id"]},
            {"$unset": {"dispatch_by": ""}}
        )
        if result.modified_count > 0:
            updated_count += 1
    
    print(f"Updated {updated_count} orders")
    
    # Also fix delivery_by if needed
    orders_delivery = await db.orders.find({"delivery_by": ""}).to_list(None)
    print(f"Found {len(orders_delivery)} orders with empty delivery_by")
    
    updated_delivery = 0
    for order in orders_delivery:
        result = await db.orders.update_one(
            {"id": order["id"]},
            {"$unset": {"delivery_by": ""}}
        )
        if result.modified_count > 0:
            updated_delivery += 1
    
    print(f"Updated {updated_delivery} orders with empty delivery_by")
    
    client.close()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_dispatch_dates())
