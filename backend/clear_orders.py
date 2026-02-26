import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def clear_all_orders():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Delete all orders
    result = await db.orders.delete_many({})
    print(f"Deleted {result.deleted_count} orders")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clear_all_orders())
