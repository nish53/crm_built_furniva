"""
Seed script to initialize default channels
Run this once to set up default channels
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv()

async def seed_default_channels():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    default_channels = [
        {
            "id": str(uuid.uuid4()),
            "name": "amazon",
            "display_name": "Amazon",
            "is_active": True,
            "required_fields": ["order_number", "asin", "sku"],
            "optional_fields": ["fnsku", "fulfillment_channel"],
            "supports_tracking": True,
            "commission_rate": 15.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "flipkart",
            "display_name": "Flipkart",
            "is_active": True,
            "required_fields": ["order_number", "fsn_id", "sku"],
            "optional_fields": ["fnsku"],
            "supports_tracking": True,
            "commission_rate": 12.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "website",
            "display_name": "Website",
            "is_active": True,
            "required_fields": ["order_number"],
            "optional_fields": ["payment_method"],
            "supports_tracking": True,
            "commission_rate": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "whatsapp",
            "display_name": "WhatsApp",
            "is_active": True,
            "required_fields": ["order_number", "phone"],
            "optional_fields": [],
            "supports_tracking": False,
            "commission_rate": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "phone",
            "display_name": "Phone Order",
            "is_active": True,
            "required_fields": ["order_number", "phone"],
            "optional_fields": [],
            "supports_tracking": True,
            "commission_rate": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    created = 0
    for channel in default_channels:
        existing = await db.channels.find_one({"name": channel["name"]}, {"_id": 0})
        if not existing:
            await db.channels.insert_one(channel)
            created += 1
            print(f"✓ Created channel: {channel['display_name']}")
        else:
            print(f"- Channel already exists: {channel['display_name']}")
    
    print(f"\n✅ Seeded {created} new channels")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_default_channels())
