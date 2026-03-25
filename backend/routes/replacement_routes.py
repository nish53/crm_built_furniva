from fastapi import APIRouter, Depends, HTTPException, Query
from models import ReplacementRequest, ReplacementRequestCreate, ReplacementStatus, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/replacements", tags=["replacements"])

@router.post("/", response_model=ReplacementRequest)
async def create_replacement_request(
    replacement_req: ReplacementRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new replacement request"""
    # Get order details
    order = await db.orders.find_one({"id": replacement_req.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Create replacement request
    replacement_dict = replacement_req.model_dump()
    replacement_dict["id"] = str(uuid.uuid4())
    replacement_dict["order_number"] = order["order_number"]
    replacement_dict["customer_id"] = order["customer_id"]
    replacement_dict["customer_name"] = order["customer_name"]
    replacement_dict["phone"] = order["phone"]
    replacement_dict["replacement_status"] = ReplacementStatus.REQUESTED
    replacement_dict["requested_date"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["status_history"] = []
    
    await db.replacement_requests.insert_one(replacement_dict)
    
    # Update order
    await db.orders.update_one(
        {"id": replacement_req.order_id},
        {"$set": {
            "replacement_requested": True,
            "replacement_id": replacement_dict["id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return ReplacementRequest(**replacement_dict)

@router.get("/", response_model=List[ReplacementRequest])
async def list_replacements(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """List all replacement requests with optional filters"""
    query = {}
    if status:
        query["replacement_status"] = status
    if search:
        query["$or"] = [
            {"order_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", -1).limit(limit).to_list(limit)
    return [ReplacementRequest(**r) for r in replacements]

@router.get("/{replacement_id}", response_model=ReplacementRequest)
async def get_replacement(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get replacement request by ID"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    return ReplacementRequest(**replacement)

@router.patch("/{replacement_id}/advance")
async def advance_replacement_workflow(
    replacement_id: str,
    new_status: ReplacementStatus,
    # Stage-specific fields
    approved_by: Optional[str] = None,
    rejection_reason: Optional[str] = None,
    parts_cost: Optional[float] = None,
    tracking_number: Optional[str] = None,
    courier_partner: Optional[str] = None,
    installer_name: Optional[str] = None,
    installation_notes: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    customer_satisfied: Optional[bool] = None,
    replacement_cost: Optional[float] = None,
    logistics_cost: Optional[float] = None,
    installation_cost: Optional[float] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Advance replacement workflow to next stage"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    current_status = replacement.get("replacement_status")
    
    # Workflow validation
    workflow_rules = {
        "requested": ["approved", "rejected"],
        "approved": ["parts_arranged", "cancelled"],
        "parts_arranged": ["dispatched"],
        "dispatched": ["in_transit"],
        "in_transit": ["delivered"],
        "delivered": ["installed", "resolved"],
        "installed": ["resolved"],
        "resolved": [],
        "rejected": [],
        "cancelled": []
    }
    
    allowed_next = workflow_rules.get(current_status, [])
    if str(new_status) not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'. Allowed: {', '.join(allowed_next)}"
        )
    
    # Build update data
    update_data = {
        "replacement_status": new_status,
        "previous_status": current_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add stage-specific fields
    if new_status == ReplacementStatus.APPROVED:
        update_data["approved_date"] = datetime.now(timezone.utc).isoformat()
        if approved_by:
            update_data["approved_by"] = approved_by
        else:
            update_data["approved_by"] = current_user.email
    
    elif new_status == ReplacementStatus.REJECTED:
        if rejection_reason:
            update_data["rejection_reason"] = rejection_reason
    
    elif new_status == ReplacementStatus.PARTS_ARRANGED:
        update_data["parts_arranged_date"] = datetime.now(timezone.utc).isoformat()
        if parts_cost:
            update_data["parts_cost"] = parts_cost
    
    elif new_status == ReplacementStatus.DISPATCHED:
        update_data["dispatch_date"] = datetime.now(timezone.utc).isoformat()
        if tracking_number:
            update_data["tracking_number"] = tracking_number
        if courier_partner:
            update_data["courier_partner"] = courier_partner
    
    elif new_status == ReplacementStatus.DELIVERED:
        update_data["delivery_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.INSTALLED:
        update_data["installation_date"] = datetime.now(timezone.utc).isoformat()
        if installer_name:
            update_data["installer_name"] = installer_name
        if installation_notes:
            update_data["installation_notes"] = installation_notes
    
    elif new_status == ReplacementStatus.RESOLVED:
        update_data["resolved_date"] = datetime.now(timezone.utc).isoformat()
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
        if customer_satisfied is not None:
            update_data["customer_satisfied"] = customer_satisfied
    
    # Calculate total cost
    if replacement_cost:
        update_data["replacement_cost"] = replacement_cost
    if logistics_cost:
        update_data["logistics_cost"] = logistics_cost
    if installation_cost:
        update_data["installation_cost"] = installation_cost
    
    if any([replacement_cost, logistics_cost, installation_cost]):
        total = (replacement_cost or 0) + (logistics_cost or 0) + (installation_cost or 0)
        update_data["total_cost"] = total
    
    if notes:
        update_data["internal_notes"] = notes
    
    # Record history
    history_entry = {
        "from_status": current_status,
        "to_status": str(new_status),
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "notes": notes or ""
    }
    
    # Update database
    await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$set": update_data, "$push": {"status_history": history_entry}}
    )
    
    updated_replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    return ReplacementRequest(**updated_replacement)

@router.get("/{replacement_id}/workflow-stages")
async def get_replacement_workflow_stages(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get available next stages for replacement workflow"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    current_status = replacement.get("replacement_status")
    
    workflow_rules = {
        "requested": ["approved", "rejected"],
        "approved": ["parts_arranged", "cancelled"],
        "parts_arranged": ["dispatched"],
        "dispatched": ["in_transit"],
        "in_transit": ["delivered"],
        "delivered": ["installed", "resolved"],
        "installed": ["resolved"],
        "resolved": [],
        "rejected": [],
        "cancelled": []
    }
    
    next_stages = workflow_rules.get(current_status, [])
    
    return {
        "current_status": current_status,
        "next_stages": next_stages,
        "can_advance": len(next_stages) > 0
    }

@router.patch("/{replacement_id}/images")
async def add_replacement_images(
    replacement_id: str,
    image_urls: List[str],
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Add damage images to replacement request"""
    result = await db.replacement_requests.update_one(
        {"id": replacement_id},
        {"$push": {"damage_images": {"$each": image_urls}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    return {"message": f"{len(image_urls)} images added successfully"}
