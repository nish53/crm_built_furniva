from fastapi import APIRouter, Depends, HTTPException, Query
from models import MasterSKUMapping, MasterSKUMappingCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/master-sku", tags=["master-sku"])

@router.post("/", response_model=MasterSKUMapping)
async def create_master_sku_mapping(
    mapping: MasterSKUMappingCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new Master SKU mapping and auto-create listings"""
    # Check if master_sku already exists
    existing = await db.master_sku_mappings.find_one({"master_sku": mapping.master_sku}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Master SKU already exists")
    
    mapping_dict = mapping.model_dump()
    mapping_dict["id"] = str(uuid.uuid4())
    mapping_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.master_sku_mappings.insert_one(mapping_dict)
    
    # Auto-create listings for each platform with SKU
    listings_created = []
    
    # Amazon listing
    if mapping.amazon_sku or mapping.amazon_asin:
        amazon_listing = {
            "id": str(uuid.uuid4()),
            "master_sku": mapping.master_sku,
            "platform": "amazon",
            "platform_sku": mapping.amazon_sku or "",
            "platform_product_id": mapping.amazon_asin or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(amazon_listing)
        listings_created.append("amazon")
    
    # Flipkart listing
    if mapping.flipkart_sku or mapping.flipkart_fsn:
        flipkart_listing = {
            "id": str(uuid.uuid4()),
            "master_sku": mapping.master_sku,
            "platform": "flipkart",
            "platform_sku": mapping.flipkart_sku or "",
            "platform_product_id": mapping.flipkart_fsn or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(flipkart_listing)
        listings_created.append("flipkart")
    
    # Website listing
    if mapping.website_sku:
        website_listing = {
            "id": str(uuid.uuid4()),
            "master_sku": mapping.master_sku,
            "platform": "website",
            "platform_sku": mapping.website_sku or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.platform_listings.insert_one(website_listing)
        listings_created.append("website")
    
    # Update all orders with matching SKUs to include master_sku
    update_count = 0
    
    if mapping.amazon_sku:
        result = await db.orders.update_many(
            {"sku": mapping.amazon_sku, "channel": "amazon"},
            {"$set": {"master_sku": mapping.master_sku, "product_name": mapping.product_name}}
        )
        update_count += result.modified_count
    
    if mapping.flipkart_sku:
        result = await db.orders.update_many(
            {"sku": mapping.flipkart_sku, "channel": "flipkart"},
            {"$set": {"master_sku": mapping.master_sku, "product_name": mapping.product_name}}
        )
        update_count += result.modified_count
    
    if mapping.website_sku:
        result = await db.orders.update_many(
            {"sku": mapping.website_sku, "channel": "website"},
            {"$set": {"master_sku": mapping.master_sku, "product_name": mapping.product_name}}
        )
        update_count += result.modified_count
    
    # Add the auto-generated fields to the dict before creating response
    mapping_dict["listings_created"] = listings_created
    mapping_dict["orders_updated"] = update_count
    
    response = MasterSKUMapping(**mapping_dict)
    
    return response

@router.get("/", response_model=List[MasterSKUMapping])
async def get_master_sku_mappings(
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all Master SKU mappings"""
    query = {}
    
    if search:
        query["$or"] = [
            {"master_sku": {"$regex": search, "$options": "i"}},
            {"product_name": {"$regex": search, "$options": "i"}},
            {"amazon_sku": {"$regex": search, "$options": "i"}},
            {"amazon_asin": {"$regex": search, "$options": "i"}},
            {"flipkart_sku": {"$regex": search, "$options": "i"}},
            {"flipkart_fsn": {"$regex": search, "$options": "i"}}
        ]
    
    if category:
        query["category"] = category
    
    mappings = await db.master_sku_mappings.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return mappings

@router.get("/{master_sku}", response_model=MasterSKUMapping)
async def get_master_sku_mapping(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get Master SKU mapping by master_sku"""
    mapping = await db.master_sku_mappings.find_one({"master_sku": master_sku}, {"_id": 0})
    if not mapping:
        raise HTTPException(status_code=404, detail="Master SKU mapping not found")
    return MasterSKUMapping(**mapping)

@router.get("/lookup/platform-sku/{platform_sku}")
async def lookup_by_platform_sku(
    platform_sku: str,
    platform: str = Query(..., description="amazon, flipkart, or website"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Lookup Master SKU by platform-specific SKU"""
    field_map = {
        "amazon": ["amazon_sku", "amazon_asin", "amazon_fnsku"],
        "flipkart": ["flipkart_sku", "flipkart_fsn"],
        "website": ["website_sku"]
    }
    
    if platform not in field_map:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    # Search across all fields for the platform
    query = {"$or": [{field: platform_sku} for field in field_map[platform]]}
    mapping = await db.master_sku_mappings.find_one(query, {"_id": 0})
    
    if not mapping:
        return {"found": False, "master_sku": None}
    
    return {"found": True, "master_sku": mapping["master_sku"], "mapping": mapping}

@router.put("/{master_sku}", response_model=MasterSKUMapping)
async def update_master_sku_mapping(
    master_sku: str,
    mapping: MasterSKUMappingCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update Master SKU mapping"""
    existing = await db.master_sku_mappings.find_one({"master_sku": master_sku}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Master SKU mapping not found")
    
    update_dict = mapping.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.master_sku_mappings.update_one(
        {"master_sku": master_sku},
        {"$set": update_dict}
    )
    
    updated_mapping = await db.master_sku_mappings.find_one({"master_sku": master_sku}, {"_id": 0})
    return MasterSKUMapping(**updated_mapping)

@router.delete("/{master_sku}")
async def delete_master_sku_mapping(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete Master SKU mapping"""
    result = await db.master_sku_mappings.delete_one({"master_sku": master_sku})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Master SKU mapping not found")
    return {"message": "Master SKU mapping deleted successfully"}

@router.post("/bulk-import")
async def bulk_import_master_sku(
    mappings: List[MasterSKUMappingCreate],
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Bulk import Master SKU mappings"""
    imported = 0
    skipped = 0
    errors = []
    
    for mapping in mappings:
        try:
            existing = await db.master_sku_mappings.find_one({"master_sku": mapping.master_sku}, {"_id": 0})
            if existing:
                skipped += 1
                continue
            
            mapping_dict = mapping.model_dump()
            mapping_dict["id"] = str(uuid.uuid4())
            mapping_dict["created_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.master_sku_mappings.insert_one(mapping_dict)
            imported += 1
        except Exception as e:
            errors.append({"master_sku": mapping.master_sku, "error": str(e)})
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "total": len(mappings)
    }

@router.post("/sync-orders/{master_sku}")
async def sync_orders_with_master_sku(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Manually sync orders with a specific Master SKU mapping"""
    # Get the mapping
    mapping = await db.master_sku_mappings.find_one({"master_sku": master_sku}, {"_id": 0})
    if not mapping:
        raise HTTPException(status_code=404, detail="Master SKU mapping not found")
    
    update_count = 0
    
    # Update Amazon orders
    if mapping.get("amazon_sku"):
        result = await db.orders.update_many(
            {"sku": mapping["amazon_sku"], "channel": "amazon"},
            {"$set": {"master_sku": master_sku, "product_name": mapping["product_name"]}}
        )
        update_count += result.modified_count
    
    # Update Flipkart orders
    if mapping.get("flipkart_sku"):
        result = await db.orders.update_many(
            {"sku": mapping["flipkart_sku"], "channel": "flipkart"},
            {"$set": {"master_sku": master_sku, "product_name": mapping["product_name"]}}
        )
        update_count += result.modified_count
    
    # Update Website orders
    if mapping.get("website_sku"):
        result = await db.orders.update_many(
            {"sku": mapping["website_sku"], "channel": "website"},
            {"$set": {"master_sku": master_sku, "product_name": mapping["product_name"]}}
        )
        update_count += result.modified_count
    
    return {
        "message": f"Synced {update_count} orders with master SKU {master_sku}",
        "orders_updated": update_count
    }

@router.post("/sync-all-orders")
async def sync_all_orders_with_master_sku(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Sync all orders with their respective Master SKU mappings"""
    # Get all mappings
    mappings = await db.master_sku_mappings.find({}, {"_id": 0}).to_list(None)
    
    total_updated = 0
    mapping_results = []
    
    for mapping in mappings:
        update_count = 0
        
        # Update Amazon orders
        if mapping.get("amazon_sku"):
            result = await db.orders.update_many(
                {"sku": mapping["amazon_sku"], "channel": "amazon"},
                {"$set": {"master_sku": mapping["master_sku"], "product_name": mapping["product_name"]}}
            )
            update_count += result.modified_count
        
        # Update Flipkart orders
        if mapping.get("flipkart_sku"):
            result = await db.orders.update_many(
                {"sku": mapping["flipkart_sku"], "channel": "flipkart"},
                {"$set": {"master_sku": mapping["master_sku"], "product_name": mapping["product_name"]}}
            )
            update_count += result.modified_count
        
        # Update Website orders
        if mapping.get("website_sku"):
            result = await db.orders.update_many(
                {"sku": mapping["website_sku"], "channel": "website"},
                {"$set": {"master_sku": mapping["master_sku"], "product_name": mapping["product_name"]}}
            )
            update_count += result.modified_count
        
        total_updated += update_count
        mapping_results.append({
            "master_sku": mapping["master_sku"],
            "orders_updated": update_count
        })
    
    return {
        "message": f"Synced {total_updated} orders across {len(mappings)} master SKU mappings",
        "total_orders_updated": total_updated,
        "mappings_processed": len(mappings),
        "results": mapping_results
    }
