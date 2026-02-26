from fastapi import APIRouter, Depends, HTTPException, Query
from models import ProcurementBatch, ProcurementBatchCreate, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/procurement-batches", tags=["procurement-batches"])

@router.post("/", response_model=ProcurementBatch)
async def create_procurement_batch(
    batch: ProcurementBatchCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new procurement batch"""
    batch_dict = batch.model_dump()
    batch_dict["id"] = str(uuid.uuid4())
    batch_dict["total_cost"] = batch.quantity * batch.unit_cost
    batch_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert datetime to ISO string
    if isinstance(batch_dict.get("procurement_date"), datetime):
        batch_dict["procurement_date"] = batch_dict["procurement_date"].isoformat()
    
    await db.procurement_batches.insert_one(batch_dict)
    return ProcurementBatch(**batch_dict)

@router.get("/", response_model=List[ProcurementBatch])
async def get_procurement_batches(
    master_sku: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all procurement batches"""
    query = {}
    if master_sku:
        query["master_sku"] = master_sku
    
    batches = await db.procurement_batches.find(query, {"_id": 0}).sort("procurement_date", -1).skip(skip).limit(limit).to_list(limit)
    return batches

@router.get("/{batch_id}", response_model=ProcurementBatch)
async def get_procurement_batch(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get procurement batch by ID"""
    batch = await db.procurement_batches.find_one({"id": batch_id}, {"_id": 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Procurement batch not found")
    return ProcurementBatch(**batch)

@router.get("/by-master-sku/{master_sku}", response_model=List[ProcurementBatch])
async def get_batches_by_master_sku(
    master_sku: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all procurement batches for a specific Master SKU"""
    batches = await db.procurement_batches.find({"master_sku": master_sku}, {"_id": 0}).sort("procurement_date", -1).to_list(100)
    return batches

@router.get("/average-cost/{master_sku}")
async def get_average_cost(
    master_sku: str,
    method: str = Query("weighted", description="fifo, lifo, or weighted"),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Calculate average cost for a Master SKU using specified method"""
    batches = await db.procurement_batches.find({"master_sku": master_sku}, {"_id": 0}).sort("procurement_date", 1).to_list(100)
    
    if not batches:
        return {"master_sku": master_sku, "average_cost": 0, "method": method}
    
    if method == "fifo":
        # First In First Out - use oldest batch cost
        return {"master_sku": master_sku, "average_cost": batches[0]["unit_cost"], "method": "fifo"}
    
    elif method == "lifo":
        # Last In First Out - use newest batch cost
        return {"master_sku": master_sku, "average_cost": batches[-1]["unit_cost"], "method": "lifo"}
    
    else:  # weighted average
        total_quantity = sum(b["quantity"] for b in batches)
        total_cost = sum(b["total_cost"] for b in batches)
        avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
        return {"master_sku": master_sku, "average_cost": avg_cost, "method": "weighted_average"}

@router.delete("/{batch_id}")
async def delete_procurement_batch(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Delete procurement batch"""
    result = await db.procurement_batches.delete_one({"id": batch_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Procurement batch not found")
    return {"message": "Procurement batch deleted successfully"}
