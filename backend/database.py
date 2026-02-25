from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
db_instance = Database()

async def get_database():
    return db_instance.client[os.environ['DB_NAME']]

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    print("Connected to MongoDB")

async def close_mongo_connection():
    db_instance.client.close()
    print("Closed MongoDB connection")
