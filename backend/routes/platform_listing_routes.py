from fastapi import APIRouter, Depends, HTTPException, Query
from models import PlatformListing, PlatformListingCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/platform-listings", tags=["platform-listings"])

@router.post("/", response_model=PlatformListing)
async def create_platform_listing(
    listing: PlatformListingCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new platform listing for a Master SKU"""
    listing_dict = listing.model_dump()
    listing_dict["id"] = str(uuid.uuid4())
    listing_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.platform_listings.insert_one(listing_dict)
    return PlatformListing(**listing_dict)

@router.get("/", response_model=List[PlatformListing])
async def get_platform_listings(
    master_sku: Optional[str] = None,
    platform: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all platform listings"""
    query = {}
    if master_sku:
        query["master_sku"] = master_sku
    if platform:
        query["platform"] = platform
    if is_active is not None:
        query["is_active"] = is_active
    
    listings = await db.platform_listings.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return listings

@router.get("/{listing_id}", response_model=PlatformListing)
async def get_platform_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get platform listing by ID"""
    listing = await db.platform_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Platform listing not found")
    return PlatformListing(**listing)

@router.get("/lookup/by-identifier")
async def lookup_by_platform_identifier(
    identifier: str,
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Lookup Master SKU by platform identifier (ASIN, FSN, SKU, FNSKU)"""
    query = {"$or": [
        {"platform_sku": identifier},
        {"platform_product_id": identifier},
        {"platform_fnsku": identifier}
    ]}
    
    if platform:
        query["platform"] = platform
    
    listing = await db.platform_listings.find_one(query, {"_id": 0})
    
    if not listing:
        return {"found": False, "master_sku": None}
    
    return {"found": True, "master_sku": listing["master_sku"], "listing": listing}

@router.put("/{listing_id}", response_model=PlatformListing)
async def update_platform_listing(
    listing_id: str,
    listing: PlatformListingCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update platform listing"""
    existing = await db.platform_listings.find_one({"id": listing_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Platform listing not found")
    
    update_dict = listing.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.platform_listings.update_one(
        {"id": listing_id},
        {"$set": update_dict}
    )
    
    updated_listing = await db.platform_listings.find_one({"id": listing_id}, {"_id": 0})
    return PlatformListing(**updated_listing)

@router.delete("/{listing_id}")
async def delete_platform_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete platform listing"""
    result = await db.platform_listings.delete_one({"id": listing_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Platform listing not found")
    return {"message": "Platform listing deleted successfully"}

@router.get("/by-master-sku/{master_sku}", response_model=List[PlatformListing])
async def get_listings_by_master_sku(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all platform listings for a specific Master SKU"""
    listings = await db.platform_listings.find({"master_sku": master_sku}, {"_id": 0}).to_list(100)
    return listings
