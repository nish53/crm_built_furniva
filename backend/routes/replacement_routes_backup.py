from fastapi import APIRouter, Depends, HTTPException
from models import ReplacementRequest, ReplacementRequestCreate, ReplacementStatus, ReplacementReason, User
from auth import get_current_active_user
from database import get_database
from datetime import datetime, timezone
from typing import List, Optional
import uuid

router = APIRouter(prefix="/replacement-requests", tags=["replacement-requests"])

@router.post("/", response_model=ReplacementRequest)
async def create_replacement_request(
    replacement_req: ReplacementRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Create a new replacement request (for Damage or Quality Issue only)"""
    # Validate images provided
    if not replacement_req.damage_images or len(replacement_req.damage_images) == 0:
        raise HTTPException(status_code=400, detail="At least one damage image is required")
    
    # Get order details
    order = await db.orders.find_one({"id": replacement_req.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Create replacement request
    replacement_dict = replacement_req.model_dump()
    replacement_dict["id"] = str(uuid.uuid4())
    replacement_dict["order_number"] = order["order_number"]
    replacement_dict["customer_id"] = order.get("customer_id", "")
    replacement_dict["customer_name"] = order["customer_name"]
    replacement_dict["phone"] = order["phone"]
    replacement_dict["replacement_status"] = ReplacementStatus.PENDING
    replacement_dict["requested_date"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["created_by"] = current_user.email
    replacement_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    replacement_dict["status_history"] = [{
        "status": ReplacementStatus.PENDING,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email
    }]
    
    await db.replacement_requests.insert_one(replacement_dict)
    
    # Update order to mark replacement requested
    await db.orders.update_one(
        {"id": replacement_req.order_id},
        {"$set": {
            "replacement_requested": True,
            "replacement_reason": replacement_req.replacement_reason,
            "replacement_request_date": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return ReplacementRequest(**replacement_dict)

@router.get("/", response_model=List[ReplacementRequest])
async def get_replacement_requests(
    status: Optional[ReplacementStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get all replacement requests with optional status filter"""
    query = {}
    if status:
        query["replacement_status"] = status
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", -1).to_list(None)
    return replacements

@router.get("/{replacement_id}", response_model=ReplacementRequest)
async def get_replacement_request(
    replacement_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get a specific replacement request"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    return ReplacementRequest(**replacement)

@router.patch("/{replacement_id}/status")
async def update_replacement_status(
    replacement_id: str,
    new_status: ReplacementStatus,
    tracking_number: Optional[str] = None,
    issue_resolved: Optional[bool] = None,
    resolution_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Update replacement request status and tracking info"""
    replacement = await db.replacement_requests.find_one({"id": replacement_id}, {"_id": 0})
    if not replacement:
        raise HTTPException(status_code=404, detail="Replacement request not found")
    
    update_data = {
        "replacement_status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update specific fields based on status
    if new_status == ReplacementStatus.PRIORITY_REVIEW:
        update_data["priority_review_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.SHIP_REPLACEMENT:
        update_data["ship_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.TRACKING_ADDED:
        if not tracking_number:
            raise HTTPException(status_code=400, detail="Tracking number required for this status")
        update_data["tracking_number"] = tracking_number
        update_data["tracking_added_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status == ReplacementStatus.DELIVERED:
        update_data["delivered_date"] = datetime.now(timezone.utc).isoformat()
    
    elif new_status in [ReplacementStatus.RESOLVED, ReplacementStatus.NOT_RESOLVED]:
        update_data["resolved_date"] = datetime.now(timezone.utc).isoformat()
        if issue_resolved is not None:
            update_data["issue_resolved"] = issue_resolved
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
    
    # Add to status history
    status_history = replacement.get("status_history", [])
    status_history.append({
        "status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changed_by": current_user.email,
        "tracking_number": tracking_number,
        "notes": resolution_notes
    })
    update_data["status_history"] = status_history
    
    await db.replacement_requests.update_one({"id": replacement_id}, {"$set": update_data})
    
    return {"message": "Replacement status updated successfully", "new_status": new_status}

@router.get("/priority/pending")
async def get_priority_replacements(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Get replacement requests that need priority attention"""
    query = {
        "replacement_status": {"$in": [
            ReplacementStatus.PENDING,
            ReplacementStatus.PRIORITY_REVIEW
        ]}
    }
    
    replacements = await db.replacement_requests.find(query, {"_id": 0}).sort("requested_date", 1).to_list(None)
    
    return {
        "count": len(replacements),
        "replacements": replacements
    }
