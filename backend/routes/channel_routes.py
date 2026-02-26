from fastapi import APIRouter, Depends, HTTPException
from models import Channel, ChannelCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List
import uuid

router = APIRouter(prefix="/channels", tags=["channels"])

@router.post("/", response_model=Channel)
async def create_channel(
    channel: ChannelCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new sales channel"""
    # Check if channel name already exists
    existing = await db.channels.find_one({"name": channel.name.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Channel with this name already exists")
    
    channel_dict = channel.model_dump()
    channel_dict["id"] = str(uuid.uuid4())
    channel_dict["name"] = channel.name.lower()
    channel_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.channels.insert_one(channel_dict)
    return Channel(**channel_dict)

@router.get("/", response_model=List[Channel])
async def get_channels(
    is_active: bool = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all channels"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    channels = await db.channels.find(query, {"_id": 0}).to_list(100)
    return channels

@router.get("/{channel_name}", response_model=Channel)
async def get_channel(
    channel_name: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get channel by name"""
    channel = await db.channels.find_one({"name": channel_name.lower()}, {"_id": 0})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return Channel(**channel)

@router.put("/{channel_name}", response_model=Channel)
async def update_channel(
    channel_name: str,
    channel: ChannelCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update channel"""
    existing = await db.channels.find_one({"name": channel_name.lower()}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    update_dict = channel.model_dump()
    update_dict["name"] = update_dict["name"].lower()
    
    await db.channels.update_one(
        {"name": channel_name.lower()},
        {"$set": update_dict}
    )
    
    updated_channel = await db.channels.find_one({"name": update_dict["name"]}, {"_id": 0})
    return Channel(**updated_channel)

@router.delete("/{channel_name}")
async def delete_channel(
    channel_name: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete channel"""
    result = await db.channels.delete_one({"name": channel_name.lower()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"message": "Channel deleted successfully"}

@router.post("/seed-default-channels")
async def seed_default_channels(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Seed default channels (Amazon, Flipkart, Website, WhatsApp, Phone)"""
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
    
    return {"message": f"Seeded {created} default channels"}
