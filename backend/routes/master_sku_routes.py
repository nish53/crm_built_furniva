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
    """Create a new Master SKU mapping"""
    # Check if master_sku already exists
    existing = await db.master_sku_mappings.find_one({"master_sku": mapping.master_sku}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Master SKU already exists")
    
    mapping_dict = mapping.model_dump()
    mapping_dict["id"] = str(uuid.uuid4())
    mapping_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.master_sku_mappings.insert_one(mapping_dict)
    return MasterSKUMapping(**mapping_dict)

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
